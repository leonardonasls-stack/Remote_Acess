import asyncio
import json
import pytest
from fastapi.testclient import TestClient

import sys
import os
import importlib.util
sig_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if sig_dir not in sys.path:
    sys.path.insert(0, sig_dir)

sig_main_path = os.path.join(sig_dir, "main.py")
spec = importlib.util.spec_from_file_location("signaling_main", sig_main_path)
sig_main = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sig_main)

app = sig_main.app
session_manager = sig_main.session_manager

cfg_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "desktop-engine", "host_config.py"))
spec_cfg = importlib.util.spec_from_file_location("host_config_mod", cfg_path)
cfg_mod = importlib.util.module_from_spec(spec_cfg)
spec_cfg.loader.exec_module(cfg_mod)
HostConfigManager = cfg_mod.HostConfigManager


@pytest.fixture(autouse=True)
def reset_session_manager():
    session_manager.hosts.clear()
    session_manager.registered_identities.clear()
    session_manager.active_clients.clear()
    session_manager.rate_limiter.failures.clear()
    session_manager.rate_limiter.lockouts.clear()


def test_health():
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_host_registration_persistence():
    """Valida registro e persistência do host_id fixo associado ao device_secret."""
    client = TestClient(app)
    device_secret = "secret_teste_1234567890abcdef"

    # 1. Primeiro registro sorteia ou registra novo host
    with client.websocket_connect("/ws/host") as ws_host:
        ws_host.send_text(json.dumps({
            "type": "register_host",
            "host_id": None,
            "device_secret": device_secret
        }))
        data = json.loads(ws_host.receive_text())
        assert data["type"] == "host_registered"
        assigned_id = data["host_id"]
        assert len(assigned_id) == 9

    # 2. Segundo registro com mesmo device_secret mantém o mesmo host_id
    with client.websocket_connect("/ws/host") as ws_host2:
        ws_host2.send_text(json.dumps({
            "type": "register_host",
            "host_id": assigned_id,
            "device_secret": device_secret
        }))
        data2 = json.loads(ws_host2.receive_text())
        assert data2["host_id"] == assigned_id

    # 3. Tentativa de usurpar o ID com outro device_secret gera um novo ID seguro
    with client.websocket_connect("/ws/host") as ws_host3:
        ws_host3.send_text(json.dumps({
            "type": "register_host",
            "host_id": assigned_id,
            "device_secret": "hacker_secret_9999"
        }))
        data3 = json.loads(ws_host3.receive_text())
        assert data3["host_id"] != assigned_id


def test_client_auth_supervised_pin(tmp_path):
    """Testa handshake completo cliente-host com PIN Temporário de 6 dígitos."""
    client = TestClient(app)
    cfg = HostConfigManager(config_dir=str(tmp_path))
    host_id = cfg.host_id
    device_secret = cfg.device_secret
    temp_pin = cfg.temp_pin

    with client.websocket_connect("/ws/host") as ws_host:
        ws_host.send_text(json.dumps({
            "type": "register_host",
            "host_id": host_id,
            "device_secret": device_secret
        }))
        reg_data = json.loads(ws_host.receive_text())
        assert reg_data["type"] == "host_registered"

        # Conectar cliente
        with client.websocket_connect("/ws/client") as ws_client:
            ws_client.send_text(json.dumps({
                "type": "auth",
                "host_id": host_id,
                "credential": temp_pin
            }))

            # Host recebe pedido de validação
            host_req = json.loads(ws_host.receive_text())
            assert host_req["type"] == "verify_credential_req"
            sess_id = host_req["session_id"]
            rec_cred = host_req["credential"]

            # Host valida localmente com host_config
            access_type = cfg.verify_incoming_credential(rec_cred)
            assert access_type == "supervised_pin"

            # Host responde para o signaling server
            ws_host.send_text(json.dumps({
                "type": "verify_credential_res",
                "session_id": sess_id,
                "valid": True,
                "access_type": access_type
            }))

            # Cliente recebe auth_success
            client_auth_res = json.loads(ws_client.receive_text())
            assert client_auth_res["type"] == "auth_success"
            assert client_auth_res["session_id"] == sess_id
            assert client_auth_res["access_type"] == "supervised_pin"
            assert "ice_servers" in client_auth_res


def test_rate_limiting_lockout():
    """Valida bloqueio na 6ª tentativa errada com rate limiter."""
    client = TestClient(app)

    # 5 tentativas erradas para um host inexistente
    for _ in range(5):
        with client.websocket_connect("/ws/client") as ws_client:
            ws_client.send_text(json.dumps({
                "type": "auth",
                "host_id": "000000000",
                "credential": "wrong"
            }))
            res = json.loads(ws_client.receive_text())
            assert res["type"] == "auth_error"
            assert res["code"] == "INVALID_CREDENTIALS_OR_UNAVAILABLE"

    # Na 6ª tentativa, deve retornar RATE_LIMITED imediatamente
    with client.websocket_connect("/ws/client") as ws_client6:
        ws_client6.send_text(json.dumps({
            "type": "auth",
            "host_id": "000000000",
            "credential": "wrong"
        }))
        res6 = json.loads(ws_client6.receive_text())
        assert res6["type"] == "auth_error"
        assert res6["code"] == "RATE_LIMITED"


def test_host_config_unattended_pbkdf2(tmp_path):
    """Testa hash PBKDF2 e tempo constante na validação de senha fixa."""
    cfg = HostConfigManager(config_dir=str(tmp_path))
    assert not cfg.unattended_enabled

    with pytest.raises(ValueError):
        cfg.set_unattended_password("curta")

    cfg.set_unattended_password("SenhaSuperForte@2026")
    assert cfg.unattended_enabled
    assert cfg.unattended_password_hash is not None

    # Recarregar do disco para validar persistência
    cfg2 = HostConfigManager(config_dir=str(tmp_path))
    assert cfg2.unattended_enabled
    assert cfg2.verify_incoming_credential("SenhaSuperForte@2026") == "unattended"
    assert cfg2.verify_incoming_credential("SenhaErrada") == "invalid"
