import asyncio
import json
import logging
import secrets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from schemas import (
    RegisterHostMsg,
    HostVerifyResponseMsg,
    ClientAuthMsg,
    AuthErrorMsg,
    AuthSuccessMsg,
    SdpSignalMsg,
    IceCandidateMsg,
    HostRegisteredMsg,
    HostVerifyRequestMsg,
    HostSessionClosedMsg,
)
from session_manager import SessionManager
from turn_credentials import generate_turn_credentials

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("SignalingServer")

app = FastAPI(title="Remote Access Signaling Server", version="2.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_manager = SessionManager()


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "active_hosts": len(session_manager.hosts),
        "active_clients": len(session_manager.active_clients),
    }


# =============================================================================
# WebSocket Endpoint para HOSTS (/ws/host)
# =============================================================================
@app.websocket("/ws/host")
async def websocket_host_endpoint(websocket: WebSocket):
    await websocket.accept()
    host_id: str | None = None

    try:
        # A primeira mensagem deve ser register_host
        raw_first = await websocket.receive_text()
        first_payload = json.loads(raw_first)
        reg_msg = RegisterHostMsg(**first_payload)

        host_id = session_manager.register_host(
            ws=websocket,
            host_id=reg_msg.host_id,
            device_secret=reg_msg.device_secret,
        )

        logger.info(f"Host registrado com sucesso: host_id={host_id}")
        ice_servers = generate_turn_credentials(username_prefix=f"host_{host_id}")
        await websocket.send_text(
            HostRegisteredMsg(host_id=host_id, ice_servers=ice_servers).model_dump_json()
        )

        # Loop principal de escuta do Host
        while True:
            text = await websocket.receive_text()
            data = json.loads(text)
            msg_type = data.get("type")

            if msg_type == "verify_credential_res":
                # Resposta do Host à verificação de PIN ou Senha
                res = HostVerifyResponseMsg(**data)
                future = session_manager.pending_verifications.get(res.session_id)
                if future and not future.done():
                    future.set_result(res)

            elif msg_type in ("sdp_offer", "sdp_answer"):
                # Encaminhar SDP para o cliente correspondente
                sdp_msg = SdpSignalMsg(**data)
                client_sess = session_manager.active_clients.get(sdp_msg.session_id)
                if client_sess:
                    await client_sess.ws.send_text(sdp_msg.model_dump_json())

            elif msg_type == "ice_candidate":
                # Encaminhar ICE candidate para o cliente
                ice_msg = IceCandidateMsg(**data)
                client_sess = session_manager.active_clients.get(ice_msg.session_id)
                if client_sess:
                    await client_sess.ws.send_text(ice_msg.model_dump_json())

            elif msg_type == "session_closed":
                sess_id = data.get("session_id")
                if sess_id:
                    client_sess = session_manager.active_clients.get(sess_id)
                    if client_sess:
                        await client_sess.ws.send_text(json.dumps({
                            "type": "session_closed",
                            "session_id": sess_id,
                            "reason": data.get("reason", "Host disconnected session")
                        }))
                    host_sess = session_manager.get_host(host_id)
                    if host_sess and host_sess.active_session_id == sess_id:
                        host_sess.active_session_id = None

    except WebSocketDisconnect:
        logger.info(f"Host desconectado: host_id={host_id}")
    except Exception as e:
        logger.error(f"Erro na conexão do host {host_id}: {e}")
    finally:
        if host_id:
            session_manager.unregister_host(host_id, ws=websocket)
            # Notifica qualquer cliente conectado a este host
            for sid, cs in list(session_manager.active_clients.items()):
                if cs.target_host_id == host_id:
                    try:
                        asyncio.create_task(cs.ws.send_text(json.dumps({
                            "type": "session_closed",
                            "session_id": sid,
                            "reason": "Host offline"
                        })))
                    except Exception:
                        pass


