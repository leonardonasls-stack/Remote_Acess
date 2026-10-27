# TRD — Technical Requirements Document
**Projeto:** Ferramenta Unificada de Acesso Remoto de Baixa Latência (Estilo AnyDesk — Desktop + Web)  
**Versão:** 2.2 (Interface Minimalista Multi-Abas `+`, Provisionamento Remoto de Senha Fixa e Guarda Anti-Auto-Clique)  
**Data:** 26/10/2026  
**Documento de Produto Pareado:** [PRD.md](./PRD.md) (v2.2)  
**Status:** Aprovado para Execução  

---

## 1. Visão Geral da Engenharia e Stack Tecnológica

Este **TRD (Technical Requirements Document)** especifica a arquitetura técnica do **Aplicativo Unificado de Acesso Remoto**, onde cada instância instalada em um computador Windows funciona simultaneamente como **Host ("Esta Bancada")** e **Client ("Controlar Outro Computador")** na mesma janela, mantendo também compatibilidade para acesso puro via navegador web (**Web Client Zero-Install**).

### 1.1. Stack e Versões Fixadas

| Camada / Módulo | Tecnologia / Biblioteca | Versão Alvo | Responsabilidade Técnica |
| :--- | :--- | :--- | :--- |
| **Core Engine (Local)** | Python (CPython 64-bit) | `3.11.x` ou `3.12.x` | Daemon local: gerencia identidade, WebRTC Host, captura e `SendInput` |
| **Janela Desktop Unificada** | `pywebview` (Edge WebView2) | `>= 5.0` | Janela nativa leve no Windows renderizando a UI unificada |
| **Ponte IPC Local** | `FastAPI` / `websockets` (`127.0.0.1`) | `>= 0.115.0` | Canal IPC autenticado (`local_ipc_token`) entre a UI React e o motor Host local |
| **WebRTC (Host Engine)** | `aiortc` + `av` (PyAV) | `aiortc >= 1.9.0`, `av >= 12.0.0` | Transmissão da tela local e recepção de DataChannels quando a máquina é acessada |
| **Captura de Tela** | `mss` + `numpy` | `mss >= 9.0.1`, `numpy >= 1.26.0` | Captura GDI em memória e conversão rápida para `av.VideoFrame` (`yuv420p`) |
| **Injeção de Input & Hooks** | `ctypes` (`user32.dll`, `shcore.dll`) | Nativo (Win32 API) | `SendInput`, `SetProcessDpiAwareness`, `WH_KEYBOARD_LL` + `WH_MOUSE_LL` (Anti-Injeção) |
| **Interface Unificada (UI)** | `React 18` + `TypeScript` + `Vite` | `React 18+`, `TS 5.x` | Painel duplo estilo AnyDesk ("Esta Bancada" + "Outra Bancada") + Abas de Sessão WebRTC |
| **Signaling Server (Cloud)** | `FastAPI` + `uvicorn[standard]` | `fastapi >= 0.115.0` | Servidor WSS central na nuvem para descoberta de IDs, roteamento de auth e SDP/ICE |
| **NAT Traversal** | `coturn` (STUN / TURN) | `4.6+` | Descoberta de rota P2P e relay UDP/TLS com credenciais efêmeras (`HMAC-SHA1`) |

---

## 2. Arquitetura Unificada (Como o Programa Único Funciona)

