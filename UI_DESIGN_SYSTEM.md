# Especificação de Wireframe, UI/UX e Design System (WCAG 2.1 / 2.2)

**Projeto:** Ferramenta Unificada de Acesso Remoto de Baixa Latência  
**Versão:** 1.0  
**Data:** 26/10/2026  
**Documentos Relacionados:** [PRD.md](./PRD.md) (v2.2) | [TRD.md](./TRD.md) (v2.2) | [Protótipo HTML](./ui-prototype.html)  
**Conformidade de Acessibilidade Alvo:** **WCAG 2.1 / 2.2 Nível AA** (com **Nível AAA** nos códigos de ID, PIN e alertas de segurança)

---

## 1. Princípios de Design e Diretrizes WCAG 2

A interface do aplicativo unificado foi projetada sob o princípio de **Redução Cognitiva**: qualquer usuário (desde um cliente leigo recebendo suporte até um administrador de TI controlando múltiplos servidores) deve identificar o que fazer em menos de **3 segundos**.

### 1.1. Regras Obrigatórias da Norma WCAG 2 Aplicadas ao Projeto

| Critério WCAG 2 | Exigência Normativa | Aplicação Prática no Frontend |
| :--- | :--- | :--- |
| **1.4.3 Contrast (Minimum) — AA** | Taxa de contraste $\ge 4.5:1$ para texto normal e $\ge 3.0:1$ para texto grande ($\ge 18\text{pt}$ ou $\ge 14\text{pt}$ negrito). | Todos os textos secundários possuem contraste mínimo de **5.3:1**; os códigos de `Host ID` e `PIN` atingem **> 11:1 (AAA)**. |
| **1.4.6 Contrast (Enhanced) — AAA** | Taxa de contraste $\ge 7.0:1$ para texto normal. | Aplicado aos títulos, números de ID, inputs de formulário e alertas de segurança. |
| **1.4.11 Non-text Contrast — AA** | Taxa de contraste $\ge 3.0:1$ para bordas de campos de formulário, botões e indicadores de foco. | Inputs possuem borda em `#475569` (Dark) / `#94A3B8` (Light) garantindo visibilidade clara do campo clicável. |
| **1.4.1 Use of Color — A** | A cor nunca deve ser o único meio visual de transmitir estado ou ação. | Estados de conexão combinam **Cor + Ícone/Forma + Rótulo textual** (ex.: `● Pronto`, `⚠️ Acesso em andamento`). |
| **2.4.7 Focus Visible & 2.4.11 Focus Appearance** | Indicador de foco via teclado (`Tab`) altamente visível com anel de no mínimo `2px`. | Todos os elementos interativos utilizam `focus-visible:ring-2 focus-visible:ring-offset-2`. |
| **2.5.8 Target Size (Minimum) — AA** | Área mínima de clique de $24 \times 24\text{ CSS px}$ (recomendado $\ge 36\text{px}$ em ações críticas). | Botões primários possuem `44px` de altura; botões secundários e o botão `[ + ]` possuem no mínimo `32px x 32px`. |

---

## 2. Padrão de Cores Oficial (Paleta Auditada WCAG 2)

O sistema suporta dois temas semânticos via variáveis CSS (`Dark Mode` como padrão para reduzir fadiga visual em suporte prolongado, e `Light Mode` opcional). Todas as combinações abaixo foram calculadas pela fórmula de luminância relativa da W3C:

$$L = 0.2126 \times R + 0.7152 \times G + 0.0722 \times B, \quad \text{Contraste} = \frac{L_{\text{claro}} + 0.05}{L_{\text{escuro}} + 0.05}$$

### 2.1. Tema Escuro Padrão (*Slate High-Contrast Dark*)

