import sys
import time
import json
from opcua import Client, ua

# --- 1. Definição do Handler de Log de Polling ---

class PollingLogger:
    """
    Simples Logger que processa e salva os dados lidos por polling
    em um arquivo NDJSON.
    """
    def __init__(self, filename="opcua_log_polling.ndjson"):
        self.filename = filename

    def log_data(self, nodeid: str, display_name: str, val, variant_type_name: str):
        """
        Chamado para logar um único valor lido por polling.
        """
        try:
            timestamp = time.time()
            
            # Constrói o objeto de log
            log_entry = {
                "timestamp_utc": timestamp,
                "node_id": nodeid,
                "value": val,
                "display_name": display_name,
                "data_type": variant_type_name
            }

            # Escreve a entrada no arquivo NDJSON
            with open(self.filename, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Logged polling data for {nodeid} ({display_name}): {val}")

        except Exception as e:
            print(f"Erro ao processar dados de polling: {e}", file=sys.stderr)


# --- 2. Definição do Logger Principal com Polling ---

class OPCUAPollingLogger:
    """
    Gerencia a conexão OPC UA, mapeamento de variáveis e
    realiza a leitura periódica (polling) das variáveis.
    """
    def __init__(self, server_url, variables_to_monitor, polling_interval_ms=1000):
        self.server_url = server_url
        self.variables_to_monitor = variables_to_monitor
        # O intervalo de amostragem agora é o intervalo de polling
        self.polling_interval_s = polling_interval_ms / 1000.0 
        self.client = None
        self.nodes_to_read = [] # Lista de objetos Node para leitura
        self.node_metadata = {} # {NodeIdStr: {'display_name': '...', 'variant_type_name': '...'}}
        self.logger = PollingLogger()

    def _connect_and_setup(self):
        """
        Conecta ao servidor e mapeia as variáveis.
        """
        print(f"--- Tentando conectar ao servidor OPC UA em: {self.server_url} ---")
        
        # 1. Conexão
        self.client = Client(self.server_url)
        self.client.connect()
        print("✅ Conexão estabelecida com sucesso.")

        # 2. Mapeamento de Variáveis e Coleta de Metadados
        self.nodes_to_read = []
        self.node_metadata = {}
        for node_id_str in self.variables_to_monitor:
            try:
                # Obtém o objeto Node
                node = self.client.get_node(node_id_str)
                display_name = node.get_display_name().Text
                
                # CORREÇÃO AQUI: Usa get_data_value() para garantir que obtemos o ua.Variant completo
                # para que possamos acessar o VariantType sem erros.
                variant = node.get_data_value().Value 
                
                # Verifica se é realmente um ua.Variant antes de tentar acessar VariantType
                if isinstance(variant, ua.Variant):
                    variant_type_name = ua.VariantType(variant.VariantType).name
                else:
                    # Se não for um ua.Variant, tenta inferir ou usa um placeholder
                    variant_type_name = type(variant).__name__.upper()

                self.nodes_to_read.append(node)
                self.node_metadata[node_id_str] = {
                    'display_name': display_name,
                    'variant_type_name': variant_type_name
                }
                print(f"   -> Mapeada variável: {node_id_str} (Display Name: {display_name}, Tipo: {variant_type_name})")
            except Exception as e:
                # A variável pode não existir, ou a conexão caiu, ou houve erro de tipagem.
                print(f"   ❌ Erro ao mapear o Node {node_id_str}: {e}. Pulando este Node.", file=sys.stderr)
        
        if not self.nodes_to_read:
            print("Nenhuma variável válida encontrada para monitorar. Desconectando.", file=sys.stderr)
            self.client.disconnect()
            self.client = None
            raise Exception("Nenhuma variável válida para monitorar.")


    def _read_and_log_values(self):
        """
        Lê os valores de todas as variáveis mapeadas e as loga.
        """
        if not self.nodes_to_read:
            return

        print(f"--- Lendo {len(self.nodes_to_read)} variáveis via Polling ---")
        
        # Lê os valores de todos os nodes de uma vez (leitura otimizada)
        try:
            values = self.client.get_values(self.nodes_to_read)
        except ua.UaError as e:
            # Re-lança exceção UA para que o loop principal tente reconectar
            raise e 
        except Exception as e:
            print(f"Erro inesperado durante a leitura: {e}", file=sys.stderr)
            return

        # Processa e loga cada valor
        for node_obj, val in zip(self.nodes_to_read, values):
            node_id_str = node_obj.nodeid.to_string()
            metadata = self.node_metadata.get(node_id_str, {})
            
            self.logger.log_data(
                node_id_str,
                metadata.get('display_name', 'N/A'),
                val,
                metadata.get('variant_type_name', 'N/A')
            )


    def run(self):
        """Loop principal com lógica de reconexão resiliente e polling."""
        reconnect_delay = 5 # Segundos para esperar antes de tentar reconectar
        
        while True:
            try:
                if self.client is None:
                    # Tenta conectar e configurar os nodes
                    self._connect_and_setup()
                
                if self.client is not None:
                    print(f"Iniciando loop de polling a cada {self.polling_interval_s}s. Pressione Ctrl+C para sair.")
                    
                    while True:
                        start_time = time.time()
                        
                        self._read_and_log_values()
                        
                        # Calcula o tempo para dormir para manter o intervalo fixo
                        elapsed_time = time.time() - start_time
                        sleep_time = self.polling_interval_s - elapsed_time
                        
                        if sleep_time > 0:
                            time.sleep(sleep_time)
                        else:
                            print("⚠️ Aviso: O polling está demorando mais do que o intervalo de polling definido.", file=sys.stderr)
                
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
        if self.client:
            try:
                self.client.disconnect()
                print("Cliente desconectado.")
            except Exception as e:
                print(f"Erro ao desconectar cliente: {e}")
        
        self.client = None
        self.nodes_to_read = []
        self.node_metadata = {}


# --- 3. Execução do Script ---

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
    
    # Intervalo de Leitura (Polling) em milissegundos
    SAMPLING_RATE_MS = 500

    # --------------------
    
    if not NODES_TO_MONITOR:
        print("Por favor, configure a lista NODES_TO_MONITOR com os NodeIds desejados.")
        sys.exit(1)
        
    logger = OPCUAPollingLogger(
        server_url=OPC_SERVER_URL,
        variables_to_monitor=NODES_TO_MONITOR,
        polling_interval_ms=SAMPLING_RATE_MS
    )
    
    logger.run()