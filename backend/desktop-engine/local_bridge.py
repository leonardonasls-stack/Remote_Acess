import asyncio
import json
import logging
from typing import Callable, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger("LocalBridge")


class LocalBridgeServer:
    """
    Servidor HTTP/WebSocket local rodando em 127.0.0.1:{porta}.
    Permite que a interface React (PyWebView ou Browser) sincronize o estado
    com o motor Python (Host ID, PIN temporário, aprovação de consentimento e senha).
    """

    def __init__(
        self,
        port: int = 8765,
        ipc_token: str | None = None,
        get_local_state_cb: Callable[[], dict[str, Any]] | None = None,
        on_action_cb: Callable[[dict[str, Any]], None] | None = None,
    ):
        self.port = port
        self.ipc_token = ipc_token
        self.get_local_state_cb = get_local_state_cb
        self.on_action_cb = on_action_cb

        self.app = FastAPI(title="Remote Access Local Bridge", version="2.2.0")
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.active_websockets: set[WebSocket] = set()
        self._setup_routes()

    def _setup_routes(self):
        @self.app.get("/health")
        async def health():
            return {"status": "ok", "service": "local_bridge"}

        @self.app.websocket("/ws/local")
        async def websocket_local(ws: WebSocket):
            await ws.accept()
            self.active_websockets.add(ws)

            # Enviar estado inicial imediatamente
            if self.get_local_state_cb:
                state = self.get_local_state_cb()
                await ws.send_text(json.dumps(state))

            try:
                while True:
                    text = await ws.receive_text()
                    data = json.loads(text)
                    if self.on_action_cb:
                        self.on_action_cb(data)
            except WebSocketDisconnect:
                pass
            except Exception as e:
                logger.error(f"Erro no WebSocket da ponte local: {e}")
            finally:
                self.active_websockets.discard(ws)

    async def broadcast_state(self, state: dict[str, Any]):
        """Notifica a UI local com o novo estado sincronizado."""
        msg = json.dumps(state)
        for ws in list(self.active_websockets):
            try:
                await ws.send_text(msg)
            except Exception:
                self.active_websockets.discard(ws)
