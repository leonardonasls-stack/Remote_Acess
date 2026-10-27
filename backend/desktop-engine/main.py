import asyncio
import ctypes
import json
import logging
import os
import sys
import threading
import uvicorn
import webview

from host_config import HostConfigManager
from input_controller import InputController
from physical_guard import PhysicalInputGuard
from host_rtc import HostRTCClient
from local_bridge import LocalBridgeServer

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("DesktopEngine")


def init_dpi_awareness():
    """Ativa Per-Monitor DPI Awareness no Windows antes de qualquer chamada gráfica."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        logger.info("DPI Awareness ativado: PROCESS_PER_MONITOR_DPI_AWARE")
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
            logger.info("DPI Awareness ativado: System DPI Aware")
        except Exception as e:
            logger.warning(f"Falha ao configurar DPI Awareness: {e}")


class DesktopApplication:
    def __init__(self):
        init_dpi_awareness()

        self.config_manager = HostConfigManager()
        self.input_controller = InputController()
        self.pending_unattended_password: str | None = None
        self.pending_consent_future: asyncio.Future | None = None

        # 1. Guarda Físico Anti-Auto-Clique e Kill Switch (Ctrl+Alt+Shift+Q)
        self.physical_guard = PhysicalInputGuard(on_kill_switch_cb=self._on_kill_switch)
        self.physical_guard.start()

        # 2. Ponte Local (127.0.0.1:8765)
        self.local_bridge = LocalBridgeServer(
            port=8765,
            get_local_state_cb=self._get_local_state,
            on_action_cb=self._on_local_action,
        )

        # 3. Cliente WebRTC do Host
        signaling_url = os.getenv("SIGNALING_URL", "ws://127.0.0.1:8000/ws/host")
        self.host_rtc = HostRTCClient(
            signaling_url=signaling_url,
            host_id=self.config_manager.host_id,
            device_secret=self.config_manager.device_secret,
            verify_credential_callback=self._verify_credential,
            on_control_message=self._on_control_message,
            on_pointer_message=self._on_pointer_message,
        )

        self.loop: asyncio.AbstractEventLoop | None = None

    def _get_local_state(self) -> dict:
        return {
            "type": "local_state",
            "host_id": self.config_manager.host_id,
            "signaling_connected": self.host_rtc.ws is not None,
            "temp_pin": self.config_manager.temp_pin,
            "pin_expires_in_sec": self.config_manager.get_temp_pin_remaining_seconds(),
            "unattended_enabled": self.config_manager.unattended_enabled,
            "has_unattended_password": self.config_manager.unattended_password_hash is not None,
            "incoming_session": (
                {"session_id": self.host_rtc.active_session_id, "client_ip": "Conectado"}
                if self.host_rtc.active_session_id
                else None
            ),
        }

    def _on_kill_switch(self):
        """Encerra qualquer sessão recebida e reseta teclas presas."""
        logger.warning("Kill switch acionado! Derrubando conexão recebida...")
        self.input_controller.release_all()
        if self.loop and self.host_rtc.active_session_id:
            asyncio.run_coroutine_threadsafe(
                self.host_rtc.close_active_session("Kill switch ativado pelo usuário local"),
                self.loop,
            )
            asyncio.run_coroutine_threadsafe(
                self.local_bridge.broadcast_state(self._get_local_state()),
                self.loop,
            )

    async def _verify_credential(self, credential: str, client_ip: str) -> tuple[bool, str]:
        """Avalia PIN ou Senha Fixa com suporte a modal de consentimento."""
        result = self.config_manager.verify_incoming_credential(credential)

        if result == "unattended":
            logger.info("Conexão autorizada via Senha Fixa (Não Supervisionada)")
            return True, "unattended"

        elif result == "supervised_pin":
            logger.info("PIN Temporário correto! Solicitando consentimento ao usuário local...")
            # Notificar UI Local com modal de consentimento
            await self.local_bridge.broadcast_state({
                "type": "incoming_consent_request",
                "request_id": "req_consent",
                "client_ip": client_ip,
                "timeout_sec": 30,
            })

            # Aguardar decisão do usuário local
            self.pending_consent_future = self.loop.create_future()
            try:
                approved = await asyncio.wait_for(self.pending_consent_future, timeout=30.0)
                return approved, "supervised_pin" if approved else "invalid"
            except asyncio.TimeoutError:
                return False, "invalid"

        return False, "invalid"

    def _on_control_message(self, msg: dict):
        t = msg.get("t")
        if t == "mb":
            self.input_controller.mouse_button(msg["b"], msg["d"] == 1, msg.get("x"), msg.get("y"))
        elif t == "ms":
            self.input_controller.mouse_wheel(msg.get("dx", 0), msg.get("dy", 0))
        elif t == "kb":
            self.input_controller.keyboard_key(msg["c"], msg["d"] == 1)
        elif t == "mode":
            self.input_controller.set_mode(msg.get("mode", "control"))
        elif t == "unattended_setup_req":
            # Técnico remoto solicitou cadastrar senha fixa
            new_pwd = msg.get("new_password")
            if new_pwd:
                self.pending_unattended_password = new_pwd
                if self.loop:
                    asyncio.run_coroutine_threadsafe(
                        self.local_bridge.broadcast_state({
                            "type": "incoming_unattended_setup_request",
                            "request_id": "req_unatt",
                            "client_ip": "Operador Remoto",
                            "timeout_sec": 30,
                        }),
                        self.loop,
                    )

    def _on_pointer_message(self, msg: dict):
        if msg.get("t") == "mm":
            self.input_controller.move_mouse(msg["x"], msg["y"])

    def _on_local_action(self, action: dict):
        act_type = action.get("type")

        if act_type == "action_rotate_pin":
            self.config_manager.rotate_temp_pin()
            if self.loop:
                asyncio.run_coroutine_threadsafe(
                    self.local_bridge.broadcast_state(self._get_local_state()), self.loop
                )

        elif act_type == "action_set_unattended":
            enabled = action.get("enabled", False)
            if enabled and action.get("new_password"):
                self.config_manager.set_unattended_password(action["new_password"])
            else:
                self.config_manager.disable_unattended()

        elif act_type == "action_consent_decision":
            if self.pending_consent_future and not self.pending_consent_future.done():
                self.pending_consent_future.set_result(action.get("approved", False))

        elif act_type == "action_unattended_setup_decision":
            approved = action.get("approved", False)
            if approved and self.pending_unattended_password:
                # RF-H08: Validação FÍSICA Anti-Auto-Clique!
                if not self.physical_guard.is_recent_physical_click():
                    logger.warning("Bloqueio Anti-Auto-Clique: Nenhum clique físico detectado!")
                    # Notificar cliente que o clique não foi físico
                    return

                self.config_manager.set_unattended_password(self.pending_unattended_password)
                self.pending_unattended_password = None
                logger.info("Senha fixa provisionada com sucesso após aprovação com mouse físico!")

        elif act_type == "action_disconnect_incoming_session":
            self._on_kill_switch()

    def run_backend_services(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        # Rodar Local Bridge (Uvicorn)
        config = uvicorn.Config(self.local_bridge.app, host="127.0.0.1", port=8765, log_level="warning")
        server = uvicorn.Server(config)

        async def main_tasks():
            await asyncio.gather(
                server.serve(),
                self.host_rtc.start(),
            )

        self.loop.run_until_complete(main_tasks())

    def start(self):
        backend_thread = threading.Thread(target=self.run_backend_services, daemon=True)
        backend_thread.start()

        # Determinar URL para WebView (dev server do Vite ou build estático)
        ui_dist = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "unified-ui", "dist", "index.html")
        )
        ui_url = f"file:///{ui_dist}" if os.path.isfile(ui_dist) else "http://localhost:5173"

        logger.info(f"Iniciando janela nativa PyWebView apontando para: {ui_url}")
        webview.create_window(
            title="RemoteAccess",
            url=ui_url,
            width=960,
            height=640,
            min_size=(800, 540),
            background_color="#090D16",
        )
        webview.start()
        self.physical_guard.stop()


if __name__ == "__main__":
    app = DesktopApplication()
    app.start()
