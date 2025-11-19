import time
from opcua import Server, ua

# --- 1. CONFIGURAÇÕES BÁSICAS ---
# Endereço de conexão do Servidor
OPCUA_ENDPOINT = "opc.tcp://127.0.0.2:4840"
SERVER_NAME = "Servidor_PLC_Linha_Triagem"
NAMESPACE_URI = "http://controle.fabrica.com/ns"

def run_opcua_server():
    # Inicializa o servidor
    server = Server()
    server.set_endpoint(OPCUA_ENDPOINT)
    server.set_server_name(SERVER_NAME)
    
    # --- 2. REGISTRO DO NAMESPACE E ESTRUTURA ---
    
    # Registra o namespace e obtém o índice (idx)
    idx = server.register_namespace(NAMESPACE_URI)
    
    # Obtém o nó de objetos raiz
    objects = server.get_objects_node()
    
    # Cria a pasta principal para o processo
    process_node = objects.add_folder(idx, "Linha_Triagem_IIoT")
    
    # Cria subpastas para organização das variáveis
    contadores_node = process_node.add_folder(idx, "Contadores_PLC")
    sensores_node = process_node.add_folder(idx, "IOs_Sensores_Fisicos")
    atuadores_node = process_node.add_folder(idx, "IOs_Atuadores_Fisicos")
    encoder_node = process_node.add_folder(idx, "IOs_Encoder")
    interno_node = process_node.add_folder(idx, "IOs_Internos_FactoryIO")

    # --- 3. CRIAÇÃO E EXPOSIÇÃO DAS VARIÁVEIS ---
    
    # 3.1. Variáveis de Contagem (Int32)
    print("Criando Contadores PLC...")
    var_total = contadores_node.add_variable(idx, "C_TOTAL", 0, datatype=ua.NodeId(ua.ObjectIds.Int32))
    var_aprovadas = contadores_node.add_variable(idx, "C_APROVADAS", 0, datatype=ua.NodeId(ua.ObjectIds.Int32))
    var_rejeitadas = contadores_node.add_variable(idx, "C_REJEITADAS", 0, datatype=ua.NodeId(ua.ObjectIds.Int32))
    var_total.set_writable(); var_aprovadas.set_writable(); var_rejeitadas.set_writable()
    
    # 3.2. IOs de Sensores Físicos (Boolean)
    print("Criando Sensores...")
    
    # Sensores Chave
    var_diffuse_sensor_0 = sensores_node.add_variable(idx, "Diffuse_Sensor_0", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_diffuse_sensor_1 = sensores_node.add_variable(idx, "Diffuse_Sensor_1", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_pusher_back = sensores_node.add_variable(idx, "Pusher_0_Back_Limit", True, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_pusher_front = sensores_node.add_variable(idx, "Pusher_0_Front_Limit", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_emergency_stop = sensores_node.add_variable(idx, "Emergency_Stop_0", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    
    # Botões (Entradas)
    var_start_button = sensores_node.add_variable(idx, "Start_Button_0", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_stop_button = sensores_node.add_variable(idx, "Stop_Button_0", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_reset_button = sensores_node.add_variable(idx, "Reset_Button_0", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    
    # Tornar todos os sensores físicos writeable (para simulação via cliente Python)
    for var in [var_diffuse_sensor_0, var_diffuse_sensor_1, var_pusher_back, var_pusher_front, var_emergency_stop, var_start_button, var_stop_button, var_reset_button]:
        var.set_writable()


    # 3.3. IOs de Atuadores Físicos (Digital e Analógico)
    print("Criando Atuadores...")
    
    # Transporte e Atuação
    var_conveyor = atuadores_node.add_variable(idx, "Belt_Conveyor_6m_0", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_pusher = atuadores_node.add_variable(idx, "Pusher_0", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_emitter_emit = atuadores_node.add_variable(idx, "Emitter_0_Emit", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_emitter_base = atuadores_node.add_variable(idx, "Emitter_0_Base", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_emitter_part = atuadores_node.add_variable(idx, "Emitter_0_Part", 0, datatype=ua.NodeId(ua.ObjectIds.Int32)) # Analógico (seleção da peça)
    var_remover_0 = atuadores_node.add_variable(idx, "Remover_0_Remove", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_remover_1 = atuadores_node.add_variable(idx, "Remover_1_Remove", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    
    # Sinalização (Stack Light e Botões)
    var_sl_green = atuadores_node.add_variable(idx, "Stack_Light_0_Green", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_sl_red = atuadores_node.add_variable(idx, "Stack_Light_0_Red", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_sl_yellow = atuadores_node.add_variable(idx, "Stack_Light_0_Yellow", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_warning_light = atuadores_node.add_variable(idx, "Warning_Light_0", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_start_light = atuadores_node.add_variable(idx, "Start_Button_0_Light", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_stop_light = atuadores_node.add_variable(idx, "Stop_Button_0_Light", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_reset_light = atuadores_node.add_variable(idx, "Reset_Button_0_Light", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    
    # Displays
    var_display_0 = atuadores_node.add_variable(idx, "Digital_Display_0", 0, datatype=ua.NodeId(ua.ObjectIds.Int32))
    var_display_1 = atuadores_node.add_variable(idx, "Digital_Display_1", 0, datatype=ua.NodeId(ua.ObjectIds.Int32))
    
    # Tornar todos os atuadores writeable
    for var in [var_conveyor, var_pusher, var_emitter_emit, var_emitter_base, var_emitter_part, var_remover_0, var_remover_1, var_sl_green, var_sl_red, var_sl_yellow, var_warning_light, var_start_light, var_stop_light, var_reset_light, var_display_0, var_display_1]:
        var.set_writable()
        
    # 3.4. IOs de Encoder (Boolean)
    print("Criando Encoder...")
    var_encoder_a = encoder_node.add_variable(idx, "Belt_Conveyor_0_Encoder_Signal_A", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_encoder_b = encoder_node.add_variable(idx, "Belt_Conveyor_0_Encoder_Signal_B", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_encoder_a.set_writable(); var_encoder_b.set_writable()

    # 3.5. IOs Internos do Factory I/O (Boolean/Analógico)
    print("Criando Variáveis Internas...")
    var_io_running = interno_node.add_variable(idx, "FACTORY_IO_Running", True, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_io_reset = interno_node.add_variable(idx, "FACTORY_IO_Reset", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_io_paused = interno_node.add_variable(idx, "FACTORY_IO_Paused", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_io_run = interno_node.add_variable(idx, "FACTORY_IO_Run", True, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_io_pause = interno_node.add_variable(idx, "FACTORY_IO_Pause", False, datatype=ua.NodeId(ua.ObjectIds.Boolean))
    var_io_timescale = interno_node.add_variable(idx, "FACTORY_IO_TimeScale", 1.0, datatype=ua.NodeId(ua.ObjectIds.Float))
    var_io_cam_pos = interno_node.add_variable(idx, "FACTORY_IO_CameraPosition", 0.0, datatype=ua.NodeId(ua.ObjectIds.Float)) # Usando Float simples para simplificar
    
    for var in [var_io_running, var_io_reset, var_io_paused, var_io_run, var_io_pause, var_io_timescale, var_io_cam_pos]:
        var.set_writable()

    # --- 4. INICIALIZAÇÃO DO SERVIDOR ---
    
    print("\n" + "="*50)
    print(f"Servidor OPC UA iniciado em: {OPCUA_ENDPOINT}")
    print("Namespace Registrado:", NAMESPACE_URI)
    print("Todas as variáveis de I/O e Lógica foram criadas e estão Writeable.")
    print("="*50 + "\n")
    server.start()
    
    # --- 5. LOOP DE MANUTENÇÃO (Mantém o servidor rodando) ---
    try:
        count = 0
        while True:
            # ************************************************************
            # * CLIENTE (CODESYS/PYTHON ORQUESTRADOR) ESCREVE AQUI       *
            # * O SERVIDOR APENAS MANTÉM OS NÓS ATIVOS                   *
            # ************************************************************
            
            # Exemplo Simples de Monitoramento para o console
            if count % 10 == 0:
                print(f"Server ativo. C_TOTAL: {var_total.get_value()} | Sensor Difuso: {var_diffuse_sensor_0.get_value()}")
            
            # Simulação de alteração do C_TOTAL para mostrar que está vivo
            #var_total.set_value(var_total.get_value() + 1)
            count += 1
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nServidor sendo desligado.")
    finally:
        # Desliga o servidor de forma limpa
        server.stop()
        print("Servidor OPC UA desligado com sucesso.")

if __name__ == "__main__":
   run_opcua_server()
