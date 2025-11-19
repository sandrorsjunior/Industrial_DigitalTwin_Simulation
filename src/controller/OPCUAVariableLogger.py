import sys
import time
import json
import datetime
from opcua import Client, ua

# --- 1. Definição do Handler de Log de Subscrição ---

class SubscriptionLogger:
    """
    Logger que processa e salva os dados recebidos via subscrição OPC UA
    em um arquivo NDJSON (JSON delimitado por nova linha).
    """
    def __init__(self, filename="opcua_log_subscription.ndjson"):
        self.filename = filename

    def log_data(self, log_entry: dict):
        """Escreve uma entrada de log no arquivo NDJSON."""
        try:
            with open(self.filename, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            print(f"[{log_entry['timestamp_local']}] 🔔 Logged change for {log_entry['node_id']} ({log_entry['display_name']}): {log_entry['value']}")

        except Exception as e:
            print(f"Erro ao escrever no arquivo de log: {e}", file=sys.stderr)


# --- 2. Handler para Notificações de Mudança de Dados ---

class DataChangeHandler:
    """
    Manipulador que é chamado pelo cliente OPC UA sempre que um valor de
    um nó monitorado muda no servidor.
    """
    def __init__(self, logger: SubscriptionLogger, node_metadata: dict):
        self.logger = logger
        self.node_metadata = node_metadata

    def datachange_notification(self, node, val, data):
        """
        Método de callback chamado quando há uma mudança de dados.
        """
        node_id_str = node.nodeid.to_string()
        metadata = self.node_metadata.get(node_id_str, {})

        log_entry = {
            "timestamp_local": datetime.datetime.now().isoformat(),
            "node_id": node_id_str,
            "display_name": metadata.get('display_name', 'N/A'),
            "value": val,
            "source_timestamp": data.monitored_item.Value.SourceTimestamp.isoformat() if data.monitored_item.Value.SourceTimestamp else None,
            "server_timestamp": data.monitored_item.Value.ServerTimestamp.isoformat() if data.monitored_item.Value.ServerTimestamp else None,
        }
        
        self.logger.log_data(log_entry)


# --- 3. Definição do Logger Principal com Subscrição ---

class OPCUASubscriptionLogger:
    """
    Gerencia a conexão OPC UA, mapeia variáveis e as monitora
    usando uma subscrição para registrar mudanças de dados.
    """
    def __init__(self, server_url, variables_to_monitor, publishing_interval_ms=500):
        self.server_url = server_url
        self.variables_to_monitor = variables_to_monitor
        self.publishing_interval_ms = publishing_interval_ms
        self.client = None
        self.subscription = None
        self.node_metadata = {}  # {NodeIdStr: {'display_name': '...'}}
        self.logger = SubscriptionLogger()

    def _connect_and_setup(self):
        """Conecta ao servidor, mapeia variáveis e cria a subscrição."""
        print(f"--- Tentando conectar ao servidor OPC UA em: {self.server_url} ---")
        self.client = Client(self.server_url)
        self.client.connect()
        print("✅ Conexão estabelecida com sucesso.")

        # 1. Mapeamento de Metadados das Variáveis
        self.node_metadata = {}
        nodes_to_subscribe = []
        for node_id_str in self.variables_to_monitor:
            try:
                node = self.client.get_node(node_id_str)
                display_name = node.get_display_name().Text
                self.node_metadata[node_id_str] = {'display_name': display_name}
                nodes_to_subscribe.append(node)
                print(f"   -> Mapeada variável: {node_id_str} (Display Name: {display_name})")
            except Exception as e:
                print(f"   ❌ Erro ao mapear o Node {node_id_str}: {e}. Pulando este Node.", file=sys.stderr)
        
        if not nodes_to_subscribe:
            print("Nenhuma variável válida encontrada para monitorar. Desconectando.", file=sys.stderr)
            self._cleanup()
            raise Exception("Nenhuma variável válida para monitorar.")

        # 2. Criação da Subscrição e do Handler
        handler = DataChangeHandler(self.logger, self.node_metadata)
        self.subscription = self.client.create_subscription(self.publishing_interval_ms, handler)
        
        # 3. Anexa os nós à subscrição
        self.subscription.subscribe_data_change(nodes_to_subscribe)
        print(f"\n✅ Subscrição criada com sucesso para {len(nodes_to_subscribe)} variáveis.")

    def run(self):
        """Loop principal com lógica de reconexão resiliente."""
        reconnect_delay = 5  # Segundos para esperar antes de tentar reconectar
        
        while True:
            try:
                if self.client is None:
                    self._connect_and_setup()
                
                if self.client is not None:
                    print(f"Aguardando notificações de mudança de dados. Pressione Ctrl+C para sair.")
                    while True:
                        time.sleep(1)
                
            except ua.UaError as e:
                print(f"\n[ERRO OPC UA]: {e}. Tentando reconexão em {reconnect_delay}s...", file=sys.stderr)
                self._cleanup()
                time.sleep(reconnect_delay)
            except ConnectionRefusedError:
                print(f"\n[ERRO DE REDE]: Conexão recusada. Tentando reconexão em {reconnect_delay}s...", file=sys.stderr)
                self._cleanup()
                time.sleep(reconnect_delay)
            except KeyboardInterrupt:
                print("\n🚨 Interrupção do usuário recebida. Encerrando...")
                self._cleanup()
                break
            except Exception as e:
                # Inclui a exceção de "Nenhuma variável válida..." aqui
                print(f"\n[ERRO INESPERADO]: {e}. Tentando reconexão em {reconnect_delay}s...", file=sys.stderr)
                self._cleanup()
                time.sleep(reconnect_delay)

    def _cleanup(self):
        """Limpa a conexão do cliente."""
        if self.subscription:
            try:
                self.subscription.delete()
                print("Subscrição removida.")
            except Exception as e:
                print(f"Erro ao remover subscrição: {e}")
            self.subscription = None

        if self.client:
            try:
                self.client.disconnect()
                print("Cliente desconectado.")
            except Exception as e:
                print(f"Erro ao desconectar cliente: {e}")
            self.client = None


# --- 4. Execução do Script ---

if __name__ == "__main__":
    # --- Configuração ---
    
    # ⚠️ Mude este endereço para o seu servidor OPC UA real
    OPC_SERVER_URL = "opc.tcp://127.0.0.2:4840"
    
    # Lista completa de NodeIDs
    NODES_TO_MONITOR = [
    # Contadores_PLC (ns=2;i=2)
    "ns=2;i=7", # C_TOTAL
    "ns=2;i=8", # C_APROVADAS
    "ns=2;i=9", # C_REJEITADAS
    
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
    
    # Intervalo de publicação da subscrição em milissegundos
    PUBLISHING_INTERVAL_MS = 500

    # --------------------
    
    if not NODES_TO_MONITOR:
        print("Por favor, configure a lista NODES_TO_MONITOR com os NodeIds desejados.")
        sys.exit(1)

    logger = OPCUASubscriptionLogger(
        server_url=OPC_SERVER_URL,
        variables_to_monitor=NODES_TO_MONITOR,
        publishing_interval_ms=PUBLISHING_INTERVAL_MS
    )
    
    logger.run()