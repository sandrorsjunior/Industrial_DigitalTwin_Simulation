from opcua import Client, ua
import time
import json
import datetime
import os

# --- Configuração do Log ---
LOG_FILE_PATH = "../../logs/opcua_variable_log.ndjson"

# Lista de NodeIds a serem monitorados
NODES_TO_MONITOR = [
    # Contadores_PLC (ns=2;i=2)
    "ns=2;i=7",  # C_TOTAL
    "ns=2;i=8",  # C_APROVADAS
    "ns=2;i=9",  # C_REJEITADAS
    
    # IOs_Sensores_Fisicos (ns=2;i=3)
    "ns=2;i=10", # Diffuse_Sensor_0
    "ns=2;i=11", # Diffuse_Sensor_1
    "ns=2;i=12", # Pusher_0_Back_Limit
    "ns=2;i=13", # Pusher_0_Front_Limit
    "ns=2;i=14", # Emergency_Stop_0
    "ns=2;i=15", # Start_Button_0
    "ns=2;i=16", # Stop_Button_0
    "ns=2;i=17", # Reset_Button_0
    
    # IOs_Atuadores_Fisicos (ns=2;i=4)
    "ns=2;i=18", # Belt_Conveyor_6m_0
    "ns=2;i=19", # Pusher_0
    "ns=2;i=20", # Emitter_0_Emit
    "ns=2;i=21", # Emitter_0_Base
    "ns=2;i=22", # Emitter_0_Part
    "ns=2;i=23", # Remover_0_Remove
    "ns=2;i=24", # Remover_1_Remove
    "ns=2;i=25", # Stack_Light_0_Green
    "ns=2;i=26", # Stack_Light_0_Red
    "ns=2;i=27", # Stack_Light_0_Yellow
    "ns=2;i=28", # Warning_Light_0
    "ns=2;i=29", # Start_Button_0_Light
    "ns=2;i=30", # Stop_Button_0_Light
    "ns=2;i=31", # Reset_Button_0_Light
    "ns=2;i=32", # Digital_Display_0
    "ns=2;i=33", # Digital_Display_1
    
    # IOs_Encoder (ns=2;i=5)
    "ns=2;i=34", # Belt_Conveyor_0_Encoder_Signal_A
    "ns=2;i=35", # Belt_Conveyor_0_Encoder_Signal_B
    
    # IOs_Internos_FactoryIO (ns=2;i=6)
    "ns=2;i=36", # FACTORY_IO_Running
    "ns=2;i=37", # FACTORY_IO_Reset
    "ns=2;i=38", # FACTORY_IO_Paused
    "ns=2;i=39", # FACTORY_IO_Run
    "ns=2;i=40", # FACTORY_IO_Pause
    "ns=2;i=41", # FACTORY_IO_TimeScale
    "ns=2;i=42", # FACTORY_IO_CameraPosition
]

class SubHandler(object):
    """
    Handler para processar notificações de data change, armazenar o último valor
    e registrar o evento em um arquivo NDJSON.
    """
    def __init__(self, log_file_path):
        # Dicionário para armazenar o último valor lido de cada nó: {node_id_str: last_value}
        self.last_values = {}
        self.log_file_path = log_file_path

    def datachange_notification(self, node, val, data):
        node_id_str = str(node.nodeid)
        
        # 1. Obter valor anterior e atualizar o valor armazenado
        # Usamos .get() para retornar None se for a primeira notificação
        valor_anterior = self.last_values.get(node_id_str)
        
        # 2. Extrair informações do evento
        # O 'data' é um opcua.Subscription.EventData que contém a DataValue completa
        
        # O timestamp do servidor (útil para agrupar eventos simultâneos)
        server_ts = data.monitored_item.Value.SourceTimestamp
        timestamp_servidor = server_ts.isoformat() if server_ts else None
        
        # O tipo de dado
        # O VariantType contém o enum do tipo de dado (ex: ua.VariantType.Boolean)
        data_type = data.monitored_item.Value.Value.VariantType.name
        
        # 3. Construir o registro (JSON object)
        log_entry = {
            "evento_realizado": "DataChangeNotification",
            "quem_realizou": "OPCUA_Client", # Identificador do cliente
            "node_id": node_id_str,
            "valor_atual": val,
            "valor_anterior": valor_anterior,
            "data_type": data_type,
            "timestamp_servidor": timestamp_servidor,
            "timestamp_local_processamento": datetime.datetime.now().isoformat(timespec='milliseconds'),
        }

        # 4. Escrever no arquivo NDJSON
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                # O default=str é usado para garantir que objetos complexos (como datetime.datetime) 
                # sejam serializados corretamente se ainda não tiverem sido convertidos.
                json.dump(log_entry, f, default=str) 
                f.write('\n') # Adiciona o delimitador de nova linha para o formato NDJSON

        except Exception as e:
            print(f"🚨 ERRO ao escrever no arquivo de log: {e}")

        # 5. Atualiza o valor após o log (para o valor anterior ser correto no próximo evento)
        self.last_values[node_id_str] = val


if __name__ == "__main__":
    server_url = "opc.tcp://127.0.0.2:4840"
    client = Client(server_url)

    try:
        # 1. Conexão
        client.connect()
        print(f"✅ Cliente conectado ao servidor em {server_url}")

        # 2. Criação do Handler e Assinatura
        # Inicializa o handler passando o caminho do arquivo de log
        handler = SubHandler(LOG_FILE_PATH)
        # Cria uma assinatura com um intervalo de amostragem (200ms)
        subscription = client.create_subscription(200, handler)

        # 3. Inscrição para todos os Nodes
        nodes_count = 0
        print(f"\n📝 Arquivo de log: {LOG_FILE_PATH}")
        print("⏳ Inscrevendo para monitorar os nós...")
        
        for node_id_str in NODES_TO_MONITOR:
            try:
                node = client.get_node(node_id_str)
                subscription.subscribe_data_change(node)
                # Inicializa o valor no handler lendo o valor atual imediatamente (opcional, mas garante o primeiro 'valor_anterior' como o valor inicial lido)
                handler.last_values[node_id_str] = node.get_value()
                print(f"   - Assinado com sucesso: {node_id_str}")
                nodes_count += 1
            except Exception as e:
                print(f"   - ❌ ERRO ao assinar {node_id_str}: {e}")

        print(f"\n✨ Total de {nodes_count} nós monitorados.")
        print("📢 Aguardando notificações e registrando em NDJSON... (Pressione Ctrl+C para sair)")

        # 4. Loop principal
        while True:
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nInterrupção pelo usuário detectada.")
    except Exception as e:
        print(f"\n🚨 Ocorreu um erro: {e}")
    finally:
        # 5. Desconexão
        if 'client' in locals() and client:
            print("\nDesconectando o cliente.")
            client.disconnect()
            print("🛑 Cliente desconectado.")