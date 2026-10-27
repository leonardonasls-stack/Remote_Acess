// -----------------------------------------------------------------------------
// Contratos TypeScript do Protocolo de Sinalização e IPC Local
// -----------------------------------------------------------------------------

export interface LocalState {
  type: "local_state";
  host_id: string;
  signaling_connected: boolean;
  temp_pin: string;
  pin_expires_in_sec: number;
  unattended_enabled: boolean;
  has_unattended_password: boolean;
  incoming_session: {
    session_id: string;
    client_ip: string;
  } | null;
}

export interface IncomingConsentRequest {
  type: "incoming_consent_request";
  request_id: string;
  client_ip: string;
  timeout_sec: number;
}

export interface IncomingUnattendedSetupRequest {
  type: "incoming_unattended_setup_request";
  request_id: string;
  client_ip: string;
  timeout_sec: number;
}

export type LocalBridgeMessage =
  | LocalState
  | IncomingConsentRequest
  | IncomingUnattendedSetupRequest;

// Ações enviadas pela UI Local -> Motor Python Local (127.0.0.1)
export type LocalActionMessage =
  | { type: "action_rotate_pin" }
  | { type: "action_set_unattended"; enabled: boolean; new_password?: string }
  | { type: "action_consent_decision"; request_id: string; approved: boolean }
  | { type: "action_unattended_setup_decision"; request_id: string; approved: boolean }
  | { type: "action_disconnect_incoming_session" };

// -----------------------------------------------------------------------------
// Contratos de Dados P2P (RTCDataChannel - Canais "control" e "pointer")
// -----------------------------------------------------------------------------

export interface ResMessage {
  v: 1;
  t: "res";
  w: number;
  h: number;
}

export interface MouseMoveMessage {
  v: 1;
  t: "mm";
  x: number; // 0.0000 .. 1.0000
  y: number; // 0.0000 .. 1.0000
}

export interface MouseButtonMessage {
  v: 1;
  t: "mb";
  b: 0 | 1 | 2; // 0=Left, 1=Middle, 2=Right
  d: 0 | 1;     // 1=Down, 0=Up
  x: number;
  y: number;
}

export interface MouseWheelMessage {
  v: 1;
  t: "ms";
  dx: number;
  dy: number;
}

export interface KeyboardMessage {
  v: 1;
  t: "kb";
  c: string; // KeyboardEvent.code (ex: "KeyA", "Enter")
  d: 0 | 1;  // 1=Down, 0=Up
}

export interface PingMessage {
  v: 1;
  t: "ping";
  ts: number;
}

export interface PongMessage {
  v: 1;
  t: "pong";
  ts: number;
}

export interface UnattendedSetupReq {
  v: 1;
  t: "unattended_setup_req";
  new_password: string;
  current_password?: string | null;
}

export interface UnattendedSetupRes {
  v: 1;
  t: "unattended_setup_res";
  status: "approved" | "rejected" | "invalid_password" | "physical_guard_blocked" | "pending_physical_approval";
}

// -----------------------------------------------------------------------------
// Estado de cada Sessão Remota no Navegador / App Desktop
// -----------------------------------------------------------------------------

export interface RemoteSession {
  id: string;           // session_id único
  hostId: string;       // ex: "482 910 384"
  label: string;        // ex: "482 910 384" ou nome amigável
  status: "connecting" | "authenticating" | "connected" | "disconnected" | "error";
  errorMessage?: string;
  rttMs: number;
  remoteWidth: number;
  remoteHeight: number;
  mode: "control" | "view";
  accessType?: "unattended" | "supervised_pin";
}

export interface RecentHost {
  hostId: string;
  label: string;
  lastConnectedAt: string;
}
