# 🏭 PROJETO: LINHA DE INSPEÇÃO E TRIAGEM AUTOMATIZADA (FACTORY I/O)

## 🎯 PROPÓSITO DO CENÁRIO INDUSTRIAL

Este projeto simula uma **estação primária de controle de qualidade e logística** comum em indústrias de embalagem ou manufatura. O objetivo principal é inspecionar automaticamente as peças de trabalho (caixas) por um critério específico (neste caso, altura/presença) e **separar as peças aprovadas das peças rejeitadas**, enquanto monitora e contabiliza o desempenho da produção.

---

## 🛠️ ELEMENTOS E COMPONENTES CHAVE

O sistema é construído sobre três pilares: Transporte, Inspeção/Atuação e Monitoramento Lógico (PLC).

### 1. Componentes Físicos (I/O)

| Tipo | Componente (Tag de I/O) | Função no Cenário |
| :--- | :--- | :--- |
| **Entrada (Sensor)** | **`Diffuse Sensor 0`** | Detecta a presença e inspeciona a altura da peça. TRUE indica peça OK. |
| **Entrada (Sensor)** | **`Pusher 0 (Back Limit)`** | Confirma que o pistão de rejeição está totalmente retraído (posição inicial). |
| **Entrada (Sensor)** | **`Pusher 0 (Front Limit)`** | Confirma que o pistão de rejeição está totalmente estendido (rejeitando a peça). |
| **Entrada (Controle)** | **`Start Button 0`**, **`Stop Button 0`**, **`Reset Button 0`** | Comandos manuais de operação e reinício da lógica de controle. |
| **Saída (Transporte)** | **`Belt Conveyor (6m) 0`** | Aciona o motor e move as peças através da linha. |
| **Saída (Atuador)** | **`Pusher 0`** | Atua como o Pistão de Rejeição. Empurra peças que falham na inspeção para a pista lateral. |
| **Saída (Sinalização)** | **`Stack Light 0 (Green)`**, **`(Red)`**, **`(Yellow)`** | Indica o status da linha (Operação, Rejeição/Parada, Alerta/Falta de Material). |

### 2. Elementos de Lógica (PLC)

| Elemento | Tipo | Função de Controle |
| :--- | :--- | :--- |
| **Contador** | `C_TOTAL` | Conta o número total de peças que passaram pelo sensor. |
| **Contador** | `C_APROVADAS` | Conta peças que passaram na inspeção (`Diffuse Sensor 0 = TRUE`). |
| **Contador** | `C_REJEITADAS` | Conta peças que falharam na inspeção (`Diffuse Sensor 0 = FALSE`). |
| **Temporizador** | `T_PULSE_PUSHER` (0.5s) | Controla o tempo de pulso exato para estender o pistão (`Pusher 0`) e rejeitar a peça. |
| **Temporizador** | `T_CYCLE_TIMEOUT` (10s) | Monitora o tempo sem detecção de peça no sensor. Dispara o alerta Amarelo se o tempo limite for excedido. |

---

## 🔄 FLUXO DE FUNCIONAMENTO E INTERAÇÃO

O processo é sequencial e baseado na leitura do **`Diffuse Sensor 0`**.

### 1. Início e Movimento

1.  O sistema é iniciado (**`Start Button 0`** acionado) (Geração de Peças via **`Emitter 0`** e **`Belt Conveyor (6m) 0`** ON).
2.  Peças geradas (`Emitter 0`) movem-se pelo **Transportador Principal**.

### 2. Inspeção, Contagem e Decisão (Diffuse Sensor 0)

Quando a peça atinge o **`Diffuse Sensor 0`**:

| Condição de Inspeção | Contagem (PLC) | Ação Imediata (Atuação) | Sinalização |
| :--- | :--- | :--- | :--- |
| **Peça OK** (`Sensor = TRUE`) | Incrementa `C_TOTAL` e `C_APROVADAS`. | **`Pusher 0`** permanece **OFF**. | **`Stack Light 0 (Green)`** ON. |
| **Peça Ruim/Ausente** (`Sensor = FALSE`) | Incrementa `C_TOTAL` e `C_REJEITADAS`. | Ativa $T\_PULSE\_PUSHER$ (0.5s) para ligar o **`Pusher 0`**. | **`Stack Light 0 (Red)`** ON. |

### 3. Triagem (Pistão de Rejeição)

* **Peça Aprovada:** Segue o fluxo principal até o Removedor Principal.
* **Peça Rejeitada:** O **`Pusher 0`** é estendido por 0.5s (controlado por $T\_PULSE\_PUSHER$), desviando a peça para a Pista de Rejeição. A confirmação da extensão/retração pode ser monitorada via **`Pusher 0 (Front Limit)`** e **`Pusher 0 (Back Limit)`**.

### 4. Monitoramento (Timeout)

* Se o transportador estiver ligado, mas o **`Diffuse Sensor 0`** não for ativado por mais de 10 segundos ($T\_CYCLE\_TIMEOUT$ expira), o PLC aciona a **`Stack Light 0 (Yellow)`**. Isso alerta o operador sobre uma possível **falta de material** ou um **bloqueio** antes da estação de inspeção.

---

## 📊 VANTAGENS DO PROJETO

* **Automação da Qualidade:** Reduz a necessidade de inspeção manual, garantindo consistência.
* **Rastreabilidade:** Os contadores fornecem métricas em tempo real sobre a produção total, aprovação e rejeição (Taxa de Rejeição).
* **Controle Preciso:** O temporizador de pulso garante que o atuador use apenas o tempo necessário para rejeitar a peça, otimizando o ciclo e prevenindo colisões.
* **Alerta Precoce:** O temporizador de Timeout evita que a linha funcione "a seco" por muito tempo, sinalizando problemas a montante.