# 🏭 GÊMEO DIGITAL INDUSTRIAL E PIPELINE DE DADOS (IIoT)

## 🚀 VISÃO GERAL DO PROJETO

Este projeto pessoal simula um ambiente de manufatura baseado no conceito da **Indústria 4.0**, com foco na **Linha de Inspeção e Triagem Automatizada** desenvolvida. O objetivo é interconectar tecnologias para criar uma cadeia completa de **IIoT (Industrial Internet of Things)**: desde a simulação física até a análise de dados na nuvem.

O **Python** atua como o motor de variabilidade (ou *variability engine*), simulando condições reais de fábrica (erros de qualidade, falhas de equipamento, flutuações de volume) através de distribuições estatísticas controladas, injetando essa "realidade" no controle do processo.

---

## 🛠️ TECNOLOGIAS E FERRAMENTAS

A integração dessas ferramentas estabelece uma ponte entre o chão de fábrica digital e o ecossistema de dados na nuvem:

| Categoria | Ferramenta | Função no Projeto |
| :--- | :--- | :--- |
| **Simulação Física** | **Factory I/O** | Simulação visual da linha de Inspeção e Triagem. |
| **Controle (SoftPLC)** | **CODESYS** | Implementação da lógica de controle (Triagem, Contagem) e exposição dos dados via OPC UA Server. |
| **Comunicação** | **OPC UA** | Protocolo de comunicação entre o Python (Cliente) e o CODESYS (Servidor). |
| **Orquestração** | **Python** | Cliente OPC UA, gerador de dados estatísticos (variabilidade) e Datalogger. |
| **Ingestão/Armazenamento** | **Azure Cloud** | IoT Hub e Azure Storage Account para recepção e armazenamento de dados brutos. |
| **Processamento/Análise** | **Azure Databricks** | Transformação (ETL/ELT), enriquecimento de dados e cálculo de KPIs (Ex: OEE, Taxa de Rejeição). |
| **Visualização** | **Power BI** | Criação de dashboards para monitoramento em tempo real dos KPIs de produção simulada. |

---

## 📊 SIMULAÇÃO DE VARIABILIDADE ESTRUTURADA

O script Python é central para a simulação da "realidade" industrial, aplicando distribuições estatísticas para variáveis que influenciam a linha de triagem:

| Variável Simulada | Aplicação no Cenário da Linha | Distribuição Estatística |
| :--- | :--- | :--- |
| **Estado do Sensor/Qualidade** | Varia a frequência de peças que falham na inspeção (peças defeituosas). | Normal (Gaussiana) |
| **Tempo para Falha (MTBF)** | Simula falhas de componentes chave, como o motor do transportador. | Exponencial / Weibull |
| **Volume de Produção** | Altera a taxa de geração de peças pelo Emissor (`Emitter`). | Uniforme |

---

## 🗺️ FLUXO COMPLETO DO PIPELINE DE DADOS

O pipeline representa a jornada do dado, do chão de fábrica (simulado) até o painel de análise:

1.  **Geração e Controle (Factory I/O / CODESYS):** O processo físico simula a contagem ($C\_TOTAL, C\_APROVADAS$) e o controle do Pistão de Rejeição, expondo todas as variáveis via OPC UA Server.

2.  **Leitura e Injeção (Python):** O Cliente OPC UA em Python **lê** os dados do controle (Contadores) e **escreve** as variáveis estatísticas geradas, forçando a ocorrência de falhas e erros de qualidade.

3.  **Coleta e Ingestão (Datalogger):** O Datalogger (Python) coleta os dados brutos e os envia em tempo real para a **Azure Cloud** (IoT Hub).

4.  **Processamento e Enriquecimento (Azure Databricks):** Os dados são limpos e transformados. O Databricks calcula métricas avançadas (OEE, Produtividade, Taxa de Rejeição) e armazena o resultado no **Delta Lake**.

5.  **Análise e Tomada de Decisão (Power BI):** O Power BI se conecta ao Delta Lake para fornecer dashboards de monitoramento e relatórios analíticos, completando o ciclo do Gêmeo Digital.