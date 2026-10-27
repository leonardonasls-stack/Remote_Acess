# PRD — Product Requirements Document (Ferramenta Unificada de Acesso Remoto)

**Versão:** 2.2 (Interface Minimalista + Múltiplas Abas de Acesso com Botão `+` + Provisionamento Remoto de Senha Fixa)  
**Data:** 26/10/2026  
**Documento Técnico Pareado:** [TRD.md](./TRD.md) (v2.2)  
**Status:** Aprovado para Execução  
**Contexto do Produto:** Piloto com usuários externos / clientes reais (Aplicativo Unificado Desktop + Web Client Zero-Install, WSS, TURN e LGPD)

---

## 1. Visão do Produto, Problema e Objetivos

### 1.1. Visão
Construir uma ferramenta moderna de acesso e controle remoto de baixa latência **unificada e minimalista ao estilo AnyDesk**: um **único aplicativo** instalado no computador permite simultaneamente **receber suporte remoto (atuar como Host)** e **acessar/controlar múltiplos computadores (atuar como Client em múltiplas abas)**, mantendo também uma **interface Web Zero-Install** para acesso direto pelo navegador.

### 1.2. Problema e Público-Alvo
- **Problema:** Separar o software em dois programas distintos ("Host para o cliente" e "Client para o técnico") ou poluir a tela com jargões técnicos gera atrito operacional. Usuários precisam de uma tela inicial limpa (apenas **Seu ID + PIN** de um lado e **Conectar** do outro), suporte a **múltiplas abas (`+`)** para técnicos que atendem mais de um computador ao mesmo tempo, e opção de o próprio técnico configurar a **Senha Fixa (Acesso Não Supervisionado)** mediante confirmação física do cliente.
- **Persona 1 — Técnico / Administrador (Client Desktop ou Web):** Abre várias sessões remotas simultâneas pelo botão `[ + ]` na barra de abas e pode solicitar pelo HUD o cadastro de uma **Senha Fixa** na máquina remota.
- **Persona 2 — Usuário do Host (Cliente Supervisionado):** Visualiza seu ID e PIN em uma interface limpa, aprova a entrada do técnico clicando em **"Aceitar"** e, se solicitado, autoriza fisicamente o Acesso Permanente.
- **Persona 3 — Máquina / Servidor Não Supervisionado (Unattended Host):** Computador com **ID Fixo** e **Senha Fixa** já ativa, permitindo conexão direta sem interação humana local.

### 1.3. Não-Metas do MVP
Áudio remoto, sincronização automática de área de transferência (clipboard), transferência de arquivos, seleção de múltiplos monitores, suporte nativo do agente Host em Linux/macOS, gravação de sessão e execução como Serviço Windows `SYSTEM` (telas de UAC e login do Windows ficam para a v2). *(Nota: Um único Client pode controlar múltiplos Hosts em abas separadas `[ + ]`, mas cada Host aceita apenas 1 operador ativo por vez — 1:1 no Host).*

### 1.4. Indicadores de Sucesso (KPIs de Produto e Performance)

| Métrica | Meta do MVP (Validada no Marco 0) | Meta v2 |
| :--- | :--- | :--- |
| **Latência ponta a ponta (LAN / P2P direto)** | `< 80 ms` (média) / `< 110 ms` (p95) | `< 45 ms` |
| **Latência ponta a ponta (WAN com TURN relay)** | `< 150 ms` (em região nacional, RTT < 40 ms) | `< 90 ms` |
| **Taxa de quadros (FPS)** | `30 FPS` estável em 720p/1080p | `60 FPS` adaptativo |
| **Tempo de handshake P2P** | `< 3 s` (após autorização da sessão) | `< 1,5 s` |
| **Uso de CPU no modo Host (1080p@30)** | Máx. `40%` de 1 núcleo lógico (`~10–15%` CPU total em Quad-Core) | `< 8%` CPU total |
| **Experiência do App Desktop** | Programa único minimalista com múltiplas abas (`+`) | Instalador `.exe` assinado + System Tray |

---

## 2. Experiência Unificada Minimalista (Wireframe Oficial v2.2)

### 2.1. Wireframe da Tela Inicial (Painel Duplo Enxuto + Barra de Abas com `+`)

