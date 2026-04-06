# 🔧 NetFix AI
### AI-Powered Network Troubleshooting Assistant for Telecom R&D Labs
 
> Conversational AI agent that diagnoses network failures, identifies root causes, and recommends remediation — in under 60 seconds.
 
---
 
## Overview
 
NetFix AI is a RAG-based network operations assistant built for telecom R&D lab environments. Engineers can query the system in natural language to get evidence-backed root cause analysis, remediation steps, and historical incident correlation across multiple lab networks.
 
**Built for:** Major US Telecom Operator | R&D Network Lab Division  
**Domain:** Generative AI × Network Operations × Telecom Engineering
 
---
 
## Features
 
| Feature | Description |
|---|---|
| Natural Language RCA | Ask questions in plain English, get structured root cause analysis |
| Multi-Source Ingestion | Syslogs, SNMP metrics, device inventory, topology, incident tickets |
| Evidence Citation | Every claim cites exact log lines, timestamps, and metric values |
| Historical Correlation | Matches current symptoms against past incidents automatically |
| Interactive Topology Map | Live network graph with color-coded device status |
| Predictive Alerting | Detects metric trends before they hit critical thresholds |
| Knowledge Base Builder | Save resolved incidents for future correlation |
| Runbook Generator | Auto-generates downloadable PDF runbooks for any incident |
| Multi-turn Conversation | Full session memory with chat history |
| NOC Dashboard | Real-time network operations center view |
 
---
 
## Tech Stack
 
| Layer | Technology |
|---|---|
| LLM | Groq (Llama 3.3 70B) — free tier |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) — local |
| Vector DB | ChromaDB — local persistent |
| Metrics Store | SQLite + Pandas |
| Orchestration | LangChain |
| Topology Viz | PyVis |
| UI | Streamlit |
| PDF Generation | ReportLab |
 
---
 
## Project Structure
 
```
NetFixAI/
├── app.py                      # NOC Dashboard (main landing page)
├── pages/
│   └── chat.py                 # AI Chat Interface
├── src/
│   ├── ingest.py               # Data ingestion pipeline
│   ├── tools.py                # semantic_search + metrics_query tools
│   ├── agent.py                # Groq LLM agent + conversation memory
│   ├── topology_viz.py         # PyVis interactive topology map
│   ├── predictor.py            # Predictive failure alerting
│   ├── knowledge_base.py       # KB save/search/retrieve
│   └── runbook_generator.py    # PDF runbook generator
├── data/
│   ├── router_syslog.log       # Syslog events
│   ├── device_inventory.csv    # Device metadata
│   ├── network_topology.json   # Network links and BGP peers
│   ├── snmp_metrics.csv        # SNMP time-series metrics
│   ├── incident_tickets.json   # Historical incident tickets
│   └── knowledge_base.json     # Auto-generated KB (created at runtime)
├── chroma_db/                  # Vector store (auto-created)
├── netfix_metrics.db           # SQLite metrics DB (auto-created)
├── .env                        # API keys
├── requirements.txt
└── README.md
```
 
---
 
## Setup & Installation
 
### Prerequisites
- Python 3.11
- Groq API key (free at [groq.com](https://groq.com))
 
### 1. Clone the repository
```bash
git clone https://github.com/yourusername/NetFixAI.git
cd NetFixAI
```
 
### 2. Create virtual environment
```bash
py -3.11 -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```
 
### 3. Install dependencies
```bash
pip install -r requirements.txt
```
 
### 4. Configure environment
Create a `.env` file in the root directory:
```
GROQ_API_KEY=your_groq_api_key_here
```
 
### 5. Ingest data
```bash
python src/ingest.py
```
Expected output: `Done! All data ingested successfully. Total documents in ChromaDB: 68`
 
### 6. Run the app
```bash
streamlit run app.py
```
 
Open `http://localhost:8501` in your browser.
 
---
 
## Sample Queries
 
```
What happened to ROUTER-LAB-01 between 08:10 and 08:20?
Why did the BGP session with peer 10.0.0.3 drop?
What is the blast radius of the 5G UPF crash?
Has this type of CPU spike and BGP drop happened before?
What are the fix commands for BGP hold timer expiry on Cisco IOS-XE?
Give me a summary of all open P1 incidents
Which devices in NET-LAB-ALPHA are in WARNING or CRITICAL state?
```
 
---
 
## Benchmark Results (10/10 Queries)
 
All 10 evaluation queries pass with evidence-backed responses:
 
| Query | Result |
|---|---|
| Root cause of ROUTER-LAB-01 incident | ✅ PASS |
| BGP session drop reason | ✅ PASS |
| WARNING/CRITICAL device list | ✅ PASS |
| SW-LAB-02 blast radius | ✅ PASS |
| Software version mismatch detection | ✅ PASS |
| Historical BGP incident correlation | ✅ PASS |
| Cisco IOS-XE BGP remediation commands | ✅ PASS |
| CRITICAL syslog event extraction | ✅ PASS |
| 5G UPF crash blast radius | ✅ PASS |
| Open P1 incident summary | ✅ PASS |
 
---
 
## Lab Networks Monitored
 
| Network | Purpose | Devices |
|---|---|---|
| NET-LAB-ALPHA | IP routing & feature development | 9 devices |
| NET-LAB-BETA | Regression testing | 2 devices |
| NET-LAB-5G | 5G core & slicing validation | 4 devices |
 
---
 
 
## Requirements
 
```
langchain
langchain-groq
chromadb
streamlit
pandas
sentence-transformers
networkx
groq
pyvis
python-dotenv
reportlab
numpy
```
 
---
 
## Important Notes
 
- All sample data is synthetic — no real telecom network required
- Never commit your `.env` file to GitHub
- Always verify AI-generated CLI commands with a senior engineer before execution
- The system reasons from provided data files, not generic LLM knowledge
 
---
 
## License
 
For educational and demonstration purposes only.
 
---
 
*Built with ❤️ for the Student Design & Development Challenge*
