import time
from opcua import Client, ua

# --- 1. CONFIGURAÇÕES OPC UA ---
OPCUA_ENDPOINT = "opc.tcp://127.0.0.2:4840"
NAMESPACE_URI = "http://controle.fabrica.com/ns"
NAMESPACE_IDX = 2 

# Variável para armazenar o log (Ainda precisa de lógica de escrita em arquivo)
GLOBAL_LOG_DATA = []

# --- 2. HANDLER DO SUBSCRIBER ---
class DataChangeHandler:
    """
    Manipulador que é chamado pelo cliente OPC UA sempre que um valor de 
    um nó monitorado muda no servidor.
    """
    def __init__(self, log_list):
        self.log_list = log_list
        
    def datachange_notification(self, node, val, data):
        """
        Método chamado quando há uma mudança de dados.
        
        Args:
            node: Objeto do nó que mudou.
            val: O novo valor do nó.
            data: Informações adicionais (incluindo timestamps do servidor).
        """
        node_name = node.get_browse_name().Name
        
        # Cria o ponto de log
        log_entry = {
            "timestamp_local": datetime.datetime.now().isoformat(),
            "node": node_name,
            "value": val,
            "source_timestamp": data.monitored_item.value.SourceTimestamp.isoformat()
        }
        
        # Neste ponto, você escreveria log_entry no disco (JSON/CSV)
        # Para este exemplo, apenas imprime e usa uma lista global
        print(f"[{log_entry['timestamp_local']}] 🔔 MUDANÇA RECEBIDA: {node_name} = {val}")
        self.log_list.append(log_entry)


# --- 3. IMPLEMENTAÇÃO DO CLIENTE COM SUBSCRIPTION ---
def run_subscriber():
    client = Client(OPCUA_ENDPOINT)
    try:
        client.connect()
        idx = client.get_namespace_index(NAMESPACE_URI)
        if idx == 0: idx = NAMESPACE_IDX
        
        # Define o Handler
        handler = DataChangeHandler(GLOBAL_LOG_DATA)
        
        # Cria a Subscription (Ex: Intervalo de 500ms para verificar mudanças)
        subscription = client.create_subscription(500, handler)
        
        # --- Nós para monitorar ---
        
        # Ex: Contadores (Lógica)
        c_total_node = client.get_node(f"0:Objects/{idx}:Linha_Triagem_IIoT/Contadores_PLC/C_TOTAL")
        
        # Ex: Sensor Difuso (Inspeção)
        diffuse_sensor_node = client.get_node(f"0:Objects/{idx}:Linha_Triagem_IIoT/IOs_Sensores_Fisicos/Diffuse_Sensor_0")
        
        # Ex: Luz Vermelha (Sinalização)
        sl_red_node = client.get_node(f"0:Objects/{idx}:Linha_Triagem_IIoT/IOs_Atuadores_Fisicos/Stack_Light_0_Red")
        
        # --- Anexa os nós à Subscription ---
        
        # monitor_items(nós, atributos)
        # O deadband (diferença mínima para notificar) deve ser ajustado para cada nó.
        # Para booleanos (sensores/luzes), deadband 0 (qualquer mudança notifica).
        
        subscription.subscribe_data_change(c_total_node)
        subscription.subscribe_data_change(diffuse_sensor_node)
        subscription.subscribe_data_change(sl_red_node)
        
        print("\nCliente Subscribed. Aguardando notificações do Servidor...")
        
        # Mantém o programa rodando para receber as notificações
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nInterrupção. Encerrando Subscription...")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
    finally:
        client.disconnect()
        print("Desconectado e encerrado.")

if __name__ == "__main.__":
    import datetime
    run_subscriber()