```text
+-----------------------------------------------------------------------------------+
| [ Início ]  [ ● 482 910 384 x ]  [ ● 109 442 710 x ]  [ + ]            ● Pronto   |
+------------------------------------+----------------------------------------------+
|  ESTE COMPUTADOR                   |  CONTROLAR OUTRO COMPUTADOR                  |
|  Passe estes dados para quem       |  Digite o ID e o PIN (ou senha fixa)         |
|  for acessar você                  |  do computador remoto                        |
|                                    |                                              |
|  Seu ID                            |  +-----------------------+ +---------------+ |
|  +------------------------------+  |  | 482 910 384           | | ••••••        | |
|  | 914 205 881         [Copiar] |  |  +-----------------------+ +---------------+ |
|  +------------------------------+  |  +-----------------------------------------+ |
|                                    |  |                Conectar                 | |
|  PIN Temporário           04:52    |  +-----------------------------------------+ |
|  +------------------------------+  |                                              |
|  | 739 201          [Atualizar] |  |  Acessados recentemente                      |
|  +------------------------------+  |  +--------------------+ +------------------+ |
|                                    |  | Servidor Loja    → | | PC Financeiro  → | |
|  --------------------------------  |  | 482 910 384        | | 109 442 710      | |
|  ● Senha fixa ativa   [Configurar] |  +--------------------+ +------------------+ |
+------------------------------------+----------------------------------------------+
```

### 2.2. Wireframe da Aba de Sessão Remota (HUD Enxuto)

```text
+-----------------------------------------------------------------------------------+
| [ Início ]  [ ● 482 910 384 x ]  [ + ]                                 ● Pronto   |
+-----------------------------------------------------------------------------------+
|       +-------------------------------------------------------------------+       |
|       | ● 482 910 384 (Servidor Loja) • 12 ms   [🔑 Criar Senha Fixa] [Sair] |     |
|       +-------------------------------------------------------------------+       |
|   +---------------------------------------------------------------------------+   |
|   |                                                                           |   |
|   |                     ÁREA DE TRABALHO REMOTA (16:9)                        |   |
|   |                                                                           |   |
|   +---------------------------------------------------------------------------+   |
+-----------------------------------------------------------------------------------+
```

1. **Múltiplos Acessos Simultâneos (`[ + ]` na Barra de Abas):**
   - O operador pode abrir várias sessões remotas ao mesmo tempo clicando no botão **`[ + ]`** ao lado das abas (que leva ao painel de conexão para abrir uma nova aba sem fechar as sessões já conectadas).
   - Ao alternar entre abas, as sessões em segundo plano permanecem conectadas, enquanto os eventos de teclado/mouse são enviados apenas para a aba atualmente visível/ativa.
2. **Fluxo de Criar Senha Fixa pelo Operador Remoto (`🔑 Criar Senha Fixa`):**
   - Na barra flutuante (HUD) da sessão ativa, o técnico clica em **`🔑 Criar Senha Fixa`** e digita a senha permanente para aquele Host.
   - No computador do cliente salta o modal **"Permitir Acesso Permanente?"**, cujo botão **`[ Permitir ]`** aceita exclusivamente o clique físico do mouse do cliente (bloqueando auto-clique remoto via `PhysicalInputGuard`).

---

## 3. Requisitos Funcionais e Critérios de Aceite (Escopo do MVP)

### 3.1. Módulo 1 — Agente Local & Motor Host (Python)

- **RF-H01 — Identidade Persistente (`Host ID`) e Credenciais Duplas (PIN + Senha Fixa):**
  - Mantém o mesmo `Host ID` de 9 dígitos entre reinicializações (`%APPDATA%\RemoteAccess\host_config.json`).
  - Gera **PIN Temporário** de 6 dígitos (`secrets`, TTL 5 minutos, uso único, regenerado após uso ou após 5 falhas).
  - Permite configurar/ativar/desativar **Senha Fixa** (mínimo 8 caracteres, armazenada como hash `PBKDF2-HMAC-SHA256`).
- **RF-H02 — Captura de Tela Otimizada:** Captura do monitor primário a `30 FPS` com `mss`, redimensionando automaticamente se > 1080p mantendo a proporção.
- **RF-H03 — Estabelecimento de Sessão WebRTC:** Negocia a conexão P2P/TURN, abre os canais de dados (`control` e `pointer`) e transmite o vídeo da tela em `< 3 s`.
- **RF-H04 — Simulação Fiel de Mouse e Teclado (`Win32 SendInput`):** Movimento absoluto preciso em qualquer escala de DPI, cliques, *drag-and-drop*, scroll, teclado por scancodes (ABNT2/US) e liberação automática de teclas presas (*Stuck-Keys Guard*).
- **RF-H05 — Consentimento Integrado, Banner de Sessão Recebida e Kill Switch:**
  - Quando recebe pedido via PIN Temporário, traz a janela do aplicativo para o topo com o modal **"Permitir acesso remoto? [Recusar] [Aceitar]"** (timeout 30s).
  - Exibe banner vermelho discreto no topo enquanto houver acesso ativo com botão **"Desconectar"** e atalho físico global **`Ctrl+Alt+Shift+Q`**.