```mermaid
flowchart TB
    subgraph App["Aplicativo Unificado no PC (Windows 10/11)"]
        subgraph UI["Janela Unificada (PyWebView / Browser - React + TS)"]
            TAB_HOME["Aba Início (Split View Estilo AnyDesk)"]
            PANEL_LEFT["Painel Esquerdo: ESTA BANCADA\n- Exibe Meu ID (482 910 384)\n- Exibe PIN Temporário (5m)\n- Config Senha Não Supervisionada\n- Modal 'Aceitar / Recusar'"]
            PANEL_RIGHT["Painel Direito: OUTRA BANCADA\n- Input ID do Parceiro + PIN/Senha\n- Lista de Sessões Recentes"]
            TAB_SESSION["Abas de Sessão Remota Ativa\n- Player <video> WebRTC\n- HUD + Botão '🔑 Acesso Permanente'"]
            TAB_HOME --> PANEL_LEFT
            TAB_HOME --> PANEL_RIGHT
            PANEL_RIGHT -->|Ao Conectar| TAB_SESSION
        end

        subgraph Engine["Motor Python Local (127.0.0.1)"]
            IPC["Local Control Server (127.0.0.1)\nProtegido por local_ipc_token"]
            CFG["HostConfig (%APPDATA%)\nhost_id fixo + device_secret\n+ unattended_password_hash"]
            GUARD["PhysicalInputGuard (Hooks Win32)\nWH_KEYBOARD_LL + WH_MOUSE_LL\nBloqueia Auto-Clique Remoto"]
            HOST_RTC["Módulo Host WebRTC (aiortc)\nScreenStreamTrack (mss)\n+ Win32 SendInput"]
            IPC <--> CFG
            IPC <--> HOST_RTC
            GUARD --> IPC
            GUARD --> HOST_RTC
        end

        PANEL_LEFT <==>|WS Local 127.0.0.1| IPC
    end

    subgraph Cloud["Infraestrutura de Sinalização e Rede"]
        SIG["Signaling Server (FastAPI WSS)"]
        TURN["STUN / TURN Server (coturn)"]
    end

    HOST_RTC <-->|WSS (/ws/host)| SIG
    TAB_SESSION <-->|WSS (/ws/client)| SIG
    HOST_RTC <==>|Fluxo P2P WebRTC (Vídeo SRTP + DataChannels DTLS)| TAB_SESSION
    HOST_RTC -.-> TURN
    TAB_SESSION -.-> TURN
```

---

## 3. Especificação da Ponte Local (`Local Control API` — `127.0.0.1`)

Rastreabilidade com o PRD: `RF-H01`, `RF-H05`, `RF-H07`, `RF-H08`, `RF-C01`.

### 3.1. Segurança da Ponte Local (`local_ipc_token`)
- Ao iniciar o aplicativo unificado, o processo Python gera um `local_ipc_token = secrets.token_urlsafe(32)` e aloca uma porta local em `127.0.0.1`.
- A janela `pywebview` recebe o token em memória na inicialização, impedindo acesso externo via navegador.

### 3.2. Mensagens da Ponte Local (`/ws/local`)

```json
// 1. Estado sincronizado enviado pelo Motor Python -> UI Local
{
  "type": "local_state",
  "host_id": "482910384",
  "signaling_connected": true,
  "temp_pin": "739201",
  "pin_expires_in_sec": 284,
  "unattended_enabled": true,
  "has_unattended_password": true,
  "incoming_session": null
}

// 2. Alerta de Solicitação de Acesso Supervisionado (Motor Python -> UI Local)
{
  "type": "incoming_consent_request",
  "request_id": "req_01",
  "client_ip": "203.0.113.42",
  "timeout_sec": 30
}

// 3. Alerta de Provisionamento Remoto de Senha Permanente (Motor Python -> UI Local)
{
  "type": "incoming_unattended_setup_request",
  "request_id": "unatt_01",
  "client_ip": "203.0.113.42",
  "timeout_sec": 30
}

// 4. Ações do Usuário Físico na UI Local -> Motor Python
{ "type": "action_rotate_pin" }
{ "type": "action_set_unattended", "enabled": true, "new_password": "MinhaSenhaForte@2026" }
{ "type": "action_consent_decision", "request_id": "req_01", "approved": true }
{ "type": "action_unattended_setup_decision", "request_id": "unatt_01", "approved": true }
{ "type": "action_disconnect_incoming_session" }
```

---

## 4. Provisionamento Remoto de Senha Não Supervisionada e Guarda Anti-Auto-Clique

Rastreabilidade com o PRD: `RF-H08`, `RF-C04`.

### 4.1. Fluxo P2P de Provisionamento (`RTCDataChannel` — Canal `control`)
O pedido de configuração de Senha Permanente feito pelo operador remoto trafega **exclusivamente dentro do túnel P2P criptografado (DTLS-SCTP)** do canal `control`, sem passar pelo Signaling Server:

