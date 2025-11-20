import random
import math
from typing import Dict, Any, Tuple, Optional

class BoxCompetitor:
    """
    Simula a competição entre tipos de caixas, onde cada tipo "compete" 
    gerando um valor entre 0 e 1 usando uma distribuição estatística.
    O tipo de caixa com o maior valor é o vencedor.
    """

    PART_TYPES: Dict[str, int] = {
        "SMALL_BOX": 1,
        "MEDIUM_BOX": 2,
        "LARGE_BOX": 4,
        "PALLETIZING_BOX": 8,
        "BLUE_RAW_MATERIAL": 16,
        "GREEN_RAW_MATERIAL": 32,
        "METAL_RAW_MATERIAL": 64,
        "BLUE_PRODUCT_BASE": 128,
        "GREEN_PRODUCT_BASE": 256,
        "METAL_PRODUCT_BASE": 512,
        "BLUE_PRODUCT_LID": 1024,
        "GREEN_PRODUCT_LID": 2048,
        "METAL_PRODUCT_LID": 4096,
        "STACKABLE_BOX": 8192,
    }

    # CORREÇÃO: "EXPONENCIAL" alterado para "EXPONENTIAL"
    DISTRIBUTION_GROUPS: Dict[str, list[str]] = {
        "EXPONENTIAL": [ 
            "SMALL_BOX", "MEDIUM_BOX", "LARGE_BOX", "PALLETIZING_BOX"
        ],
        "POISSON": [
            "BLUE_RAW_MATERIAL", "GREEN_RAW_MATERIAL", "METAL_RAW_MATERIAL", "BLUE_PRODUCT_BASE"
        ],
        "WEIBULL": [
            "GREEN_PRODUCT_BASE", "METAL_PRODUCT_BASE", "BLUE_PRODUCT_LID"
        ],
        "NORMAL": [
            "GREEN_PRODUCT_LID", "METAL_PRODUCT_LID", "STACKABLE_BOX"
        ],
    }
    
    # CORREÇÃO: "EXPONENCIAL" alterado para "EXPONENTIAL"
    DISTRIBUTION_PARAMS: Dict[str, Dict[str, float]] = {
        "EXPONENTIAL": {"lambda": 5.0}, 
        "POISSON": {"lambda": 2.0},
        "WEIBULL": {"alpha": 1.5, "beta": 1.0},
        "NORMAL": {"mu": 0.5, "sigma": 0.2},
    }

    def _generate_exponential(self, part_name: str) -> float:
        """ Gera um valor da distribuição exponencial e o escalona para [0, 1]. """
        # CORREÇÃO: Acessa o parâmetro usando a chave "EXPONENTIAL"
        lambd = self.DISTRIBUTION_PARAMS["EXPONENTIAL"]["lambda"]
        
        value = random.expovariate(lambd)
        result = math.exp(-lambd * value) 
        return result

    def _generate_poisson(self, part_name: str) -> float:
        """ Gera um valor da distribuição de Poisson e o escalona para [0, 1]. """
        lambd = self.DISTRIBUTION_PARAMS["POISSON"]["lambda"]
        
        k = random.randint(0, 5) 
        
        # Calculamos a PMF do número k gerado
        pmf = (lambd**k * math.exp(-lambd)) / math.factorial(k)
        
        return pmf
    
    def _generate_weibull(self, part_name: str) -> float:
        """ Gera um valor da distribuição de Weibull e o escalona para [0, 1]. """
        alpha = self.DISTRIBUTION_PARAMS["WEIBULL"]["alpha"]
        beta = self.DISTRIBUTION_PARAMS["WEIBULL"]["beta"]
        
        value = random.weibullvariate(alpha=alpha, beta=beta)
        
        cdf = 1 - math.exp(-((value / beta)**alpha))
        return min(cdf, 1.0) 

    def _generate_normal(self, part_name: str) -> float:
        """ Gera um valor da distribuição normal e o trunca/escalona para [0, 1]. """
        mu = self.DISTRIBUTION_PARAMS["NORMAL"]["mu"]
        sigma = self.DISTRIBUTION_PARAMS["NORMAL"]["sigma"]
        
        value = random.gauss(mu=mu, sigma=sigma)
        
        return max(0.0, min(1.0, value)) 

    def run_competition(self) -> Tuple[str, float, str, Dict[str, float]]:
        """
        Executa a competição, gerando um valor para cada PART_TYPE e 
        determinando o vencedor.
        
        :return: Uma tupla contendo (part_vencedora, valor_vencedor, distribuicao_vencedora, resultados_detalhados)
        """
        results: Dict[str, float] = {}
        
        generation_map: Dict[str, callable] = {}
        for dist_type, parts in self.DISTRIBUTION_GROUPS.items():
            # dist_type.lower() agora será "exponential" (correto)
            generator = getattr(self, f"_generate_{dist_type.lower()}") 
            for part in parts:
                generation_map[part] = generator
        
        # 1. Gerar o número para cada PART_TYPE
        for part_name, generator in generation_map.items():
            generated_value = generator(part_name)
            results[part_name] = generated_value

        # 2. Avaliar o maior número gerado (o vencedor)
        if not results:
            raise ValueError("Nenhuma peça configurada para competição.")
            
        winner_part = max(results, key=results.get)
        winner_value = results[winner_part]
        
        # 3. Determinar a distribuição do vencedor
        winner_distribution = ""
        for dist_type, parts in self.DISTRIBUTION_GROUPS.items():
            if winner_part in parts:
                winner_distribution = dist_type
                break

        return winner_part, winner_value, winner_distribution, results


# --- Exemplo de Uso ---
print("## 🚀 Início da Competição de Peças\n")

# Instancia a classe
competitor = BoxCompetitor()

# Executa o processo de competição
vencedor, valor, distribuicao, todos_resultados = competitor.run_competition()

# --- Apresentação dos Resultados ---
print("### 🥇 Resultado da Rodada")
print(f"**Caixa Vencedora:** {vencedor}")
print(f"**Valor Vencedor:** {valor:.6f}")
print(f"**Distribuição Vencedora:** {distribuicao}\n")

print("---")

print("### 📈 Detalhes dos Resultados Gerados (TOP 5)")
# Ordenar os resultados do maior para o menor
sorted_results = sorted(todos_resultados.items(), key=lambda item: item[1], reverse=True)

# Imprimir os 5 primeiros
for i, (part, value) in enumerate(sorted_results[:5]):
    dist = ""
    for d, parts in competitor.DISTRIBUTION_GROUPS.items():
        if part in parts:
            dist = d
            break
    print(f"* **{i+1}. {part}** ({dist}): {value:.6f}")
    
if len(sorted_results) > 5:
    print("\n* ... (Demais resultados omitidos) ...")