- **RF-H06 — Proteção contra Sobrecarga e Comandos Inválidos:** Valida o schema de cada comando, limita a taxa a **200 mensagens/segundo** e bloqueia injeção de comandos no modo `Apenas Visualização`.
- **RF-H07 — Ponte Local (`Local Control API`) e Reconexão:** Sincroniza estado em tempo real com a UI unificada via `127.0.0.1` e reconecta automaticamente ao Signaling Server.
- **RF-H08 — Provisionamento Remoto Seguro de Senha Fixa (Anti-Auto-Clique):**
  - Quando o operador remoto solicita cadastrar uma Senha Fixa pelo HUD (`unattended_setup_req`) durante uma sessão iniciada por PIN, exibe modal local cujo botão **"Permitir"** rejeita cliques injetados remotamente (`LLMHF_INJECTED`).

### 3.2. Módulo 2 — Signaling Server (FastAPI + WebSockets)

- **RF-S01 — Registro Persistente de Peers:** Valida `host_id` + `device_secret` dos aplicativos online.
- **RF-S02 — Autenticação Híbrida e Anti-Brute-Force:** Coordena a verificação de PIN Temporário ou Senha Fixa com rate limit por IP e por `host_id` (máx. 5 falhas/minuto e *lockout* de 5 minutos), retornando mensagem de erro idêntica.
- **RF-S03 — Pareamento 1:1 por Host e Múltiplas Sessões por Client:** Cada Host aceita apenas 1 operador por vez, mas um mesmo operador (Client) pode abrir múltiplas conexões simultâneas para diferentes `host_id`s em abas independentes.
- **RF-S04 — Independência da Sessão P2P:** Oscilações no WebSocket após a conexão WebRTC ativa não derrubam a sessão P2P.
- **RF-S05 — Segurança de Transporte e TURN:** Opera sobre `WSS` em produção, restringe origens (`Origin` allowlist), valida payloads e emite credenciais TURN temporárias.

### 3.3. Módulo 3 — Interface Unificada Minimalista (React + TypeScript)

- **RF-C01 — Tela Inicial Minimalista + Barra de Abas com Botão `+`:**
  - **Barra de Abas:** Aba fixa `Início`, abas dinâmicas para cada computador remoto conectado e botão **`[ + ]`** ao lado das abas para iniciar uma nova conexão sem encerrar as atuais.
  - **Lado Esquerdo ("Este Computador"):** Exibe apenas `Seu ID` (`Copiar`), `PIN Temporário` (`Atualizar` + timer) e link discreto `Configurar senha fixa` (que abre modal).
  - **Lado Direito ("Controlar Outro Computador"):** Campos diretos de `ID` e `PIN ou Senha`, botão `Conectar` e lista limpa de `Acessados recentemente`.
- **RF-C02 — Múltiplos Viewports Remotos Independentes:** Cada aba mantém sua própria instância de `RTCPeerConnection` e `<video>`, encaminhando eventos de mouse/teclado apenas da aba ativa em foco.
- **RF-C03 — Precisão de Clique e Atalhos:** Mapeia cliques sobre a imagem útil do vídeo (descartando barras pretas), bloqueia menu de contexto e suporta *Keyboard Lock* em Tela Cheia.
- **RF-C04 — HUD Compacto na Sessão:** Exibe ID conectado, latência (`ms`), botão **`🔑 Criar Senha Fixa`**, alternância **`Controle Ativo / Apenas Visualização`** e botão **`Sair`**.
- **RF-C05 — Reconexão Automática:** Tenta restabelecer o fluxo WebRTC por até `30 segundos` em caso de queda de rede.

---

## 4. Segurança, Privacidade e Conformidade LGPD

1. **Zero-Knowledge para Senha Fixa:** A Senha Fixa nunca é armazenada no Signaling Server; o pedido remoto trafega diretamente pelo túnel P2P criptografado (`RTCDataChannel` DTLS) e apenas o hash `PBKDF2` é salvo em disco no Host.
2. **Proteção Física Contra Auto-Aprovação (`PhysicalInputGuard`):** Cliques injetados remotamente (`SendInput`) não conseguem aprovar modais de segurança nem alterar senhas locais do Host.
3. **Soberania do Usuário do Host:** Consentimento obrigatório para PIN temporário, banner ativo em 100% das sessões e *Kill Switch* físico local (`Ctrl+Alt+Shift+Q`).
4. **Privacidade e LGPD:** Zero gravação de imagem/teclado e retenção máxima de **30 dias** para logs técnicos de conexão no Signaling Server.

---

---

