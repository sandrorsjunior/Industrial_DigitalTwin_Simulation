from opcua import Client, Node, ua
import sys

# --- Configurações ---
URL_SERVIDOR = "opc.tcp://127.0.0.1:4840" 
NODE_ID_INICIAL = "ns=4;s=|var|CODESYS Control Win V3 x64.Application" 

# Caracteres usados para desenhar a árvore
LINE_PREFIX = "├── " # Prefixo para o nó atual
LAST_PREFIX = "└── " # Prefixo para o último nó de uma lista
INDENT_STEP = "    " # Espaço para cada nível de profundidade

# --- Função de Navegação Recursiva ---
def browse_and_read(node: Node, depth=0, parent_prefix=""):
    """
    Navega recursivamente, imprime a estrutura em formato de árvore
    e lê o valor das variáveis.
    """
    
    # 1. Obter Nome e Classe
    try:
        display_name = node.get_display_name().Text
    except ua.UaError:
        display_name = str(node.nodeid)
    
    node_class = node.get_node_class()

    # 2. Imprimir o Nó Atual
    prefix = LAST_PREFIX if depth == 0 else LINE_PREFIX
    
    if node_class == ua.NodeClass.Variable:
        try:
            # Tenta ler o valor da variável
            value = node.get_value()
            value_str = f"**{value}** ({type(value).__name__})"
            
            # Formato de Variável: Nome | Valor (Tipo) | [NodeID]
            output = f"VARIÁVEL: {display_name} | Valor: {value_str}"
        except Exception as e:
            # Formato de Erro: Nome | [ERRO] | [NodeID]
            output = f"VARIÁVEL: {display_name} | Erro ao ler: {e}"
        
        # Imprime a linha da variável
        print(f"{parent_prefix}{prefix}{output}")
        # Opcional: imprimir o NodeID da variável abaixo
        print(f"{parent_prefix}{INDENT_STEP}NodeID: {str(node.nodeid)}")

    elif node_class == ua.NodeClass.Object or node_class == ua.NodeClass.Method:
        # Formato de Pasta: Nome (Objeto) | [NodeID]
        output = f"OBJETO/PASTA: {display_name}"
        print(f"{parent_prefix}{prefix}{output}")
        # Opcional: imprimir o NodeID da pasta abaixo
        print(f"{parent_prefix}{INDENT_STEP}NodeID: {str(node.nodeid)}")
        
        # 3. Preparar para Navegar nos Filhos
        try:
            children = node.get_children()
        except Exception as e:
            print(f"{parent_prefix}{INDENT_STEP}Erro ao buscar filhos: {e}")
            return # Sai da recursão se não puder buscar filhos

        # Define o novo prefixo de indentação para os filhos
        # Se este nó não for o último filho do seu pai, a linha vertical continua.
        new_parent_prefix = parent_prefix + (INDENT_STEP if prefix == LINE_PREFIX else "    ")
        
        # 4. Chamar Recursivamente para cada Filho
        for i, child in enumerate(children):
            # Passa o prefixo de indentação atualizado
            browse_and_read(child, depth + 1, new_parent_prefix)


# --- Função Principal ---
def main():
    """Conecta ao servidor OPC UA do Codesys e inicia a leitura."""
    
    client = Client(URL_SERVIDOR)
    
    print(f"\n==========================================================================")
    print(f"       Conectando a {URL_SERVIDOR}...")
    print(f"==========================================================================\n")
    
    try:
        client.connect()
        print("Conexão estabelecida com sucesso! \n")
        
        start_node = client.get_node(NODE_ID_INICIAL)
        print(f"Iniciando a Árvore a partir do nó: {NODE_ID_INICIAL}\n")
        
        # Inicia a navegação (a profundidade inicial é 0)
        browse_and_read(start_node)
        
    except ConnectionRefusedError:
        print(f"\nERRO DE CONEXÃO: O servidor OPC UA no endereço {URL_SERVIDOR} recusou a conexão.")
        print("Verifique se o Codesys SoftPLC está rodando e o servidor OPC UA está ativo.")
    except Exception as e:
        print(f"\nOcorreu um erro: {e}")
        
    finally:
        try:
            client.disconnect()
            print("\n==========================================================================")
            print("Conexão OPC UA fechada.")
            print("==========================================================================")
        except:
            pass 

if __name__ == "__main__":
    main()