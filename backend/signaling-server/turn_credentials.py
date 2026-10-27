import base64
import hashlib
import hmac
import os
import time


def generate_turn_credentials(
    username_prefix: str = "remoteaccess",
    ttl: int = 3600,
) -> list[dict]:
    """
    Gera lista de ice_servers.
    Em desenvolvimento local, inclui STUN público default do Google.
    Se TURN_SHARED_SECRET e TURN_URL estiverem configurados nas variáveis de ambiente,
    calcula HMAC-SHA1 conforme especificação padrão do coturn (turn REST API).
    """
    ice_servers = [
        {"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]}
    ]

    turn_secret = os.getenv("TURN_SHARED_SECRET")
    turn_url = os.getenv("TURN_URL")

    if turn_secret and turn_url:
        expiry = int(time.time()) + ttl
        username = f"{expiry}:{username_prefix}"
        
        # HMAC-SHA1 do username usando o shared secret
        digest = hmac.new(
            turn_secret.encode("utf-8"),
            username.encode("utf-8"),
            hashlib.sha1
        ).digest()
        credential = base64.b64encode(digest).decode("utf-8")

        urls = [turn_url] if isinstance(turn_url, str) else turn_url
        ice_servers.append({
            "urls": urls,
            "username": username,
            "credential": credential
        })

    return ice_servers
