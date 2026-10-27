import base64
import hashlib
import hmac
import json
import os
import random
import secrets
import string
import time
from typing import Literal


class HostConfigManager:
    """
    Gerencia a identidade e credenciais da máquina Host:
    1. Persistência em %APPDATA%\\RemoteAccess\\host_config.json:
       - host_id (9 dígitos fixos)
       - device_secret (64 caracteres hex)
       - unattended_enabled (bool)
       - unattended_salt (base64)
       - unattended_password_hash (hex via PBKDF2-HMAC-SHA256, 200.000 iterações)
    2. PIN Temporário em memória:
       - 6 dígitos numéricos
       - TTL de 300 segundos (5 minutos)
       - Uso único (invalida após conexão)
       - Regenerado na 5ª falha de tentativa consecutiva
    3. Verificação de credenciais em tempo constante contra timing attacks.
    """

    PBKDF2_ITERATIONS = 200_000

    def __init__(self, config_dir: str | None = None):
        if config_dir is None:
            appdata = os.getenv("APPDATA") or os.path.expanduser("~")
            self.config_dir = os.path.join(appdata, "RemoteAccess")
        else:
            self.config_dir = config_dir

        self.config_file = os.path.join(self.config_dir, "host_config.json")
        os.makedirs(self.config_dir, exist_ok=True)

        # Estado persistido
        self.host_id: str = ""
        self.device_secret: str = ""
        self.unattended_enabled: bool = False
        self.unattended_salt: bytes | None = None
        self.unattended_password_hash: str | None = None

        # Estado efêmero em memória (PIN temporário supervisionado)
        self.temp_pin: str = ""
        self.pin_expires_at: float = 0.0
        self.pin_failed_attempts: int = 0

        self._load_or_initialize()
        self.rotate_temp_pin()

    def _load_or_initialize(self):
        """Carrega do arquivo host_config.json ou gera identidade na 1ª execução."""
        if os.path.isfile(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.host_id = data.get("host_id", "")
                    self.device_secret = data.get("device_secret", "")
                    self.unattended_enabled = data.get("unattended_enabled", False)
                    salt_b64 = data.get("unattended_salt")
                    self.unattended_salt = base64.b64decode(salt_b64) if salt_b64 else None
                    self.unattended_password_hash = data.get("unattended_password_hash")
            except Exception:
                pass

        # Se não existe ou arquivo corrompido, gera novo
        if not self.host_id or not self.device_secret:
            self.host_id = f"{random.randint(100_000_000, 999_999_999)}"
            self.device_secret = secrets.token_hex(32)
            self.save_config()

    def save_config(self):
        """Grava as configurações persistentes atomicamente."""
        data = {
            "host_id": self.host_id,
            "device_secret": self.device_secret,
            "unattended_enabled": self.unattended_enabled,
            "unattended_salt": base64.b64encode(self.unattended_salt).decode("utf-8") if self.unattended_salt else None,
            "unattended_password_hash": self.unattended_password_hash,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        temp_file = f"{self.config_file}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_file, self.config_file)

    def rotate_temp_pin(self) -> str:
        """Gera novo PIN temporário de 6 dígitos com TTL de 300 segundos."""
        self.temp_pin = "".join(secrets.choice(string.digits) for _ in range(6))
        self.pin_expires_at = time.time() + 300.0
        self.pin_failed_attempts = 0
        return self.temp_pin

    def get_temp_pin_remaining_seconds(self) -> int:
        remaining = int(self.pin_expires_at - time.time())
        return max(0, remaining)

    def is_temp_pin_valid(self) -> bool:
        return time.time() < self.pin_expires_at

    def set_unattended_password(self, password: str):
        """Configura Senha Fixa com PBKDF2-HMAC-SHA256 (200.000 iterações)."""
        if len(password) < 8:
            raise ValueError("A senha fixa deve ter no mínimo 8 caracteres.")

        self.unattended_salt = secrets.token_bytes(16)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            self.unattended_salt,
            self.PBKDF2_ITERATIONS,
        )
        self.unattended_password_hash = key.hex()
        self.unattended_enabled = True
        self.save_config()

    def disable_unattended(self):
        """Desativa o acesso por senha fixa."""
        self.unattended_enabled = False
        self.save_config()

    def remove_unattended_password(self):
        """Remove completamente a senha fixa configurada."""
        self.unattended_enabled = False
        self.unattended_salt = None
        self.unattended_password_hash = None
        self.save_config()

    def verify_incoming_credential(
        self, credential: str
    ) -> Literal["unattended", "supervised_pin", "invalid"]:
        """
        Verifica a credencial recebida.
        Executa comparações com hmac.compare_digest para evitar timing attacks.
        Retorna 'unattended', 'supervised_pin' ou 'invalid'.
        """
        now = time.time()
        is_unattended = False
        is_pin = False

        # 1. Checa Senha Fixa (se ativa)
        if self.unattended_enabled and self.unattended_salt and self.unattended_password_hash:
            computed_key = hashlib.pbkdf2_hmac(
                "sha256",
                credential.encode("utf-8"),
                self.unattended_salt,
                self.PBKDF2_ITERATIONS,
            ).hex()
            if hmac.compare_digest(computed_key, self.unattended_password_hash):
                is_unattended = True

        # 2. Checa PIN Temporário (tempo constante)
        if self.is_temp_pin_valid():
            # Comparação segura em tempo constante
            if hmac.compare_digest(credential.strip(), self.temp_pin):
                is_pin = True

        if is_unattended:
            return "unattended"

        if is_pin:
            # Uso único: rotaciona o PIN imediatamente após uso bem-sucedido
            self.rotate_temp_pin()
            return "supervised_pin"

        # Falha na credencial: contabiliza para mitigar tentativas locais
        self.pin_failed_attempts += 1
        if self.pin_failed_attempts >= 5:
            # Força rotação automática do PIN ao atingir 5 falhas
            self.rotate_temp_pin()

        return "invalid"
