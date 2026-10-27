# Implementation Plan — Ferramenta Unificada de Acesso Remoto (v2.2)

**Documentos de Referência no Repositório:**
- [PRD.md](./PRD.md) — Requisitos de Produto, Fluxos Supervisionado/Não Supervisionado e Critérios de Aceite.
- [TRD.md](./TRD.md) — Especificação Técnica, Protocolos JSON/WebRTC, Estruturas C (`SendInput`) e Hooks Win32.
- [UI_DESIGN_SYSTEM.md](./UI_DESIGN_SYSTEM.md) — Wireframe Minimalista Multi-Abas (`+`), Anatomia de Componentes e Paleta WCAG 2.
- [ui-prototype.html](./ui-prototype.html) — Protótipo Funcional de Alta Definição.

---

## Visão Geral da Estrutura do Monorepo

```text
Remote Acess/
├── PRD.md
├── TRD.md
├── UI_DESIGN_SYSTEM.md
├── IMPLEMENTATION_PLAN.md
├── ui-prototype.html
├── .env.example
├── .venv/                           # Ambiente virtual Python (compartilhado em dev)
├── spike-marco0/                    # Marco 0: Validação empírica de captura, WebRTC e SendInput
│   └── benchmark_pipeline.py
├── signaling-server/                # Marco 1: Servidor Central de Sinalização (FastAPI + WSS)
│   ├── requirements.txt
│   ├── schemas.py
│   ├── turn_credentials.py
│   ├── session_manager.py
│   ├── main.py
│   └── tests/
│       └── test_signaling.py
├── desktop-engine/                  # Marcos 1, 2, 3 e 4: Motor Local Python + Janela PyWebView
│   ├── requirements.txt
│   ├── host_config.py               # Persistência %APPDATA%\RemoteAccess\host_config.json + PBKDF2
│   ├── screen_track.py              # Captura mss -> numpy -> av.VideoFrame (yuv420p)
│   ├── scancode_map.py              # Mapa KeyboardEvent.code -> Win32 Hardware Scancode Set 1
│   ├── input_controller.py          # Win32 SendInput + Stuck-Keys Guard + Rate Limiter (200 msg/s)
│   ├── physical_guard.py            # Hooks WH_KEYBOARD_LL (Kill Switch) + WH_MOUSE_LL (Anti-Auto-Clique)
│   ├── host_rtc.py                  # PeerConnection aiortc + DataChannels + Signaling Client do Host
│   ├── local_bridge.py              # API/WS Local (127.0.0.1) autenticada por local_ipc_token
│   ├── main.py                      # Entrypoint: DPI Awareness -> Engine -> PyWebView Window
│   └── tests/
│       └── test_engine.py
└── unified-ui/                      # Marcos 2, 3 e 4: Frontend React 18 + TypeScript + Tailwind + Vite
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx                  # Gerenciador de Abas (Início + Sessões Simultâneas [ + ])
        ├── types/
        │   └── protocol.ts          # Contratos TypeScript de Sinalização, IPC Local e DataChannels v1
        ├── utils/
        │   ├── coordinates.ts       # Cálculo de Letterbox/Pillarbox (0.0000 .. 1.0000)
        │   └── wheel.ts             # Normalização de Scroll (WHEEL_DELTA = 120)
        ├── services/
        │   ├── localBridge.ts       # WebSocket Client para 127.0.0.1 (/ws/local)
        │   ├── signalingClient.ts   # WebSocket Client para o Signaling Server (/ws/client)
        │   └── webrtcSession.ts     # Classe RTCPeerConnection + Canais control & pointer + RTT Ping
        └── components/
            ├── TopTabBar.tsx        # Barra superior com Aba Início, Abas Remotas e botão [ + ]
            ├── IncomingBanner.tsx   # Banner vermelho quando este PC está sendo acessado
            ├── ThisDeskCard.tsx     # Coluna Esquerda: Seu ID, PIN Temporário e link Senha Fixa
            ├── RemoteConnectCard.tsx# Coluna Direita: Input ID + PIN/Senha + Botão Conectar + Recentes
            ├── SessionViewport.tsx  # Player <video> + Captura de Mouse/Teclado + HUD Compacto
            └── modals/
                ├── ConsentModal.tsx          # Modal "Permitir acesso remoto? [Recusar] [Aceitar]"
                ├── PasswordSetupModal.tsx    # Modal local "Configurar senha fixa"
                ├── RemoteUnattendedModal.tsx # Modal no HUD do Técnico "🔑 Criar Senha Fixa neste Host"
                └── PhysicalApprovalModal.tsx # Modal no Host "Permitir Acesso Permanente? (Clique Local)"
```