| Token CSS | Cor (Hex) | Equivalente Tailwind | Função na Interface | Contraste Medido | Nível WCAG |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--bg-canvas` | `#090D16` | `bg-slate-950` | Fundo externo / Barra de abas | Base | — |
| `--bg-window` | `#0F172A` | `bg-slate-900` | Superfície principal da janela | Base | — |
| `--bg-card` | `#1E293B` | `bg-slate-800/60` | Cards ("Este Computador" / "Controlar") | Base | — |
| `--bg-input` | `#090D16` | `bg-slate-950` | Caixas de ID, PIN e Inputs | Base | — |
| `--border-subtle` | `#334155` | `border-slate-700` | Divisórias de seções e cards | `2.1:1` (decorativo) | — |
| `--border-control` | `#64748B` | `border-slate-500` | Bordas de Inputs e Botões secundários | **`3.4:1`** sobre `#0F172A` | **AA (1.4.11)** |
| `--text-primary` | `#F8FAFC` | `text-slate-50` | Títulos, `Seu ID` e valores digitados | **`17.4:1`** sobre `#0F172A` | **AAA** |
| `--text-secondary` | `#CBD5E1` | `text-slate-300` | Subtítulos, rótulos de campos e descrições | **`11.6:1`** sobre `#0F172A` | **AAA** |
| `--text-muted` | `#94A3B8` | `text-slate-400` | Cronômetro do PIN e metadados secundários | **`5.8:1`** sobre `#0F172A` | **AA** |
| `--primary-bg` | `#4F46E5` | `bg-indigo-600` | Botão principal **`Conectar`** / **`Salvar`** | **`5.6:1`** com texto `#FFFFFF` | **AA** |
| `--primary-hover` | `#4338CA` | `hover:bg-indigo-700` | Hover do botão principal | **`7.2:1`** com texto `#FFFFFF` | **AAA** |
| `--pin-highlight` | `#818CF8` | `text-indigo-400` | Destaque numérico do **PIN Temporário** | **`6.4:1`** sobre `#090D16` | **AA / AAA (Large)** |
| `--status-success` | `#34D399` | `text-emerald-400` | Indicador `● Pronto` e `● Senha fixa ativa` | **`9.8:1`** sobre `#0F172A` | **AAA** |
| `--status-warning` | `#FBBF24` | `text-amber-400` | Alertas de permissão e modo visualização | **`11.2:1`** sobre `#0F172A` | **AAA** |
| `--danger-bg` | `#DC2626` | `bg-red-600` | Botões **`Desconectar`**, **`Sair`** e Kill Switch | **`5.6:1`** com texto `#FFFFFF` | **AA** |

### 2.2. Tema Claro (*Clean Light Mode*)

| Token CSS | Cor (Hex) | Equivalente Tailwind | Função na Interface | Contraste Medido | Nível WCAG |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--bg-canvas` | `#F1F5F9` | `bg-slate-100` | Fundo externo / Barra de abas | Base | — |
| `--bg-window` | `#FFFFFF` | `bg-white` | Superfície principal da janela | Base | — |
| `--bg-card` | `#F8FAFC` | `bg-slate-50` | Cards ("Este Computador" / "Controlar") | Base | — |
| `--border-control` | `#64748B` | `border-slate-500` | Bordas de Inputs e Botões | **`4.6:1`** sobre `#FFFFFF` | **AA (1.4.11)** |
| `--text-primary` | `#0F172A` | `text-slate-900` | Títulos, `Seu ID` e valores digitados | **`17.8:1`** sobre `#FFFFFF` | **AAA** |
| `--text-secondary` | `#334155` | `text-slate-700` | Subtítulos e rótulos de campos | **`10.9:1`** sobre `#FFFFFF` | **AAA** |
| `--text-muted` | `#475569` | `text-slate-600` | Cronômetro do PIN e metadados | **`7.5:1`** sobre `#FFFFFF` | **AAA** |
| `--primary-bg` | `#4338CA` | `bg-indigo-700` | Botão principal **`Conectar`** | **`7.2:1`** com texto `#FFFFFF` | **AAA** |
| `--pin-highlight` | `#3730A3` | `text-indigo-800` | Destaque numérico do **PIN Temporário** | **`9.4:1`** sobre `#FFFFFF` | **AAA** |
| `--status-success` | `#047857` | `text-emerald-700` | Indicador `● Pronto` e `● Senha fixa ativa` | **`5.4:1`** sobre `#FFFFFF` | **AA** |
| `--danger-bg` | `#B91C1C` | `bg-red-700` | Botões **`Desconectar`** e **`Sair`** | **`6.4:1`** com texto `#FFFFFF` | **AA** |

---

## 3. Tipografia e Legibilidade de Códigos

1. **Fonte de Interface (Sans-Serif):** `Inter`, `system-ui`, `-apple-system`, `Segoe UI`, `sans-serif`.
2. **Fonte de Códigos, IDs e PINs (Monospace Tabular):** `JetBrains Mono`, `Cascadia Mono`, `Consolas`, `monospace` com `font-variant-numeric: tabular-nums`.
   - **Motivo Técnico:** Garante que os dígitos `0`, `1`, `8` tenham largura idêntica e distinção clara, e que o cronômetro regressivo (`04:52`) não faça o layout "tremer" a cada segundo.
