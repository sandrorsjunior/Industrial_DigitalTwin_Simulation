# 🏭 PROJETO: LINHA DE INSPEÇÃO E TRIAGEM AUTOMATIZADA (FACTORY I/O)

## 🎯 PROPÓSITO DO CENÁRIO INDUSTRIAL

Este projeto simula uma **estação primária de controle de qualidade e logística** comum em indústrias de embalagem ou manufatura. O objetivo principal é inspecionar automaticamente as peças de trabalho (caixas) por um critério específico (neste caso, altura/presença) e **separar as peças aprovadas das peças rejeitadas**, enquanto monitora e contabiliza o desempenho da produção.

---

## 🛠️ ELEMENTOS E COMPONENTES CHAVE

O sistema é construído sobre três pilares: Transporte, Inspeção/Atuação e Monitoramento Lógico (PLC).

### 1. Componentes Físicos (I/O)

| Tipo | Componente (Tag de I/O) | Função no Cenário |
| :--- | :--- | :--- |
| **Entrada** (Sensor) | `Sensor Central` (Diffuse Sensor) | Detecta a presença e inspeciona a altura da peça. TRUE indica peça OK. |
| **Saída** (Transporte) | `Conveyor_Motor` (Transportador) | Move as peças através da linha. |
| **Saída** (Atuador) | `Pusher` (Pistão de Rejeição) | Empurra peças que falham na inspeção para a pista lateral. |
| **Saída** (Sinalização) | `Light_Green`, `Light_Red`, `Light_Yellow` | Indica o status da linha (Operação, Rejeição/Parada, Alerta/Falta de Material). |

### 2. Elementos de Lógica (PLC)

| Elemento | Tipo | Função de Controle |
| :--- | :--- | :--- |
| **Contador** | `C_TOTAL` | Conta o número total de peças que passaram pelo sensor. |
| **Contador** | `C_APROVADAS` | Conta peças que passaram na inspeção (`Sensor Central = TRUE`). |
| **Contador** | `C_REJEITADAS` | Conta peças que falharam na inspeção (`Sensor Central = FALSE`). |
| **Temporizador** | `T_PULSE_PUSHER` (0.5s) | Controla o tempo de pulso exato para estender o pistão e rejeitar a peça. |
| **Temporizador** | `T_CYCLE_TIMEOUT` (10s) | Monitora o tempo sem detecção de peça. Dispara o alerta Amarelo se o tempo limite for excedido. |

---

## 🔄 FLUXO DE FUNCIONAMENTO E INTERAÇÃO

O processo é sequencial e baseado na leitura do **Sensor Central**.

### 1. Início e Movimento

1.  O sistema é iniciado (Geração de Peças e `Conveyor_Motor` ON).
2.  Peças geradas (`Emitter`) movem-se pelo **Transportador Principal**.

### 2. Inspeção, Contagem e Decisão (Sensor Central)

Quando a peça atinge o `Sensor Central`:

| Condição de Inspeção | Contagem (PLC) | Ação Imediata (Atuação) | Sinalização |
| :--- | :--- | :--- | :--- |
| **Peça OK** (`Sensor = TRUE`) | Incrementa `C_TOTAL` e `C_APROVADAS`. | `Pusher` permanece **OFF**. | `Light_Green` ON. |
| **Peça Ruim/Ausente** (`Sensor = FALSE`) | Incrementa `C_TOTAL` e `C_REJEITADAS`. | Ativa $T\_PULSE\_PUSHER$ (0.5s) para ligar o `Pusher`. | `Light_Red` ON. |

### 3. Triagem (Pistão de Rejeição)

* **Peça Aprovada:** Segue o fluxo principal até o Removedor Principal.
* **Peça Rejeitada:** O `Pusher` é estendido por 0.5s (controlado por $T\_PULSE\_PUSHER$), desviando a peça para a Pista de Rejeição.

### 4. Monitoramento (Timeout)

* Se o transportador estiver ligado, mas o `Sensor Central` não for ativado por mais de 10 segundos ($T\_CYCLE\_TIMEOUT$ expira), o PLC aciona a `Light_Yellow`. Isso alerta o operador sobre uma possível **falta de material** ou um **bloqueio** antes da estação de inspeção.

---

## 📊 VANTAGENS DO PROJETO

* **Automação da Qualidade:** Reduz a necessidade de inspeção manual, garantindo consistência.
* **Rastreabilidade:** Os contadores fornecem métricas em tempo real sobre a produção total, aprovação e rejeição (Taxa de Rejeição).
* **Controle Preciso:** O temporizador de pulso garante que o atuador use apenas o tempo necessário para rejeitar a peça, otimizando o ciclo e prevenindo colisões.
* **Alerta Precoce:** O temporizador de Timeout evita que a linha funcione "a seco" por muito tempo, sinalizando problemas a montante.