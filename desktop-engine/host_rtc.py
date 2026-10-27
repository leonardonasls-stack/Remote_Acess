import asyncio
import json
import logging
from typing import Callable, Coroutine, Any
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCDataChannel
import websockets

from screen_track import ScreenStreamTrack

logger = logging.getLogger("HostRTC")


class HostRTCClient:
    """
    Cliente WebRTC do Host:
    - Conecta ao Signaling Server (/ws/host).
    - Negocia ofertas SDP e ICE candidates.
    - Anexa ScreenStreamTrack (mss + cv2 YUV420p).
    - Registra listeners nos canais 'control' e 'pointer'.
    """

    def __init__(
        self,
        signaling_url: str,
        host_id: str,
        device_secret: str,
        verify_credential_callback: Callable[[str, str], Coroutine[Any, Any, tuple[bool, str]]],
        on_control_message: Callable[[dict], None] | None = None,
        on_pointer_message: Callable[[dict], None] | None = None,
    ):
        self.signaling_url = signaling_url
        self.host_id = host_id
        self.device_secret = device_secret
        self.verify_credential_callback = verify_credential_callback
        self.on_control_message = on_control_message
        self.on_pointer_message = on_pointer_message

        self.ws: websockets.WebSocketClientProtocol | None = None
        self.pc: RTCPeerConnection | None = None
        self.current_track: ScreenStreamTrack | None = None
        self.active_session_id: str | None = None
        self.is_running = False

    async def start(self):
        self.is_running = True
        while self.is_running:
            try:
                logger.info(f"Conectando ao Signaling Server em {self.signaling_url}...")
                async with websockets.connect(self.signaling_url) as ws:
                    self.ws = ws

                    # 1. Registrar Host
                    await ws.send(json.dumps({
                        "type": "register_host",
                        "host_id": self.host_id,
                        "device_secret": self.device_secret,
                    }))

                    # 2. Loop de escuta de mensagens do servidor
                    async for raw_msg in ws:
                        data = json.loads(raw_msg)
                        await self._handle_signaling_message(data)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Erro na conexão com signaling: {e}. Reconectando em 3s...")
                await asyncio.sleep(3)

    async def _handle_signaling_message(self, data: dict):
        msg_type = data.get("type")

        if msg_type == "host_registered":
            self.host_id = data["host_id"]
            logger.info(f"Host registrado com sucesso no Signaling Server: ID={self.host_id}")

        elif msg_type == "verify_credential_req":
            session_id = data["session_id"]
            credential = data["credential"]
            client_ip = data["client_ip"]

            # Callback para host_config / modal de consentimento local
            is_valid, access_type = await self.verify_credential_callback(credential, client_ip)

            if self.ws:
                await self.ws.send(json.dumps({
                    "type": "verify_credential_res",
                    "session_id": session_id,
                    "valid": is_valid,
                    "access_type": access_type,
                }))

        elif msg_type == "sdp_offer":
            session_id = data["session_id"]
            sdp = data["sdp"]
            await self._handle_sdp_offer(session_id, sdp)

        elif msg_type == "session_closed":
            session_id = data.get("session_id")
            if self.active_session_id == session_id:
                await self.close_active_session("Sessão finalizada pelo cliente")

    async def _handle_sdp_offer(self, session_id: str, sdp: str):
        logger.info(f"Recebida SDP Offer para session_id={session_id}")
        await self.close_active_session("Nova sessão autorizada")

        self.active_session_id = session_id
        self.pc = RTCPeerConnection()

        # Anexar track de captura de tela (30 FPS)
        self.current_track = ScreenStreamTrack(target_fps=30)
        self.pc.addTrack(self.current_track)

        # Tratar DataChannels criados pelo Client
        @self.pc.on("datachannel")
        def on_datachannel(channel: RTCDataChannel):
            logger.info(f"DataChannel aberto: {channel.label}")

            if channel.label == "control":
                # Enviar resolução remota assim que o canal abrir
                @channel.on("open")
                def on_open():
                    channel.send(json.dumps({
                        "v": 1,
                        "t": "res",
                        "w": self.current_track.out_w if self.current_track else 1920,
                        "h": self.current_track.out_h if self.current_track else 1080,
                    }))

                @channel.on("message")
                def on_message(message):
                    try:
                        parsed = json.loads(message)
                        if self.on_control_message:
                            self.on_control_message(parsed)
                    except Exception as err:
                        logger.error(f"Erro processando mensagem de controle: {err}")

            elif channel.label == "pointer":
                @channel.on("message")
                def on_pointer(message):
                    try:
                        parsed = json.loads(message)
                        if self.on_pointer_message:
                            self.on_pointer_message(parsed)
                    except Exception:
                        pass

        # Aceitar Offer e criar Answer
        await self.pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type="offer"))
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        if self.ws:
            await self.ws.send(json.dumps({
                "type": "sdp_answer",
                "session_id": session_id,
                "sdp": answer.sdp,
            }))

    async def close_active_session(self, reason: str = "Desconectado"):
        if self.current_track:
            self.current_track.close()
            self.current_track = None

        if self.pc:
            await self.pc.close()
            self.pc = None

        self.active_session_id = None
        logger.info(f"Sessão Host finalizada: {reason}")

    async def stop(self):
        self.is_running = False
        await self.close_active_session("Host parado")
        if self.ws:
            await self.ws.close()