3. **Escala Tipográfica Mínima:**
   - Nenhum texto na aplicação pode ser menor que `12px` (`0.75rem` / `text-xs`).
   - **Seu ID (`914 205 881`):** `24px` (`text-2xl`), `font-weight: 700`, `letter-spacing: 0.05em`.
   - **PIN Temporário (`739 201`):** `20px` (`text-xl`), `font-weight: 700`, `letter-spacing: 0.05em`.
   - **Inputs de Conexão (`ID` e `Senha`):** `16px` (`text-base`), `font-weight: 600`.

---

## 4. Documentação Estrutural do Wireframe (Mapa de Componentes)

### 4.1. Visão Geral do Grid e Dimensões

```text
+-----------------------------------------------------------------------------------+
| [1. BARRA DE ABAS (Header)]                                              h: 44px  |
| [ Início ]  [ ● 482 910 384 x ]  [ ● 109 442 710 x ]  [ + ]            ● Pronto   |
+-----------------------------------------------------------------------------------+
| [2. BANNER DE ALERTA DE SESSÃO RECEBIDA (Condicional)]                   h: 40px  |
| 🔴 Acesso remoto em andamento neste computador                    [Desconectar]   |
+------------------------------------+----------------------------------------------+
| [3. COLUNA ESQUERDA: 5 Colunas]    | [4. COLUNA DIREITA: 7 Colunas]               |
|                                    |                                              |
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
|  | 739 201          [Atualizar] |  |  [5. ACESSADOS RECENTEMENTE (Grid 2 Cols)]   |
|  +------------------------------+  |  +--------------------+ +------------------+ |
|                                    |  | Servidor Loja    → | | PC Financeiro  → | |
|  --------------------------------  |  | 482 910 384        | | 109 442 710      | |
|  ● Senha fixa ativa   [Configurar] |  +--------------------+ +------------------+ |
+------------------------------------+----------------------------------------------+
```

- **Container da Tela Inicial (`<HomeSplitView />`):**
  - Largura máxima: `max-w-4xl` (`896px`) centralizado, padding interno de `32px` (`p-8`), espaçamento entre colunas de `32px` (`gap-8`).
  - Proporção responsiva: `grid-cols-1` em telas estreitas (`< 768px`) e `grid-cols-12` em desktop (`5 colunas` para Host + `7 colunas` para Client).

---

### 4.2. Especificação Componente a Componente

#### Componente 1 — Barra Superior de Abas (`<TopTabBar />`)
- **Elementos:**
  1. **Aba Fixa `Início`:** Nunca possui botão de fechar (`✕`).
  2. **Abas de Sessão (`[ ● 482 910 384 ✕ ]`):** Uma aba para cada conexão WebRTC ativa. Exibe ponto verde (`#34D399`) quando conectada, amarelo (`#FBBF24`) quando reconectando, e botão `✕` para encerrar aquela sessão específica.
  3. **Botão `[ + ]` (Nova Conexão):** Botão quadrado (`28px x 28px`, `aria-label="Abrir nova conexão remota"`). Ao ser clicado enquanto o usuário está em uma aba remota, alterna a visualização para a aba `Início` e posiciona o foco automaticamente no input `ID do computador remoto`, mantendo todas as sessões abertas rodando em segundo plano.
  4. **Indicador de Status do Sinalizador (`● Pronto`):** Alinhado à direita, confirma que o WebSocket com o servidor de sinalização está conectado.
- **Acessibilidade (WAI-ARIA):** `role="tablist"`, cada aba com `role="tab"` e `aria-selected="true|false"`.

#### Componente 2 — Banner de Sessão Recebida (`<IncomingSessionBanner />`)
- **Regra de Exibição:** Oculto por padrão. Aparece imediatamente abaixo do cabeçalho sempre que este computador estiver sendo acessado por um operador remoto (seja via PIN Temporário ou via Senha Fixa).
- **Elementos:** Indicador pulsante vermelho + texto `"Acesso remoto em andamento neste computador"` + Botão **`Desconectar`** (`#DC2626`).
- **Acessibilidade:** `role="status"` e `aria-live="polite"`.

#### Componente 3 — Coluna Esquerda: Card "Este Computador" (`<ThisDeskCard />`)
- **Bloco "Seu ID":**
  - Exibe o `Host ID` persistente de 9 dígitos formatado com espaços a cada 3 dígitos (`914 205 881`).
  - Botão **`Copiar`**: Copia os 9 dígitos para o clipboard e altera o texto para `"Copiado!"` por `1.5s` (`aria-live="polite"`).