```json
// 1. Operador Remoto -> Host (Solicitação enviada pelo HUD da sessão)
{
  "v": 1,
  "t": "unattended_setup_req",
  "new_password": "SenhaDaEquipeTI@2026",
  "current_password": null // Obrigatório apenas se quiser trocar sem prompt quando já entrou em modo unattended
}

// 2. Host -> Operador Remoto (Status intermediário quando exige aprovação física no Host)
{
  "v": 1,
  "t": "unattended_setup_res",
  "status": "pending_physical_approval"
}

// 3. Host -> Operador Remoto (Resultado final)
{
  "v": 1,
  "t": "unattended_setup_res",
  "status": "approved" // "approved" | "rejected" | "invalid_password" | "physical_guard_blocked"
}
```

### 4.2. Arquitetura do `PhysicalInputGuard` (Prevenção de Auto-Aprovação via `SendInput`)
Quando há uma sessão remota ativa na máquina Host, o operador remoto possui controle do cursor via `SendInput`. Para impedir que o próprio operador remoto clique no botão **"✅ Permitir Acesso Permanente"** (ou altere a senha no painel local do Host):

1. **Monitoramento em `WH_MOUSE_LL` e `WH_KEYBOARD_LL`:**
   - Na estrutura `MSLLHOOKSTRUCT` do hook `WH_MOUSE_LL`, o Windows define a flag `LLMHF_INJECTED = 0x00000001` (e `LLMHF_LOWER_IL_INJECTED = 0x00000002`) para qualquer evento gerado por `SendInput`.
   - Na estrutura `KBDLLHOOKSTRUCT` do hook `WH_KEYBOARD_LL`, o Windows define a flag `LLKHF_INJECTED = 0x00000010`.
2. **Rastreamento de Último Input Físico vs. Injetado:**
   ```python
   if (mouse_struct.flags & LLMHF_INJECTED) == 0:
       self.last_physical_mouse_down_ts = time.monotonic()
   else:
       self.last_injected_mouse_down_ts = time.monotonic()
   ```
3. **Validação na Aprovação (`verify_physical_interaction()`):**
   - Quando o motor Python recebe `action_unattended_setup_decision(approved=True)` ou `action_set_unattended` enquanto uma sessão remota está ativa:
     - Ele verifica se `(time.monotonic() - self.last_physical_mouse_down_ts) < 0.8` (ou se a tecla física `F8` foi pressionada sem `LLKHF_INJECTED`).
     - Se o clique que acionou o botão foi injetado remotamente (`last_injected_mouse_down_ts >= last_physical_mouse_down_ts`), o Host **rejeita a aprovação** e mantém um aviso no modal: *"Aprovação bloqueada: utilize o mouse físico deste computador (cliques remotos não são permitidos para esta ação)"*.

---

## 5. Especificação do Pipeline de Vídeo (`screen_track.py`)

Rastreabilidade com o PRD: `RF-H02`, `RF-H03`.

1. **DPI Awareness:** Executa `ctypes.windll.shcore.SetProcessDpiAwareness(2)` (`PROCESS_PER_MONITOR_DPI_AWARE`) na inicialização do processo.
2. **Captura (`mss`) e Alinhamento Par:**
   - Captura monitor primário em `BGRA` (`uint8`).
   - Aplica *downscale* proporcional se exceder `1920x1080` e garante dimensões pares (`out_w = int(raw_w * scale) & ~1`, `out_h = int(raw_h * scale) & ~1`).
   - Converte para `av.VideoFrame` (`yuv420p`) com clock RTP de `90 kHz` e pacing de `30 FPS`.

---

## 6. Especificação de Injeção de Input (`input_controller.py`)

Rastreabilidade com o PRD: `RF-H04`, `RF-H05`, `RF-H06`.

1. **Win32 `SendInput` (`ctypes`):**
   - **Mouse:** Coordenadas absolutas normalizadas no espaço `0..65535` (`MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE`), botões (`left`, `right`, `middle`) e scroll (`MOUSEEVENTF_WHEEL` / `MOUSEEVENTF_HWHEEL` em múltiplos de `120`).
   - **Teclado:** Mapeamento direto de `KeyboardEvent.code` para **Hardware Scancode Set 1** (`KEYEVENTF_SCANCODE` + `KEYEVENTF_EXTENDEDKEY`), independente de layout ABNT2/US.