## 5. Estrutura do Monorepo e Separação de Responsabilidades

O projeto está organizado em um Monorepo com separação clara e isolada entre as camadas de **Backend** e **Frontend**:

```text
Remote Acess/
├── backend/
│   ├── signaling-server/         # Módulo 2: Servidor Central de Sinalização (FastAPI + WSS + STUN/TURN)
│   │   ├── main.py               # Endpoints WebSocket /ws/host e /ws/client (bloqueio 1:1 e roteamento)
│   │   ├── session_manager.py    # Gerenciamento de sessões, salas e rate limiter anti-força-bruta
│   │   ├── schemas.py            # Contratos de dados Pydantic v2 para validação estrita
│   │   ├── turn_credentials.py   # Emissão de credenciais efêmeras coturn via HMAC-SHA1
│   │   ├── requirements.txt
│   │   └── tests/
│   │       └── test_signaling.py # Testes de handshake, persistência de ID e rate limit
│   └── desktop-engine/           # Módulo 1: Motor Local do Agente Host em Python
│       ├── main.py               # Entrypoint: Per-Monitor DPI Awareness + Local Bridge + PyWebView
│       ├── host_config.py        # Identidade fixa (%APPDATA%), PIN de uso único e hash PBKDF2
│       ├── host_rtc.py           # Conexão P2P WebRTC (aiortc) e handlers dos DataChannels
│       ├── screen_track.py       # Captura de tela otimizada mss + cv2 resize (YUV420p) a 30 FPS
│       ├── input_controller.py   # Injeção Win32 SendInput com Stuck-Keys Guard (release_all)
│       ├── physical_guard.py     # Hooks Win32 WH_MOUSE_LL e WH_KEYBOARD_LL (Anti-Auto-Clique + Kill Switch)
│       ├── scancode_map.py       # Mapeamento W3C para Hardware Scancode Set 1 (ABNT2 e US)
│       ├── local_bridge.py       # Servidor IPC local seguro em 127.0.0.1:8765
│       ├── requirements.txt
│       └── tests/
│           └── test_engine.py    # Testes unitários de injeção, scancodes e guarda físico
│
├── frontend/
│   ├── unified-ui/               # Módulo 3: Aplicação Web e Desktop em React 19 + TypeScript + Vite + Tailwind CSS
│   │   ├── src/
│   │   │   ├── App.tsx           # Gerenciador de abas simultâneas e tela inicial (Split View)
│   │   │   ├── components/       # TopTabBar, ThisDeskCard, RemoteConnectCard, SessionViewport e modais
│   │   │   ├── types/protocol.ts # Contratos TypeScript do protocolo de dados e DataChannels
│   │   │   └── utils/            # Cálculo de coordenadas, letterbox/pillarbox e normalização de mouse
│   │   ├── package.json
│   │   └── vite.config.ts
│   └── ui-prototype.html         # Protótipo funcional de alta definição de referência estética WCAG 2
│
├── spike-marco0/                 # Spike Técnico de Risco (validação empírica de FPS, latência e SendInput)
│   ├── benchmark_pipeline.py
│   └── marco0_report.json
├── PRD.md
├── TRD.md
├── UI_DESIGN_SYSTEM.md
└── IMPLEMENTATION_PLAN.md
```

---

## 6. Roadmap de Entrega

- **Marco 0 — Spike Técnico de Risco:** Validar performance de captura (`mss` + `cv2`) + codificação (`aiortc`) em 1080p@30fps e injeção Win32 `SendInput` com DPI Awareness (Concluído: `within_tolerance: true`, erro `0px`).
- **Marco 1 — Backend Signaling Server, Identidade Fixa e Motor Unificado:** Servidor FastAPI (`backend/signaling-server`), persistência de `Host ID` + PIN/Senha Fixa (`backend/desktop-engine/host_config.py`) e API local do agente unificado.
- **Marco 2 — Frontend Unificado Minimalista (Multi-Abas `+`) + Streaming de Vídeo:** Dashboard enxuto em `frontend/unified-ui`, suporte a múltiplas abas simultâneas de sessão remota e streaming de tela a 30 FPS.
- **Marco 3 — Controle Remoto Completo (`Win32 SendInput`):** Mouse, teclado por scancode, cursor remoto, suporte a DPI/letterbox e liberação automática de teclas presas (`Stuck-Keys Guard`).
- **Marco 4 — Provisionamento Remoto de Senha, Consentimento Físico, Kill Switch e Resiliência:** Fluxo de criar Senha Fixa pelo HUD com trava anti-auto-clique no Host (`backend/desktop-engine/physical_guard.py`), atalho `Ctrl+Alt+Shift+Q` e reconexão automática.