# =============================================================================
# WebSocket Endpoint para CLIENTS (/ws/client)
# =============================================================================
@app.websocket("/ws/client")
async def websocket_client_endpoint(websocket: WebSocket):
    await websocket.accept()
    client_ip = websocket.client.host if websocket.client else "127.0.0.1"
    session_id = secrets.token_hex(16)
    target_host_id: str | None = None

    try:
        # A primeira mensagem deve ser a autenticação
        raw_first = await websocket.receive_text()
        first_payload = json.loads(raw_first)
        auth_msg = ClientAuthMsg(**first_payload)
        target_host_id = auth_msg.host_id.replace(" ", "")

        # 1. Checagem de Rate Limit por IP e por Host
        if session_manager.rate_limiter.is_blocked(client_ip) or session_manager.rate_limiter.is_blocked(target_host_id):
            await websocket.send_text(AuthErrorMsg(
                code="RATE_LIMITED",
                message="Muitas tentativas com erro. Aguarde 5 minutos antes de tentar novamente."
            ).model_dump_json())
            await websocket.close(code=1008)
            return

        # 2. Verificar se o Host está online
        host_sess = session_manager.get_host(target_host_id)
        if not host_sess:
            session_manager.rate_limiter.record_failure(client_ip)
            session_manager.rate_limiter.record_failure(target_host_id)
            await websocket.send_text(AuthErrorMsg(
                code="INVALID_CREDENTIALS_OR_UNAVAILABLE",
                message="Credenciais inválidas ou computador indisponível."
            ).model_dump_json())
            await websocket.close(code=1008)
            return

        # 3. Bloqueio 1:1 de entrada por Host
        if host_sess.active_session_id is not None:
            await websocket.send_text(AuthErrorMsg(
                code="HOST_BUSY",
                message="Este computador já está em uma sessão remota ativa."
            ).model_dump_json())
            await websocket.close(code=1008)
            return

        # 4. Enviar solicitação de validação para o Host
        loop = asyncio.get_running_loop()
        verify_future = loop.create_future()
        session_manager.pending_verifications[session_id] = verify_future

        req_msg = HostVerifyRequestMsg(
            session_id=session_id,
            credential=auth_msg.credential,
            client_ip=client_ip
        )
        await host_sess.ws.send_text(req_msg.model_dump_json())

        # Aguardar resposta do host (timeout de 35s para dar tempo do modal de consentimento)
        try:
            verify_res: HostVerifyResponseMsg = await asyncio.wait_for(verify_future, timeout=35.0)
        except asyncio.TimeoutError:
            session_manager.rate_limiter.record_failure(client_ip)
            session_manager.rate_limiter.record_failure(target_host_id)
            await websocket.send_text(AuthErrorMsg(
                code="INVALID_CREDENTIALS_OR_UNAVAILABLE",
                message="Tempo esgotado aguardando autorização do computador remoto."
            ).model_dump_json())
            await websocket.close(code=1008)
            return

        # 5. Avaliar resultado da verificação
        if not verify_res.valid:
            session_manager.rate_limiter.record_failure(client_ip)
            session_manager.rate_limiter.record_failure(target_host_id)
            await websocket.send_text(AuthErrorMsg(
                code="INVALID_CREDENTIALS_OR_UNAVAILABLE",
                message="Credenciais inválidas ou computador indisponível."
            ).model_dump_json())
            await websocket.close(code=1008)
            return

        # Sucesso na autenticação
        session_manager.rate_limiter.record_success(client_ip)
        session_manager.rate_limiter.record_success(target_host_id)
        host_sess.active_session_id = session_id
        session_manager.register_client_session(
            session_id=session_id,
            host_id=target_host_id,
            ws=websocket,
            client_ip=client_ip,
        )

        ice_servers = generate_turn_credentials(username_prefix=f"client_{session_id}")
        await websocket.send_text(AuthSuccessMsg(
            session_id=session_id,
            host_id=target_host_id,
            access_type=verify_res.access_type if verify_res.access_type != "invalid" else "supervised_pin",
            ice_servers=ice_servers,
        ).model_dump_json())

        # Loop principal de troca de sinalização WebRTC para o cliente
        while True:
            text = await websocket.receive_text()
            data = json.loads(text)
            msg_type = data.get("type")

            if msg_type in ("sdp_offer", "sdp_answer"):
                sdp_msg = SdpSignalMsg(**data)
                target_host = session_manager.get_host(target_host_id)
                if target_host:
                    await target_host.ws.send_text(sdp_msg.model_dump_json())

            elif msg_type == "ice_candidate":
                ice_msg = IceCandidateMsg(**data)
                target_host = session_manager.get_host(target_host_id)
                if target_host:
                    await target_host.ws.send_text(ice_msg.model_dump_json())

    except WebSocketDisconnect:
        logger.info(f"Cliente desconectado: session_id={session_id}")
    except Exception as e:
        logger.error(f"Erro na conexão do cliente {session_id}: {e}")
    finally:
        session_manager.unregister_client_session(session_id)
        if target_host_id:
            host_sess = session_manager.get_host(target_host_id)
            if host_sess and host_sess.active_session_id == session_id:
                host_sess.active_session_id = None
                try:
                    await host_sess.ws.send_text(HostSessionClosedMsg(
                        session_id=session_id,
                        reason="Client disconnected"
                    ).model_dump_json())
                except Exception:
                    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
