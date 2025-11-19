import time
from opcua import Client

# --- 1. CONFIGURAÇÕES OPC UA ---
OPCUA_ENDPOINT = "opc.tcp://127.0.0.2:4840"
NAMESPACE_URI = "http://controle.fabrica.com/ns"
# O caminho do nó que controla o tipo de peça (baseado na estrutura do Servidor anterior)
EMITTER_PART_NODE_PATH = "0:Objects/{}:Linha_Triagem_IIoT/IOs_Atuadores_Fisicos/Emitter_0_Part"

class EmitterController:
    """
    Controlador Cliente OPC UA para definir o tipo de peça a ser emitida
    pelo Emitter 0 no Factory I/O.
    """

    # Mapeamento do Factory I/O (Emitter > Options)
    PART_TYPES = {
        "SMALL_BOX": 0,
        "BOX": 1,
        "PLASTIC_CONTAINER": 2,
        "WOODEN_PALLET": 3,
        "BARREL": 4
    }

    def __init__(self, endpoint: str = OPCUA_ENDPOINT, namespace_uri: str = NAMESPACE_URI):
        self.client = Client(endpoint)
        self.namespace_uri = namespace_uri
        self.emitter_part_node = None
        self.namespace_idx = -1

    def connect(self):
        """Estabelece a conexão com o Servidor OPC UA e encontra o nó."""
        try:
            print(f"Conectando a {self.client.server_url}...")
            self.client.connect()
            print("Conexão estabelecida com sucesso.")

            # 1. Encontrar o índice do Namespace
            self.namespace_idx = self.client.get_namespace_index(self.namespace_uri)
            if self.namespace_idx == 0:
                 # Se for 0, geralmente é o default OPC UA. Tenta o índice 2 (comum para namespaces customizados)
                 self.namespace_idx = 2 
            
            # 2. Construir o caminho completo do nó e obtê-lo
            node_path = EMITTER_PART_NODE_PATH.format(self.namespace_idx)
            self.emitter_part_node = self.client.get_node(node_path)
            
            if self.emitter_part_node:
                print(f"Nó do Emitter Part encontrado: {node_path}")
            else:
                print(f"ERRO: Nó do Emitter Part não encontrado no caminho: {node_path}")

        except Exception as e:
            print(f"Falha na conexão ou na busca do nó: {e}")
            self.disconnect()

    def disconnect(self):
        """Desconecta do Servidor OPC UA."""
        if self.client:
            self.client.disconnect()
            print("Desconectado do Servidor OPC UA.")

    def set_part_type(self, part_name: str):
        """
        Define o tipo de peça a ser emitido no Factory I/O.
        
        Args:
            part_name: O nome da peça (Ex: 'SMALL_BOX', 'BOX').
        """
        if not self.emitter_part_node:
            print("ERRO: Cliente não conectado ou nó não encontrado.")
            return

        part_name = part_name.upper().replace(' ', '_')
        
        if part_name not in self.PART_TYPES:
            print(f"ERRO: Tipo de peça '{part_name}' inválido.")
            print(f"Tipos válidos são: {list(self.PART_TYPES.keys())}")
            return

        part_value = self.PART_TYPES[part_name]
        
        try:
            # Escreve o valor numérico no nó do atuador
            self.emitter_part_node.set_value(part_value)
            print(f"Comando enviado: Definido o Emitter Part como '{part_name}' ({part_value}).")
            
        except Exception as e:
            print(f"Falha ao escrever no nó OPC UA: {e}")

# --- 2. EXEMPLO DE USO ---
if __name__ == "__main__":
    controller = EmitterController()
    controller.connect()

    if controller.emitter_part_node:
        try:
            print("\n--- Teste de Alteração de Peça ---")
            
            # 1. Tenta definir para Caixa Média (Valor 1)
            controller.set_part_type("BOX")
            time.sleep(3)
            
            # 2. Tenta definir para Contêiner Plástico (Valor 2)
            controller.set_part_type("PLASTIC_CONTAINER")
            time.sleep(3)
            
            # 3. Tenta definir para Pallet de Madeira (Valor 3)
            controller.set_part_type("WOODEN_PALLET")
            time.sleep(3)

        except KeyboardInterrupt:
            print("\nOperação interrompida pelo usuário.")
            
        finally:
            # 4. Retorna para o valor padrão (Caixa Pequena)
            controller.set_part_type("SMALL_BOX")
            
    controller.disconnect()