- **Bloco "PIN Temporário":**
  - Exibe o PIN descartável de 6 dígitos (`739 201`) e o cronômetro regressivo (`04:52`).
  - Botão **`Atualizar`**: Solicita ao motor local (`action_rotate_pin`) a geração imediata de um novo PIN de 6 dígitos e reinicia o contador para `05:00`.
- **Rodapé de Senha Fixa:**
  - Status à esquerda: `● Senha fixa ativa` (verde) ou `○ Senha fixa desativada` (cinza).
  - Ação à direita: Botão de texto **`Configurar senha fixa`**, que abre o `<PasswordSetupModal />`.

#### Componente 4 — Coluna Direita: Card "Controlar Outro Computador" (`<RemoteConnectCard />`)
- **Campo 1 — ID Remoto:**
  - `input[type="text"]`, `inputMode="numeric"`, `maxLength={11}`, máscara automática `XXX XXX XXX`.
  - Validação visual: borda vermelha caso tenha menos de 9 dígitos numéricos ao submeter.
- **Campo 2 — PIN ou Senha:**
  - `input[type="password"]` com opção de revelar caracteres, aceitando tanto PIN de 6 dígitos quanto Senha Fixa de 8+ caracteres.
- **Botão Principal `Conectar`:**
  - Ocupa `100%` da largura do card (`w-full py-3`), fundo `--primary-bg`, desabilitado durante o estado `"Conectando..."`.

#### Componente 5 — Grade "Acessados Recentemente" (`<RecentSessionsGrid />`)
- Exibe os últimos computadores conectados com sucesso (armazenados em `localStorage`, contendo apenas `{ id, label, lastConnectedAt }`).
- Cada card é um `<button>` ocupando `100%` da coluna da grade, permitindo navegação por `Tab` e acionamento com `Enter` ou `Espaço`.

#### Componente 6 — Aba de Sessão Remota e HUD (`<SessionViewport />` + `<FloatingHud />`)
- **Barra Flutuante Compacta (`<FloatingHud />`):**
  - Centralizada no topo do vídeo (`max-w-3xl`), contendo:
    1. Identificação: `● 482 910 384 (Servidor Loja) • 12 ms`
    2. Botão **`🔑 Criar Senha Fixa`**: Abre o modal para o técnico cadastrar uma senha permanente naquele Host remoto.
    3. Botão de Modo: Alterna entre **`Controle Ativo`** e **`Apenas Visualização`**.
    4. Botão **`Sair`** (`#DC2626`): Encerra a conexão WebRTC daquela aba e fecha a aba.
- **Área de Vídeo (`<video>`):**
  - Mantém proporção original da tela remota (`aspect-video` / `object-fit: contain`) sobre fundo `#000000`.

---

## 5. Especificação dos Modais e Fluxos de Confirmação

Todos os modais devem implementar `role="dialog"`, `aria-modal="true"`, **Focus Trap** (o `Tab` circula apenas dentro do modal aberto) e fundo escurecido (`bg-black/70 backdrop-blur-sm`).

| Modal | Quem Visualiza | Gatilho | Botões de Ação | Regra Especial de Segurança |
| :--- | :--- | :--- | :--- | :--- |
| **`<ConsentModal />`** ("Permitir acesso remoto?") | Usuário do Host | Operador remoto conectou usando o PIN Temporário de 6 dígitos | `[ Recusar ]` / `[ Aceitar ]` | Timeout automático de 30s (recusa se ninguém clicar); foco inicial no botão `Recusar` para evitar aprovação acidental ao digitar `Enter`. |
| **`<PasswordSetupModal />`** ("Senha de Acesso Fixo") | Usuário do Host | Clique em `Configurar senha fixa` no card "Este Computador" | `[ Cancelar ]` / `[ Salvar ]` | Exige mínimo de 8 caracteres; bloqueia salvamento se o clique vier de input injetado durante sessão ativa. |
| **`<RemoteUnattendedModal />`** ("Criar Senha Fixa neste Host") | Operador Remoto | Clique em `🔑 Criar Senha Fixa` no HUD da sessão ativa | `[ Cancelar ]` / `[ Solicitar ]` | Envia pacote `unattended_setup_req` pelo `RTCDataChannel` (`control`). |
| **`<PhysicalApprovalModal />`** ("Permitir Acesso Permanente?") | Usuário do Host | Recebimento de `unattended_setup_req` em sessão iniciada por PIN | `[ Negar ]` / `[ Permitir (Clique Local) ]` | **Trava `PhysicalInputGuard`:** O botão `Permitir` rejeita cliques com flag `LLMHF_INJECTED` (auto-clique remoto via `SendInput`). |
