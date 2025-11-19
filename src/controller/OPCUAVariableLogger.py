import time
import json
from opcua import ua


class OPCUAVariableLogger:
    """
    Monitora variáveis OPC UA e salva mudanças no formato NDJSON.
    Cada linha do arquivo é um JSON independente.
    """

    def __init__(self, server, output_file="log_variaveis.ndjson"):
        self.server = server
        self.output_file = output_file
        self.variable_nodes = []
        self.last_values = {}

    def _collect_all_variables(self):
        """Coleta todos os nós de variáveis existentes no servidor."""
        root = self.server.get_objects_node()

        # Busca profunda (3 níveis é suficiente para sua estrutura)
        nodes_to_scan = [root]
        for node in root.get_children():
            nodes_to_scan.append(node)
            for sub in node.get_children():
                nodes_to_scan.append(sub)
                for sub2 in sub.get_children():
                    nodes_to_scan.append(sub2)

        # Filtrar apenas nós de variáveis
        var_nodes = []
        for node in nodes_to_scan:
            try:
                var_nodes.extend(node.get_variables())
            except:
                pass

        self.variable_nodes = var_nodes

    def _save_ndjson(self, record: dict):
        """Salva uma linha NDJSON no arquivo."""
        with open(self.output_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def start(self, interval=0.1):
        """
        Inicia o monitoramento e salva alterações.
        'interval' define o tempo entre leituras (em segundos).
        """
        self._collect_all_variables()

        print(f"[LOGGER] Monitorando {len(self.variable_nodes)} variáveis OPC UA...")
        print(f"[LOGGER] Salvando alterações em {self.output_file}\n")

        # Registrar valores iniciais
        for var in self.variable_nodes:
            try:
                name = var.get_browse_name().Name
                self.last_values[name] = var.get_value()
            except:
                pass

        # Loop principal
        while True:
            for var in self.variable_nodes:
                try:
                    name = var.get_browse_name().Name
                    current = var.get_value()
                    previous = self.last_values.get(name)

                    # Detectar mudança
                    if current != previous:
                        record = {
                            "timestamp": time.time(),
                            "timestamp_readable": time.strftime("%Y-%m-%d %H:%M:%S"),
                            "variable": name,
                            "old_value": previous,
                            "new_value": current
                        }

                        self._save_ndjson(record)
                        print(f"[LOG] {name}: {previous} -> {current}")

                        self.last_values[name] = current

                except Exception as e:
                    print(f"[LOGGER] Erro ao ler variável: {e}")

            time.sleep(interval)
