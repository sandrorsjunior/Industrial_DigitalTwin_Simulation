from opcua import Client, ua

# --- Configurações ---
URL_SERVIDOR = "opc.tcp://127.0.0.1:4840" 
NODE_ID_VARIAVEL = "ns=4;s=|var|CODESYS Control Win V3 x64.Application.GVL_TRAFFIC.light_red"

def read_node_attributes_safely(client, node_id):
    """Lê e exibe os atributos padrão do nó, ignorando aqueles que falham."""
    
    try:
        variavel_node = client.get_node(node_id)
        print(f"\n--- ATRIBUTOS DIAGNÓSTICO PARA O NÓ: {variavel_node.get_display_name().Text} ---")
        print(f"NodeID: {node_id}\n")
        
        # 1. Nome de Exibição (Geralmente OK)
        print(f"Nome (DisplayName): {variavel_node.get_display_name().Text}")

        # 2. Valor Atual
        try:
            value = variavel_node.get_value()
            print(f"Valor Atual: **{value}** (Tipo Python: {type(value).__name__})")
        except Exception as e:
            print(f"Valor Atual: N/A. FALHA: {e}") # <-- Se falhar aqui, o nó não suporta leitura de valor.

        # 3. Tipo de Dado
        try:
            data_type_node = variavel_node.get_data_type()
            data_type_name = variavel_node.get_browse_name().Name
            print(f"Tipo de Dado (OPC UA): {data_type_name}")
        except Exception as e:
            print(f"Tipo de Dado: N/A. FALHA: {e}")
            print(dir(variavel_node))

        # 4. Nível de Acesso (Crucial para R/W/Subscribe)
        try:
            access_level = variavel_node.get_access_level()
            access_str = str(access_level)
            print(f"Nível de Acesso (R/W/S): {access_str}")
        except Exception as e:
            print(f"Nível de Acesso: N/A. FALHA: {e}")
            print(access_level)

        # 5. Mínimo Intervalo de Amostragem (Relevante para Subscrição)
        try:
            min_sampling_interval = variavel_node.get_minimum_sampling_interval()
            print(f"Min. Intervalo de Amostragem (ms): {min_sampling_interval}")
        except Exception as e:
            print(f"Min. Intervalo de Amostragem: N/A. FALHA: {e}")
            
    except Exception as e:
        print(f"🛑 Erro fatal ao obter o objeto do nó: {e}")


def main():
    client = Client(URL_SERVIDOR)
    try:
        client.connect()
        read_node_attributes_safely(client, NODE_ID_VARIAVEL)
    except Exception as e:
        print(f"Erro de conexão: {e}")
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()