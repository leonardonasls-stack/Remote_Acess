from typing import Literal
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------------
# Mensagens enviadas pelo HOST -> SIGNALING SERVER
# -----------------------------------------------------------------------------

class RegisterHostMsg(BaseModel):
    """Host anuncia presença ou registra/recupera seu host_id fixo de 9 dígitos."""
    type: Literal["register_host"] = "register_host"
    host_id: str | None = Field(default=None, description="Host ID prévio de 9 dígitos ou None para sortear novo")
    device_secret: str = Field(..., description="Segredo único de máquina para autenticação e posse do host_id")


class HostVerifyResponseMsg(BaseModel):
    """Resposta do Host à verificação de credencial de um cliente tentando conectar."""
    type: Literal["verify_credential_res"] = "verify_credential_res"
    session_id: str
    valid: bool
    access_type: Literal["unattended", "supervised_pin", "invalid"] = "invalid"


# -----------------------------------------------------------------------------
# Mensagens enviadas pelo SIGNALING SERVER -> HOST
# -----------------------------------------------------------------------------

class HostRegisteredMsg(BaseModel):
    type: Literal["host_registered"] = "host_registered"
    host_id: str
    ice_servers: list[dict]


class HostVerifyRequestMsg(BaseModel):
    """Signaling Server solicita que o Host valide a credencial fornecida pelo cliente."""
    type: Literal["verify_credential_req"] = "verify_credential_req"
    session_id: str
    credential: str
    client_ip: str


class HostSessionClosedMsg(BaseModel):
    type: Literal["session_closed"] = "session_closed"
    session_id: str
    reason: str


# -----------------------------------------------------------------------------
# Mensagens enviadas pelo CLIENT -> SIGNALING SERVER
# -----------------------------------------------------------------------------

class ClientAuthMsg(BaseModel):
    """Cliente tentando se conectar a um Host fornecendo ID e credencial (PIN ou Senha)."""
    type: Literal["auth"] = "auth"
    host_id: str = Field(..., description="ID de 9 dígitos do Host de destino")
    credential: str = Field(..., description="PIN temporário ou Senha Fixa")


# -----------------------------------------------------------------------------
# Mensagens trocadas entre CLIENT e SIGNALING SERVER (Auth e Erros)
# -----------------------------------------------------------------------------

class AuthSuccessMsg(BaseModel):
    type: Literal["auth_success"] = "auth_success"
    session_id: str
    host_id: str
    access_type: Literal["unattended", "supervised_pin"]
    ice_servers: list[dict]


class AuthErrorMsg(BaseModel):
    """Erro genérico padronizado para mitigar enumeração de contas e timing attacks."""
    type: Literal["auth_error"] = "auth_error"
    code: Literal["INVALID_CREDENTIALS_OR_UNAVAILABLE", "RATE_LIMITED", "HOST_BUSY"] = "INVALID_CREDENTIALS_OR_UNAVAILABLE"
    message: str = "Credenciais inválidas ou computador indisponível."


# -----------------------------------------------------------------------------
# Troca de Sinalização WebRTC (SDP e ICE Candidates)
# -----------------------------------------------------------------------------

class SdpSignalMsg(BaseModel):
    """Encaminhamento de SDP Offer ou Answer entre Host e Client."""
    type: Literal["sdp_offer", "sdp_answer"]
    session_id: str
    sdp: str


class IceCandidateMsg(BaseModel):
    """Encaminhamento de ICE candidate."""
    type: Literal["ice_candidate"] = "ice_candidate"
    session_id: str
    candidate: dict
