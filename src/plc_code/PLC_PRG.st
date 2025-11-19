PROGRAM PLC_PRG
VAR
    // Flancos (Edge Detection) para Sensores/Botões
    R_TRIG_StartButton      : R_TRIG;   // Flanco de subida para o botão Start
    R_TRIG_StopButton       : R_TRIG;   // Flanco de subida para o botão Stop
    R_TRIG_ResetButton      : R_TRIG;   // Flanco de subida para o botão Reset
    R_TRIG_Sensor_In        : R_TRIG;   // Flanco de subida para peça entrando (Diffuse_Sensor_0)
    
    // Variáveis de Estado da Máquina
    B_Sistema_Ligado        : BOOL := FALSE;    // Indica se o sistema está em modo RUN (Start/Stop)
    B_Emergencia_Ativa      : BOOL := TRUE;     // TRUE se a parada de emergência estiver ativa
    
    // Variáveis de Controle de Ação
    B_Rejeitar_Peca         : BOOL := FALSE;    // Flag que mantém o Pusher ligado pelo tempo de pulso
    
    // Instâncias de Temporizadores IEC
    T_PULSE_PUSHER_Inst     : TON;              // Temporizador para o Pulso do Pistão (0.5s)
    T_CYCLE_TIMEOUT_Inst    : TON;              // Temporizador de Timeout (10s)

    // Variáveis de Estado Interno
    B_Timeout_Ativo         : BOOL := FALSE;    // Flag que indica que o timeout expirou
    
    // Constantes
    C_TEMPO_PULSO_PUSHER    : TIME := T#500MS;  // 0.5 segundos para o pistão
    C_TEMPO_TIMEOUT_CICLO   : TIME := T#10S;    // 10 segundos para alerta de falta de material
END_VAR


// ----------------------------------------------
// 1. GERENCIAMENTO DE EMERGÊNCIA E ESTADO
// ----------------------------------------------

// B_Emergencia_Ativa: TRUE se o botão de emergência estiver pressionado
B_Emergencia_Ativa := NOT Datasource.Linha_Triagem_IIoT_IOs_Sensores_Fisicos_Emergency_Stop_0;

// Detecção de flancos para botões de controle
R_TRIG_StartButton(CLK := Datasource.Linha_Triagem_IIoT_IOs_Sensores_Fisicos_Start_Button_0);
R_TRIG_StopButton(CLK := Datasource.Linha_Triagem_IIoT_IOs_Sensores_Fisicos_Stop_Button_0);
R_TRIG_ResetButton(CLK := Datasource.Linha_Triagem_IIoT_IOs_Sensores_Fisicos_Reset_Button_0);

// Lógica de Ativação/Desativação do Sistema (RUN/STOP)
IF R_TRIG_StartButton.Q AND NOT B_Emergencia_Ativa THEN
    B_Sistema_Ligado := TRUE;
END_IF

IF R_TRIG_StopButton.Q OR B_Emergencia_Ativa THEN
    B_Sistema_Ligado := FALSE;
END_IF

// Ativação dos atuadores mestres
Datasource.Linha_Triagem_IIoT_IOs_Atuadores_Fisicos_Belt_Conveyor_6m_0 := B_Sistema_Ligado AND NOT B_Emergencia_Ativa;
Datasource.Linha_Triagem_IIoT_IOs_Atuadores_Fisicos_Emitter_0_Emit := B_Sistema_Ligado AND NOT B_Emergencia_Ativa;
Datasource.Linha_Triagem_IIoT_IOs_Atuadores_Fisicos_Remover_0_Remove := B_Sistema_Ligado AND NOT B_Emergencia_Ativa;
Datasource.Linha_Triagem_IIoT_IOs_Atuadores_Fisicos_Remover_1_Remove := B_Sistema_Ligado AND NOT B_Emergencia_Ativa;

// ----------------------------------------------
// 2. INSPEÇÃO, CONTAGEM E DECISÃO
// * Sensor 0 (Presença): Gatilho R_TRIG
// * Sensor 1 (Altura): Checa a Qualidade
// ----------------------------------------------

// O R_TRIG detecta a chegada da peça (Diffuse_Sensor_0)
R_TRIG_Sensor_In(CLK := Datasource.Linha_Triagem_IIoT_IOs_Sensores_Fisicos_Diffuse_Sensor_0);

// Ação no momento que a peça entra na zona de inspeção
IF R_TRIG_Sensor_In.Q AND B_Sistema_Ligado THEN
    
    // Resetar o temporizador de timeout (Houve detecção de peça)
    T_CYCLE_TIMEOUT_Inst(IN := FALSE);

    // 1. Contagem Total (Qualquer peça que chega)
    Datasource.Linha_Triagem_IIoT_Contadores_PLC_C_TOTAL := Datasource.Linha_Triagem_IIoT_Contadores_PLC_C_TOTAL + 1;
    
    // 2. Inspeção (Lê o Sensor de Altura Diffuse_Sensor_1)
    IF Datasource.Linha_Triagem_IIoT_IOs_Sensores_Fisicos_Diffuse_Sensor_1 THEN
        
        // Peça OK
        Datasource.Linha_Triagem_IIoT_Contadores_PLC_C_APROVADAS := Datasource.Linha_Triagem_IIoT_Contadores_PLC_C_APROVADAS + 1;
        B_Rejeitar_Peca := FALSE; // Garante que a rejeição está desligada
        
    ELSE
        
        // Peça Ruim/Baixa
        Datasource.Linha_Triagem_IIoT_Contadores_PLC_C_REJEITADAS := Datasource.Linha_Triagem_IIoT_Contadores_PLC_C_REJEITADAS + 1;
        B_Rejeitar_Peca := TRUE; // Ativa a flag para iniciar o pulso do pistão
        
    END_IF
