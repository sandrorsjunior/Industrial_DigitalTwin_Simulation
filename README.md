# 🏭 Industrial Digital Twin Simulation and Data Pipeline

## Project Overview

This personal project aims to simulate a complete manufacturing environment within the **Industry 4.0** context, integrating process simulation, real-time control, statistical data orchestration, and cloud-based analysis. The main objective is to study the interconnection of the following technologies:

* **Control and Simulation:** Factory I/O & CODESYS (SoftPLC).
* **Industrial Communication:** OPC UA (Client/Server).
* **Orchestration and Statistics:** Python (Statistical Distribution Generation).
* **Cloud and Analytics:** Azure Cloud, Databricks, and Power BI.

The project establishes a comprehensive **IIoT (Industrial Internet of Things)** chain, where Python acts as the variability engine, simulating real-world conditions like equipment failures, quality deviations (part errors), and production volume fluctuations through controlled statistical distributions.

---

## 🛠️ Technologies and Tools

| Category | Tool | Project Function |
| :--- | :--- | :--- |
| **Simulation** | Factory I/O | Visual and real-time simulation of the production line. |
| **Control** | CODESYS | SoftPLC for controlling Factory I/O I/Os via an OPC UA Server. |
| **Orchestration** | Python | OPC UA Client, statistical distribution generator (numpy), and Datalogger. |
| **Communication** | OPC UA | Communication protocol between Python and CODESYS. |
| **Ingestion/Storage** | Azure Cloud | Azure Storage Account / IoT Hub for receiving and storing raw data. |
| **Processing/Analysis** | Azure Databricks | Cleaning, transformation (OEE calculation), and data enrichment. |
| **Visualization** | Power BI | Creation of dashboards for monitoring simulated production KPIs (Key Performance Indicators). |

---

## 📊 Data Generation Structure (Python)

The core Python script centralizes the generation of the simulated industrial "reality" by applying different statistical distributions to key variables, which are then injected into CODESYS via OPC UA.

| Simulated Variable (Example) | Statistical Distribution | Objective |
| :--- | :--- | :--- |
| Quality Error | Normal (Gaussian) | Simulating dimensional tolerances and deviations in parts. |
| Time to Failure | Exponential / Weibull | Simulating equipment MTBF (Mean Time Between Failures). |
| Production Volume | Uniform | Simulating random variations in demand or raw material feeding rate. |

---

## 🗺️ Data Pipeline Flow

1.  **Factory I/O / CODESYS:** Process simulation and control, exposing data via the **OPC UA Server**.
2.  **Python Script:** OPC UA Client, which **reads** sensor data and **writes** the statistically generated variables for control.
3.  **Datalogger (Python):** Collects raw data and sends it to **Azure Cloud**.
4.  **Azure Databricks:** Processing (ETL/ELT) of raw data and storage in **Delta Lake**.
5.  **Power BI:** Connects to the Delta Lake for visualization and KPI monitoring.