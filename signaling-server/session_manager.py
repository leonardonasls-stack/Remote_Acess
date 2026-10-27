import asyncio
from dataclasses import dataclass, field
import hashlib
import hmac
import random
import time
from typing import Any
from fastapi import WebSocket


@dataclass
class HostSession:
    host_id: str
    secret_hash: str
    ws: WebSocket
    active_session_id: str | None = None
    connected_at: float = field(default_factory=time.time)


@dataclass
class ClientSession:
    session_id: str
    target_host_id: str
    ws: WebSocket
    client_ip: str
    connected_at: float = field(default_factory=time.time)


class RateLimiter:
    """
    Controla tentativas de autenticação para mitigar força bruta:
    - Máximo 5 falhas por minuto por IP ou por Host ID.
    - Se atingir 5 falhas, aplica lockout de 5 minutos (300 segundos).
    """

    def __init__(self, max_failures: int = 5, window_sec: int = 60, lockout_sec: int = 300):
        self.max_failures = max_failures
        self.window_sec = window_sec
        self.lockout_sec = lockout_sec
        self.failures: dict[str, list[float]] = {}
        self.lockouts: dict[str, float] = {}

    def is_blocked(self, key: str) -> bool:
        now = time.time()
        lockout_until = self.lockouts.get(key, 0)
        if now < lockout_until:
            return True
        return False

    def record_failure(self, key: str):
        now = time.time()
        timestamps = [t for t in self.failures.get(key, []) if (now - t) < self.window_sec]
        timestamps.append(now)
        self.failures[key] = timestamps

        if len(timestamps) >= self.max_failures:
            self.lockouts[key] = now + self.lockout_sec
            self.failures[key] = []

    def record_success(self, key: str):
        self.failures.pop(key, None)
        self.lockouts.pop(key, None)


class SessionManager:
    """
    Gerenciador central de conexões em memória para o Signaling Server:
    - Mapeia hosts registrados: host_id -> HostSession
    - Mapeia segredos de host para persistência do ID: host_id -> secret_hash
    - Mapeia sessões ativas: session_id -> ClientSession
    - Suporta espera assíncrona por resposta de autenticação do host.
    """

    def __init__(self):
        self.hosts: dict[str, HostSession] = {}
        self.registered_identities: dict[str, str] = {}  # host_id -> secret_hash
        self.active_clients: dict[str, ClientSession] = {}  # session_id -> ClientSession
        self.rate_limiter = RateLimiter(max_failures=5, window_sec=60, lockout_sec=300)
        self.pending_verifications: dict[str, asyncio.Future] = {}  # session_id -> Future

    def _hash_secret(self, secret: str) -> str:
        return hashlib.sha256(secret.encode("utf-8")).hexdigest()

    def generate_unique_host_id(self) -> str:
        """Gera um host_id de 9 dígitos formatável como XXX XXX XXX."""
        while True:
            candidate = f"{random.randint(100_000_000, 999_999_999)}"
            if candidate not in self.registered_identities:
                return candidate

    def register_host(self, ws: WebSocket, host_id: str | None, device_secret: str) -> str:
        secret_hash = self._hash_secret(device_secret)

        if host_id:
            # Tentar reivindicar ID existente
            saved_hash = self.registered_identities.get(host_id)
            if saved_hash:
                # Compara hashes com tempo constante para evitar timing attacks
                if not hmac.compare_digest(saved_hash, secret_hash):
                    # Segredo não bate: gera um novo ID seguro para o dispositivo
                    host_id = self.generate_unique_host_id()
            else:
                self.registered_identities[host_id] = secret_hash
        else:
            host_id = self.generate_unique_host_id()
            self.registered_identities[host_id] = secret_hash

        # Fecha conexão anterior do mesmo host_id se houver
        if host_id in self.hosts:
            old_host = self.hosts[host_id]
            try:
                asyncio.create_task(old_host.ws.close(code=1000, reason="Host reconnected"))
            except Exception:
                pass

        self.hosts[host_id] = HostSession(
            host_id=host_id,
            secret_hash=secret_hash,
            ws=ws
        )
        return host_id

    def unregister_host(self, host_id: str, ws: WebSocket | None = None):
        current = self.hosts.get(host_id)
        if current and (ws is None or current.ws == ws):
            self.hosts.pop(host_id, None)

    def get_host(self, host_id: str) -> HostSession | None:
        return self.hosts.get(host_id)

    def register_client_session(self, session_id: str, host_id: str, ws: WebSocket, client_ip: str) -> ClientSession:
        cs = ClientSession(
            session_id=session_id,
            target_host_id=host_id,
            ws=ws,
            client_ip=client_ip
        )
        self.active_clients[session_id] = cs
        return cs

    def unregister_client_session(self, session_id: str):
        self.active_clients.pop(session_id, None)
        future = self.pending_verifications.pop(session_id, None)
        if future and not future.done():
            future.cancel()
