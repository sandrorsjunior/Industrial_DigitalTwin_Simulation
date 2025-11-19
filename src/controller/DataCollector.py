import time
import json
import os
import uuid
import datetime
from opcua import Client

# --- 1. CONFIGURAÇÕES OPC UA ---
OPCUA_ENDPOINT = "opc.tcp://127.0.0.2:4840"
NAMESPACE_URI = "http://controle.fabrica.com/ns"

# Diretório base onde os logs serão armazenados
LOGS_BASE_DIR = "factory_io_data_logs" 

class DataCollector:
    """
    Cliente OPC UA que coleta dados periódicos e escreve diretamente no disco
    para evitar memory overflow.
    """

    def __init__(self, endpoint: str = OPCUA_ENDPOINT, namespace_uri: str = NAMESPACE_URI):
        self.client = Client(endpoint)
        self.namespace_uri = namespace_uri
        self.log_session_id = str(uuid.uuid4())
        self.start_time = None
        self.all_opcua_nodes = {}
        self.namespace_idx = 2
        
        # Variáveis para gerenciamento do arquivo
        self.session_dir = None
        self.log_file = None
        self.data_point_count = 0

    def connect(self):
        """Estabelece a conexão, inicializa a sessão no disco e encontra os nós."""
        try:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Tentando conectar a {self.client.server_url}...")
            self.client.connect()
            self.start_time = datetime.datetime.now()
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Conexão estabelecida. Iniciando sessão: {self.log_session_id}")

            # 1. Encontra o índice do Namespace
            self.namespace_idx = self.client.get_namespace_index(self.namespace_uri)
            if self.namespace_idx == 0: self.namespace_idx = 2 
            
            # 2. Preenche o cache de nós
            self._cache_all_nodes()
            
            # 3. Inicializa o arquivo de log no disco
            self._initialize_log_file()
            
            return True

        except Exception as e:
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ❌ ERRO na conexão ou inicialização: {e}")
            self.disconnect()
            return False

    def disconnect(self):
        """Desconecta do Servidor OPC UA."""
        if self.client:
            self.client.disconnect()
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Desconectado do Servidor OPC UA.")

    def _cache_all_nodes(self):
        """Busca e armazena os objetos dos nós OPC UA para leitura rápida."""
        root_data_folder = self.client.get_node(f"0:Objects/{self.namespace_idx}:Linha_Triagem_IIoT")
        
        if not root_data_folder:
            print("❌ ERRO: Pasta raiz 'Linha_Triagem_IIoT' não encontrada.")
            return

        for child in root_data_folder.get_children():
            if child.get_browse_name().Name != 'HasComponent':
                for variable in child.get_children():
                    node_name = variable.get_browse_name().Name
                    self.all_opcua_nodes[node_name] = variable

        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ✅ {len(self.all_opcua_nodes)} variáveis prontas para coleta.")
        
    def _initialize_log_file(self):
        """Cria o diretório único e abre o arquivo de log, escrevendo o colchete inicial '['."""
        self.session_dir = os.path.join(LOGS_BASE_DIR, self.log_session_id)
        os.makedirs(self.session_dir, exist_ok=True)
        
        log_path = os.path.join(self.session_dir, "data_log.json")
        
        # Abre o arquivo para escrita e inicializa o array JSON
        self.log_file = open(log_path, 'w', encoding='utf-8')
        self.log_file.write('[\n')
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Arquivo de log inicializado em: {log_path}")
        
    def collect_and_write(self):
        """Lê os valores dos nós e escreve imediatamente no arquivo de log no disco."""
        
        if not self.all_opcua_nodes:
            # Não faz nada se não houver nós
            return
            
        timestamp_log = datetime.datetime.now().isoformat()
        data_point = {"timestamp": timestamp_log}

        # 1. Coleta os valores
        for name, node in self.all_opcua_nodes.items():
            try:
                value = node.get_value()
                data_point[name] = value
            except Exception:
                data_point[name] = None # Define como None se houver erro de leitura

        # 2. Escreve no disco
        
        # Se for o primeiro ponto de dados, não precisa da vírgula inicial
        if self.data_point_count > 0:
            self.log_file.write(',\n')
            
        # Escreve o objeto JSON no arquivo
        json.dump(data_point, self.log_file)
        
        self.log_file.flush() # Força a escrita no disco
        self.data_point_count += 1

    def start_logging(self, interval_seconds=1.0):
        """Inicia o loop de coleta de dados."""
        if not self.start_time or not self.log_file:
            print("❌ ERRO: Cliente não conectado ou arquivo de log não inicializado.")
            return

        print(f"\n--- INICIANDO DATALOGGER (Intervalo: {interval_seconds}s) ---")
        try:
            while True:
                self.collect_and_write()
                print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Coletado e escrito ponto de dados #{self.data_point_count}.")
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            print("\n--- DATALOGGER ENCERRADO POR INTERRUPÇÃO DO USUÁRIO ---")
        except Exception as e:
            print(f"\n--- DATALOGGER ENCERRADO POR ERRO: {e} ---")
            
        finally:
            self.finalize_log_to_disk()
            self.disconnect()

    def finalize_log_to_disk(self):
        """Fecha o array JSON no arquivo de log e cria o arquivo de metadados."""
        
        end_time = datetime.datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        if self.log_file:
            # 1. Fecha o array JSON no arquivo de log
            self.log_file.write('\n]')
            self.log_file.close()
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Arquivo de log JSON finalizado e fechado.")
        
        # 2. Cria o arquivo de Metadados
        metadata = {
            "session_id": self.log_session_id,
            "start_timestamp": self.start_time.isoformat(),
            "end_timestamp": end_time.isoformat(),
            "duration_seconds": round(duration, 2),
            "total_data_points": self.data_point_count,
            "opcua_endpoint": OPCUA_ENDPOINT,
            "opcua_namespace": self.namespace_uri,
            "notes": "Log de dados coletados do Gêmeo Digital Factory I/O/CODESYS."
        }
        
        metadata_path = os.path.join(self.session_dir, "metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4)
            
        print("\n" + "="*60)
        print("✅ LOG SALVO COM SUCESSO (Escrita direta no disco)")
        print(f"ID da Sessão: {self.log_session_id}")
        print(f"Local do Log: {self.session_dir}")
        print(f"Duração: {round(duration, 2)} segundos. Pontos: {self.data_point_count}")
        print("="*60)


# --- EXECUÇÃO PRINCIPAL ---
if __name__ == "__main__":
    
    # 1. Instancia e conecta o coletor
    collector = DataCollector()
    
    if collector.connect():
        # 2. Inicia o logging (coleta a cada 1.0 segundos)
        # O loop continua até ser interrompido (Ctrl+C)
        collector.start_logging(interval_seconds=1.0) 
        
    else:
        print("\nNão foi possível iniciar o log. Verifique se o Servidor OPC UA está rodando.")