END_IF

// ----------------------------------------------
// 3. CONTROLE DO PISTÃO DE REJEIÇÃO (PULSO DE 0.5S)
// ----------------------------------------------

// O temporizador é ligado se B_Rejeitar_Peca for TRUE
T_PULSE_PUSHER_Inst(IN := B_Rejeitar_Peca, PT := C_TEMPO_PULSO_PUSHER);

// O pistão é ligado enquanto B_Rejeitar_Peca for TRUE
Datasource.Linha_Triagem_IIoT_IOs_Atuadores_Fisicos_Pusher_0 := B_Rejeitar_Peca;

// Quando o temporizador expira (Q=TRUE), o pulso de rejeição termina.
IF T_PULSE_PUSHER_Inst.Q THEN
    B_Rejeitar_Peca := FALSE; // Desliga o pistão (ele retrai)
    T_PULSE_PUSHER_Inst(IN := FALSE); // Reinicia o temporizador
END_IF


// ----------------------------------------------
// 4. MONITORAMENTO DE TIMEOUT
// ----------------------------------------------

// O temporizador é ligado se: Sistema ON E Sensor de PRESENÇA (0) OFF por muito tempo
T_CYCLE_TIMEOUT_Inst(
    IN := B_Sistema_Ligado AND NOT Datasource.Linha_Triagem_IIoT_IOs_Sensores_Fisicos_Diffuse_Sensor_0,
    PT := C_TEMPO_TIMEOUT_CICLO
);

B_Timeout_Ativo := T_CYCLE_TIMEOUT_Inst.Q;


// ----------------------------------------------
// 5. SINALIZAÇÃO E DISPLAY
// ----------------------------------------------

// Luz Verde (Operação)
Datasource.Linha_Triagem_IIoT_IOs_Atuadores_Fisicos_Stack_Light_0_Green := B_Sistema_Ligado AND NOT B_Timeout_Ativo AND NOT B_Emergencia_Ativa;

// Luz Vermelha (Rejeição ou Parada de Emergência)
Datasource.Linha_Triagem_IIoT_IOs_Atuadores_Fisicos_Stack_Light_0_Red := B_Emergencia_Ativa OR B_Rejeitar_Peca;

// Luz Amarela (Alerta/Timeout)
Datasource.Linha_Triagem_IIoT_IOs_Atuadores_Fisicos_Stack_Light_0_Yellow := B_Timeout_Ativo AND NOT B_Emergencia_Ativa;

// Luzes dos botões
Datasource.Linha_Triagem_IIoT_IOs_Atuadores_Fisicos_Start_Button_0_Light := B_Sistema_Ligado AND NOT B_Emergencia_Ativa;
Datasource.Linha_Triagem_IIoT_IOs_Atuadores_Fisicos_Stop_Button_0_Light := NOT B_Sistema_Ligado OR B_Emergencia_Ativa;

// Sinalização de Aviso (Pode ser ligado ao Timeout)
Datasource.Linha_Triagem_IIoT_IOs_Atuadores_Fisicos_Warning_Light_0 := B_Timeout_Ativo;

// Display Digital 0: Total de Peças
Datasource.Linha_Triagem_IIoT_IOs_Atuadores_Fisicos_Digital_Display_0 := Datasource.Linha_Triagem_IIoT_Contadores_PLC_C_TOTAL;

// Display Digital 1: Peças Aprovadas
Datasource.Linha_Triagem_IIoT_IOs_Atuadores_Fisicos_Digital_Display_1 := Datasource.Linha_Triagem_IIoT_Contadores_PLC_C_APROVADAS;


// ----------------------------------------------
// 6. LÓGICA DE RESET
// ----------------------------------------------

IF R_TRIG_ResetButton.Q THEN
    // Zera Contadores
    Datasource.Linha_Triagem_IIoT_Contadores_PLC_C_TOTAL := 0;
    Datasource.Linha_Triagem_IIoT_Contadores_PLC_C_APROVADAS := 0;
    Datasource.Linha_Triagem_IIoT_Contadores_PLC_C_REJEITADAS := 0;
    
    // Reseta flags e temporizadores
    T_PULSE_PUSHER_Inst(IN := FALSE);
    T_CYCLE_TIMEOUT_Inst(IN := FALSE);
    B_Timeout_Ativo := FALSE;
    B_Rejeitar_Peca := FALSE;
    B_Sistema_Ligado := FALSE;
END_IF


