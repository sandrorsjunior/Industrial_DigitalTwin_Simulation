# Documentação do Servidor OPC UA: Linha de Triagem IIoT

## 1. Visão Geral do Projeto

Este documento descreve a configuração e a estrutura de endereçamento
(**Address Space**) de um Servidor **OPC UA**, implementado em Python
utilizando a biblioteca **python-opcua**.

O servidor simula e fornece dados em tempo real de uma **Linha de
Triagem Industrial (Sorting Line)**, ideal para integração com
plataformas como **Factory I/O** e sistemas de controle (PLC/SoftPLC,
como CODESYS).

O servidor atua como um **broker de dados**, expondo todas as entradas e
saídas (I/O) do processo, bem como variáveis internas e contadores.

## 2. Configurações de Conexão

  ------------------------------------------------------------------------------------
  Parâmetro                Valor                            Descrição
  ------------------------ -------------------------------- --------------------------
  **Endpoint**             opc.tcp://127.0.0.2:4840         Endereço TCP/IP onde o
                                                            servidor está escutando.

  **Nome do Servidor**     Servidor_PLC_Linha_Triagem       Nome amigável do servidor
                                                            OPC UA.

  **Namespace URI**        http://controle.fabrica.com/ns   Identificador único do
                                                            namespace do processo.
  ------------------------------------------------------------------------------------

## 3. Estrutura do Address Space

### 3.1 Namespace

-   **URI:** `http://controle.fabrica.com/ns`
-   Geralmente registrado como **idx = 2**

### 3.2 Hierarquia de Pastas

  Pasta                        Descrição
  ---------------------------- --------------------------------------
  **Linha_Triagem_IIoT**       Nó principal da linha de produção.
  **Contadores_PLC**           Variáveis inteiras de contagem.
  **IOs_Sensores_Fisicos**     Entradas físicas Booleanas.
  **IOs_Atuadores_Fisicos**    Saídas físicas Booleanas e Inteiras.
  **IOs_Encoder**              Sinais A e B do encoder.
  **IOs_Internos_FactoryIO**   Variáveis internas do Factory I/O.

## 4. Definição Detalhada das Variáveis

### 4.1 Contadores (Int32)

**Local:** `Linha_Triagem_IIoT/Contadores_PLC`

  Variável       Tipo    Descrição
  -------------- ------- --------------------------
  C_TOTAL        Int32   Contador total de peças.
  C_APROVADAS    Int32   Peças aprovadas.
  C_REJEITADAS   Int32   Peças rejeitadas.

### 4.2 Sensores (Boolean)

**Local:** `Linha_Triagem_IIoT/IOs_Sensores_Fisicos`

  Variável                Tipo      Descrição
  ----------------------- --------- ------------------------
  Diffuse_Sensor_0        Boolean   Sensor difuso 0.
  Diffuse_Sensor_1        Boolean   Sensor difuso 1.
  Pusher_0\_Back_Limit    Boolean   Fim de curso traseiro.
  Pusher_0\_Front_Limit   Boolean   Fim de curso frontal.
  Emergency_Stop_0        Boolean   Botão de emergência.
  Start_Button_0          Boolean   Botão de início.
  Stop_Button_0           Boolean   Botão de parada.
  Reset_Button_0          Boolean   Botão de reset.

### 4.3 Atuadores (Boolean / Int32)

**Local:** `Linha_Triagem_IIoT/IOs_Atuadores_Fisicos`

  Variável                Tipo      Descrição
  ----------------------- --------- --------------------------
  Belt_Conveyor_6m_0      Boolean   Transportador principal.
  Pusher_0                Boolean   Atuador de empurrão.
  Emitter_0\_Emit         Boolean   Emite peça.
  Emitter_0\_Base         Boolean   Base do emissor.
  Emitter_0\_Part         Int32     Tipo da peça.
  Remover_0\_Remove       Boolean   Remoção na estação 0.
  Remover_1\_Remove       Boolean   Remoção na estação 1.
  Stack_Light_0\_Green    Boolean   Luz verde.
  Stack_Light_0\_Red      Boolean   Luz vermelha.
  Stack_Light_0\_Yellow   Boolean   Luz amarela.
  Warning_Light_0         Boolean   Luz de aviso.
  Start_Button_0\_Light   Boolean   Luz botão iniciar.
  Stop_Button_0\_Light    Boolean   Luz botão parar.
  Reset_Button_0\_Light   Boolean   Luz botão reset.
  Digital_Display_0       Int32     Display digital 0.
  Digital_Display_1       Int32     Display digital 1.

### 4.4 Encoder (Boolean)

**Local:** `Linha_Triagem_IIoT/IOs_Encoder`

  Variável                            Tipo      Descrição
  ----------------------------------- --------- -----------
  Belt_Conveyor_0\_Encoder_Signal_A   Boolean   Pulso A.
  Belt_Conveyor_0\_Encoder_Signal_B   Boolean   Pulso B.

### 4.5 Internos Factory I/O (Boolean / Float)

**Local:** `Linha_Triagem_IIoT/IOs_Internos_FactoryIO`

  Variável                    Tipo      Descrição
  --------------------------- --------- ---------------------
  FACTORY_IO_Running          Boolean   Simulação rodando.
  FACTORY_IO_Reset            Boolean   Reset da simulação.
  FACTORY_IO_Paused           Boolean   Simulação pausada.
  FACTORY_IO_Run              Boolean   Comando iniciar.
  FACTORY_IO_Pause            Boolean   Comando pausar.
  FACTORY_IO_TimeScale        Float     Escala de tempo.
  FACTORY_IO_CameraPosition   Float     Posição da câmera.

## 5. Arquitetura de Comunicação

### Servidor OPC UA (Python)

-   Mantém Address Space
-   Responde leituras/escritas
-   Não implementa lógica

### Cliente OPC UA (PLC / Python / CODESYS)

-   Conecta em: `opc.tcp://127.0.0.2:4840`
-   Lê sensores e encoder
-   Escreve atuadores, contadores e variáveis internas
-   Implementa a lógica da linha de triagem
