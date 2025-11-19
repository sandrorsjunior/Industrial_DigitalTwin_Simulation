import sys
import time
import json
import threading
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
            with open(self.filename, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')
            print(f"[{log_entry['timestamp_local']}] 🔔 Logged change for {log_entry['node_id']} ({log_entry['display_name']}): {log_entry['value']}")

        except Exception as e:
            print(f"Erro ao escrever no arquivo de log: {e}", file=sys.stderr)


# --- 3. Definição do Logger Principal com Subscrição ---

class OPCUASubscriptionLogger:
    """
    Gerencia a conexão OPC UA, mapeia variáveis e as monitora
    usando uma subscrição para registrar mudanças de dados.
    """
    def __init__(self, server_url, variables_to_monitor, log_interval_seconds=1.0):
        self.server_url = server_url
        self.variables_to_monitor = variables_to_monitor
        self.log_interval_seconds = log_interval_seconds
        self.client = None
        self.nodes_to_read = [] # Lista de objetos Node para leitura
        self.node_metadata = {} # {NodeIdStr: {'display_name': '...'}}
        self.logger = SubscriptionLogger()
        self._stop_event = threading.Event()
        self._logging_thread = None

    def _connect_and_setup(self):
        """Conecta ao servidor, mapeia variáveis e cria a subscrição."""
        print(f"--- Tentando conectar ao servidor OPC UA em: {self.server_url} ---")
        self.client = Client(self.server_url)
        self.client.connect()
        print("✅ Conexão estabelecida com sucesso.")

        # 1. Mapeamento de Metadados das Variáveis
        self.nodes_to_read = []
        self.node_metadata = {}
        for node_id_str in self.variables_to_monitor:
            try:
                node = self.client.get_node(node_id_str)
                display_name = node.get_display_name().Text
                self.node_metadata[node_id_str] = {'display_name': display_name}
                self.nodes_to_read.append(node)
                print(f"   -> Mapeada variável: {node_id_str} (Display Name: {display_name})")
            except Exception as e:
                print(f"   ❌ Erro ao mapear o Node {node_id_str}: {e}. Pulando este Node.", file=sys.stderr)
        
        if not self.nodes_to_read:
            print("Nenhuma variável válida encontrada para monitorar. Desconectando.", file=sys.stderr)
            self._cleanup()
            raise Exception("Nenhuma variável válida para monitorar.")

    def _log_snapshot(self):
        """Lê todas as variáveis e as registra como um único ponto de dados."""
        while not self._stop_event.is_set():
            try:
                if self.client:
                    # Cria um único registro (log_entry) com todas as variáveis
                    log_entry = {
                        "timestamp_local": datetime.datetime.now().isoformat()
                    }
                    
                    # Lê os valores de todos os nós de uma vez
                    values = self.client.get_values(self.nodes_to_read)
                    
                    # Adiciona cada variável ao registro
                    for node_obj, val in zip(self.nodes_to_read, values):
                        node_id_str = node_obj.nodeid.to_string()
                        display_name = self.node_metadata.get(node_id_str, {}).get('display_name', 'N/A')
                        log_entry[display_name] = val
                    
                    # Escreve a linha completa no arquivo
                    with open(self.logger.filename, 'a', encoding='utf-8') as f:
                        f.write(json.dumps(log_entry) + '\n')
                    
                    print(f"[{log_entry['timestamp_local']}] 📸 Snapshot de {len(self.nodes_to_read)} variáveis salvo.")
                
                time.sleep(self.log_interval_seconds)

            except ua.UaError as e:
                print(f"\n[ERRO OPC UA no Logging]: {e}. O loop principal tentará reconectar.", file=sys.stderr)
                # O loop principal cuidará da reconexão
                break 
            except Exception as e:
                print(f"\n[ERRO no Logging Thread]: {e}", file=sys.stderr)
                time.sleep(self.log_interval_seconds)
        
    def run(self):
        """Loop principal com lógica de reconexão resiliente."""
        reconnect_delay = 5  # Segundos para esperar antes de tentar reconectar
        
        while True:
            try:
                if self.client is None:
                    self._connect_and_setup()
                
                if self.client is not None:
                    # Inicia a thread de logging em segundo plano
                    self._stop_event.clear()
                    self._logging_thread = threading.Thread(target=self._log_snapshot, daemon=True)
                    self._logging_thread.start()
                    print(f"\n--- Iniciando coleta de snapshots a cada {self.log_interval_seconds}s. Pressione Ctrl+C para sair. ---")
                    while True:
                        time.sleep(1) # Loop principal apenas para manter a conexão e detectar erros
                
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
        self._stop_event.set()
        if self._logging_thread and self._logging_thread.is_alive():
            print("Aguardando a thread de logging encerrar...")
            self._logging_thread.join(timeout=2)
        self._logging_thread = None

        if self.client:
            try:
                self.client.disconnect()
                print("Cliente desconectado.")
            except Exception as e:
                print(f"Erro ao desconectar cliente: {e}")
            self.client = None
        
        print("Limpeza concluída.")


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
    
    # Intervalo de coleta de dados em segundos
    LOG_INTERVAL_SECONDS = 1.0

    # --------------------
    
    if not NODES_TO_MONITOR:
        print("Por favor, configure a lista NODES_TO_MONITOR com os NodeIds desejados.")
        sys.exit(1)

    logger = OPCUASubscriptionLogger(
        server_url=OPC_SERVER_URL,
        variables_to_monitor=NODES_TO_MONITOR,
        log_interval_seconds=LOG_INTERVAL_SECONDS
    )
    
    logger.run()