2. **Stuck-Keys Guard (`release_all`):**
   - Mantém conjunto de teclas e botões pressionados e injeta `KEYUP`/`MOUSEUP` automaticamente ao encerrar a sessão ou alternar para modo `view`.
3. **Kill Switch Físico (`WH_KEYBOARD_LL`):**
   - Hook global em thread dedicada que filtra `LLKHF_INJECTED` (`0x10`) e encerra a sessão imediatamente ao detectar `Ctrl + Alt + Shift + Q` físico.

---

## 7. Protocolo `RTCDataChannel` (Schema v1 Consolidado)

| Canal | Configuração | Direção | Tipos de Mensagem (`t`) |
| :--- | :--- | :--- | :--- |
| `pointer` | `ordered: false, maxRetransmits: 0` | Bidirecional | `mm` (Client $\rightarrow$ Host), `cur` (Host $\rightarrow$ Client) |
| `control` | `ordered: true` | Bidirecional | `hello`, `mb`, `ms`, `kb`, `mode`, `ping`, `pong`, `res`, `bye`, `unattended_setup_req`, `unattended_setup_res` |

- **Rate Limit no Host:** Máximo de **200 pacotes/s** somando ambos os canais.

---

## 8. Estrutura de Diretórios Unificada do Projeto

```text
Remote Acess/
├── PRD.md                           # Product Requirements Document (v2.1)
├── TRD.md                           # Technical Requirements Document (v2.1)
├── ui-prototype.html                # Protótipo interativo de alta definição da Interface Unificada
├── .env.example                     # Variáveis de ambiente padronizadas
├── spike-marco0/                    # Benchmark do Marco 0 (mss + aiortc + SendInput DPI)
│   └── benchmark_pipeline.py
├── signaling-server/                # Servidor Central de Sinalização na Nuvem (FastAPI + WSS)
│   ├── main.py
│   ├── session_manager.py
│   ├── schemas.py
│   └── requirements.txt
├── desktop-engine/                  # Motor Local do App Unificado (Python + aiortc + mss + SendInput + PyWebView)
│   ├── main.py                      # Inicializa DPI, Motor Host, Ponte Local (127.0.0.1) e abre Janela Nativa
│   ├── host_config.py               # Persistência %APPDATA%\RemoteAccess\host_config.json e PBKDF2
│   ├── local_bridge.py              # API/WS local (127.0.0.1) para o Painel "Esta Bancada"
│   ├── host_rtc.py                  # PeerConnection aiortc + Signaling Client do Host
│   ├── screen_track.py              # Captura mss -> av.VideoFrame (yuv420p)
│   ├── input_controller.py          # Win32 SendInput + Scancode Map + Stuck-Keys Guard
│   ├── physical_guard.py            # Hooks WH_KEYBOARD_LL + WH_MOUSE_LL (Kill Switch + Anti-Auto-Clique)
│   └── requirements.txt
└── unified-ui/                      # Interface Unificada (React + TypeScript + Vite — roda no App Desktop e na Web)
    ├── package.json
    └── src/
        ├── App.tsx                  # Barra de Abas (🏠 Início + Abas de Sessão Remota)
        ├── components/
        │   ├── HomeSplitView.tsx    # Painel Duplo estilo AnyDesk ("Esta Bancada" | "Outra Bancada")
        │   ├── ThisDeskPanel.tsx    # Exibe Meu ID, PIN Temporário, Config Senha Fixa e Status Host
        │   ├── RemoteDeskPanel.tsx  # Formulário Conectar + Grade de Sessões Recentes
        │   ├── ConsentModal.tsx     # Modal "Aceitar / Recusar" e Modal de Aprovação Física de Senha Fixa
        │   ├── SessionTabView.tsx   # Player <video> WebRTC + Captura de Input
        │   └── ControlBar.tsx       # HUD Flutuante (RTT, FPS, Modo, Botão '🔑 Acesso Permanente')
        ├── services/
        │   ├── localBridge.ts       # Conexão com o motor Python local (127.0.0.1)
        │   ├── signaling.ts         # Cliente WSS para o Signaling Server
        │   └── webrtcClient.ts      # RTCPeerConnection + DataChannels (control & pointer)
        └── utils/
            └── coordinates.ts       # Matemática de Letterbox/Pillarbox e normalização 0..1
```