---

## Etapa 0 — Configuração de Ambiente e Execução do Marco 0 (Spike Técnico)

### Objetivo
Configurar o ambiente virtual Python, validar `SetProcessDpiAwareness(2)`, medir a precisão do `SendInput` (`<= 2px`) e confirmar que `mss` + `aiortc` mantém `30 FPS` dentro do orçamento de CPU.

### Passos na IDE
1. Criar o ambiente virtual e instalar os pacotes base:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\pip install --upgrade pip
   .\.venv\Scripts\pip install aiortc av mss numpy psutil fastapi "uvicorn[standard]" websockets pydantic pywebview pytest httpx
   ```
2. Executar o script em [spike-marco0/benchmark_pipeline.py](./spike-marco0/benchmark_pipeline.py):
   ```powershell
   .\.venv\Scripts\python spike-marco0\benchmark_pipeline.py
   ```
3. Verificar o arquivo gerado `spike-marco0/marco0_report.json`:
   - Confirmar `within_tolerance: true` na validação do `SendInput`.
   - Confirmar `effective_fps >= 28` e escolher o codec vencedor (`video/VP8` vs `video/H264`) para fixar no `.env`.

---

## Etapa 1 — Marco 1: Signaling Server & Persistência de Identidade (`Host ID` + PIN/Senha)

### 1.1. Implementar `signaling-server/`
1. **`signaling-server/schemas.py`:**
   - Definir modelos Pydantic v2 para validação estrita das mensagens:
     - `RegisterHostMsg(type="register_host", host_id: str | None, device_secret: str)`
     - `ClientAuthMsg(type="auth", host_id: str, credential: str)`
     - `VerifyCredentialMsg`, `AuthResultMsg`, `SdpSignalMsg`, `IceCandidateMsg`.
2. **`signaling-server/turn_credentials.py`:**
   - Implementar `generate_turn_credentials(shared_secret, ttl=3600)` usando `HMAC-SHA1` e retornando a lista `ice_servers` (STUN público em dev + TURN quando configurado no `.env`).
3. **`signaling-server/session_manager.py`:**
   - Gerenciar dicionário `rooms: dict[str, SessionRoom]`.
   - Validar `device_secret` com `hashlib.sha256` e `hmac.compare_digest` para garantir que cada computador mantenha seu `host_id` fixo de 9 dígitos.
   - Implementar rate limit por IP (`max 5 falhas/minuto`) e lockout de 5 minutos para proteção contra força bruta.
   - Garantir que qualquer erro (Host offline, PIN expirado ou Senha errada) retorne exatamente `{ "type": "auth_error", "code": "INVALID_CREDENTIALS_OR_UNAVAILABLE" }`.
4. **`signaling-server/main.py`:**
   - Endpoints WebSocket `/ws/host` e `/ws/client`.
   - Suporte a múltiplas sessões de saída por Client, mantendo bloqueio estrito 1:1 de entrada por Host.

### 1.2. Implementar `desktop-engine/host_config.py`
1. Criar/ler `%APPDATA%\RemoteAccess\host_config.json`.
2. Na primeira execução, sortear `host_id` (9 dígitos) e `device_secret` (`secrets.token_hex(32)`).
3. Implementar geração de **PIN Temporário** em memória (`6 dígitos`, `TTL = 300s`, uso único, regenerado após uso ou na 5ª falha).
4. Implementar `set_unattended_password(password: str)` salvando `unattended_salt` (16 bytes) e `unattended_password_hash` (`PBKDF2-HMAC-SHA256`, `200.000` iterações).
5. Implementar `verify_incoming_credential(credential: str) -> Literal["unattended", "supervised_pin", "invalid"]` executando ambas as comparações em **tempo constante** para evitar *timing attacks*.

### Critério de Verificação da Etapa 1
- Rodar `.\.venv\Scripts\pytest signaling-server/tests` validando registro de Host ID fixo, rejeição na 6ª tentativa errada e distinção correta entre PIN Temporário e Senha Fixa.

---

## Etapa 2 — Marco 2: Pipeline de Vídeo (`mss` + `aiortc`), Ponte Local e UI Multi-Abas

### 2.1. Implementar `desktop-engine/screen_track.py` e `host_rtc.py`
1. **`screen_track.py`:**
   - Subclasse `ScreenStreamTrack(VideoStreamTrack)` capturando `sct.monitors[1]`.
   - Aplicar *downscale* se `width > 1920` ou `height > 1080` e truncar para dimensões pares (`width & ~1`, `height & ~1`).
   - Converter `BGRA -> BGR -> av.VideoFrame(yuv420p)` com clock de `90 kHz` e pacing de `30 FPS`.
2. **`host_rtc.py`:**
   - Conectar ao `/ws/host` com reconexão automática (*exponential backoff*).
   - Ao receber `SDP Offer` de uma sessão autorizada, anexar `ScreenStreamTrack`, registrar handlers para os canais `control` e `pointer` e enviar `{ "v": 1, "t": "res", "w": out_w, "h": out_h }`.
3. **`local_bridge.py`:**
   - Servidor FastAPI local ouvindo exclusivamente em `127.0.0.1:{porta_dinamica}` com validação de `local_ipc_token`.
   - Enviar estado em tempo real (`host_id`, `temp_pin`, `pin_expires_in_sec`, `unattended_enabled`, `incoming_session`) para o painel esquerdo da UI.

### 2.2. Criar `unified-ui/` (React + TypeScript + Tailwind)
1. Inicializar projeto Vite em `unified-ui/`:
   ```powershell
   npm create vite@latest unified-ui -- --template react-ts
   ```
2. Configurar as variáveis CSS no `src/index.css` exatamente com a paleta auditada WCAG 2 do [UI_DESIGN_SYSTEM.md](./UI_DESIGN_SYSTEM.md).
3. Implementar os componentes seguindo o protótipo [ui-prototype.html](./ui-prototype.html):
   - `TopTabBar.tsx`: Aba `Início`, abas dinâmicas para cada sessão ativa e botão **`[ + ]`** ao lado das abas.
   - `ThisDeskCard.tsx`: Exibe `Seu ID` (`Copiar`), `PIN Temporário` (`Atualizar` + timer tabular) e link `Configurar senha fixa`.
   - `RemoteConnectCard.tsx`: Inputs de `ID` (máscara `XXX XXX XXX`) e `PIN ou Senha`, botão `Conectar` e grade de `Acessados recentemente` (`localStorage`).
   - `SessionViewport.tsx`: Renderiza o `<video autoPlay playsInline muted>` de cada aba conectada.

### Critério de Verificação da Etapa 2
- Abrir duas instâncias (ou aba local) e validar que a tela é transmitida a `30 FPS` e que o botão **`[ + ]`** permite abrir uma segunda aba sem derrubar a primeira.

---

## Etapa 3 — Marco 3: Controle Remoto Completo (`Win32 SendInput` + Scancodes + Letterbox)

### 3.1. Implementar Mapeamento no Client (`unified-ui/src/utils/coordinates.ts`)
1. Implementar `getNormalizedVideoCoords(event, videoElement)` calculando o retângulo útil da imagem (`object-fit: contain`) e retornando `null` se o clique ocorrer nas barras pretas (*letterbox*/*pillarbox*).
2. Implementar *throttling* de `mousemove` a `60 Hz` (`16 ms`) enviando pelo canal **`pointer`** (`ordered: false, maxRetransmits: 0`).
3. Enviar cliques (`mb`), scroll normalizado em múltiplos de `120` (`ms`) e eventos de teclado (`kb` usando `KeyboardEvent.code`) imediatamente pelo canal **`control`** (`ordered: true`).

### 3.2. Implementar `desktop-engine/scancode_map.py` e `input_controller.py`
1. **`scancode_map.py`:**
   - Mapear todos os códigos `KeyboardEvent.code` da Tabela 6.3 do [TRD.md](./TRD.md) (incluindo teclas ABNT2 `IntlBackslash`, `IntlRo` e flags `KEYEVENTF_EXTENDEDKEY`).
2. **`input_controller.py`:**
   - Configurar estruturas `INPUT`, `MOUSEINPUT` e `KEYBDINPUT` via `ctypes`.
   - Converter `(x, y)` $\in [0.0, 1.0]$ para `(dx, dy)` $\in [0, 65535]$ com `MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE`.
   - Implementar **Rate Limiter** (janela deslizante de `200 msg/s`) e verificação de modo (`control` vs `view`).
   - Implementar **Stuck-Keys Guard (`release_all()`)**: rastrear todas as teclas e botões pressionados e liberá-los automaticamente ao desconectar ou trocar para modo visualização.

### Critério de Verificação da Etapa 3
- Clicar nos 4 cantos e no centro do vídeo remoto com a janela redimensionada (com barras pretas) e escala do Windows em 125%/150%: o cursor físico do Host deve atingir exatamente o ponto clicado.
- Testar `Ctrl+C`, `Ctrl+V`, `Shift` e desconexão abrupta com tecla pressionada (confirmando liberação imediata).

---

## Etapa 4 — Marco 4: Modais de Segurança, Senha Fixa Remota (`PhysicalInputGuard`) e Kill Switch

### 4.1. Implementar `desktop-engine/physical_guard.py`
1. Criar thread dedicada com *message pump* Win32 (`GetMessageW`) instalando dois Low-Level Hooks:
   - **`WH_KEYBOARD_LL`:**
     - Ignora qualquer evento com `LLKHF_INJECTED` (`0x10`).
     - Detecta a combinação física **`Ctrl + Alt + Shift + Q`** e aciona o encerramento imediato da sessão recebida + `input_controller.release_all()`.
   - **`WH_MOUSE_LL`:**
     - Verifica a flag `LLMHF_INJECTED` (`0x01`).
     - Registra `last_physical_click_ts` (quando `LLMHF_INJECTED == 0`) e `last_injected_click_ts` (quando `LLMHF_INJECTED != 0`).
2. Implementar `is_recent_physical_click() -> bool`:
   - Retorna `True` somente se houve clique físico real nos últimos `800 ms` e posterior a qualquer clique injetado.

### 4.2. Implementar Provisionamento Remoto de Senha Fixa (`RF-H08`)
1. No HUD da sessão (`SessionViewport.tsx`), ao clicar em **`🔑 Criar Senha Fixa`**, abrir `<RemoteUnattendedModal />` e enviar `{ "v": 1, "t": "unattended_setup_req", "new_password": "..." }` pelo canal `control`.
2. Ao receber `unattended_setup_req` no Host:
   - Trazer a janela do aplicativo no Host para a frente (`SetForegroundWindow`) e exibir `<PhysicalApprovalModal />` (*"Permitir Acesso Permanente?"*).
   - Quando o botão **`Permitir (Clique Local)`** for acionado na UI do Host, o `local_bridge.py` valida `physical_guard.is_recent_physical_click()`.
   - Se o clique veio do `SendInput` remoto, bloqueia a ação; se veio do mouse físico local, grava o novo hash `PBKDF2` no `host_config.json` e retorna `{ "v": 1, "t": "unattended_setup_res", "status": "approved" }` para o técnico.

### 4.3. Empacotamento da Janela Nativa (`desktop-engine/main.py`)
1. Chamar `init_dpi_awareness()` na primeira linha do script.
2. Iniciar `local_bridge` + `host_rtc` + `physical_guard` em background.
3. Abrir a janela nativa `webview.create_window("RemoteAccess", url=..., width=960, height=640, min_size=(800, 540))`.

---

## Checklist Final de Aceite (Definition of Done)

- [x] **Marco 0:** Benchmark executado confirmando pipeline de codificação WebRTC e precisão do `SendInput` com erro de `0px` (`within_tolerance: true`).
- [x] **Marco 1:** `Host ID` de 9 dígitos persiste ao reiniciar; PIN expira em 5 min / uso único; rate-limit bloqueia na 6ª tentativa (`test_signaling.py` 100% aprovado).
- [x] **Marco 2:** Tela inicial minimalista fiel ao [UI_DESIGN_SYSTEM.md](./UI_DESIGN_SYSTEM.md); botão **`[ + ]`** abre múltiplas sessões simultâneas em abas (build de produção do `unified-ui` concluído com sucesso).
- [x] **Marco 3:** Coordenadas batem com precisão com `getNormalizedVideoCoords` (letterbox/pillarbox) e DPI; nenhuma tecla fica presa ao desconectar com `Stuck-Keys Guard` (`release_all()`).
- [x] **Marco 4:** Técnico consegue solicitar criação de Senha Fixa pelo HUD; Host exige clique físico real (`PhysicalInputGuard`) com `LLMHF_INJECTED` para aprovar; atalho físico `Ctrl+Alt+Shift+Q` encerra qualquer sessão.
