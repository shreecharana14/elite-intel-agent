# 🧠 Elite Intel Agent

> **The AI system that filters the world's information like the top 1% do — and delivers it straight to your Telegram or WhatsApp.**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Ollama](https://img.shields.io/badge/LLM-Ollama-green)](https://ollama.ai)
[![CrewAI](https://img.shields.io/badge/Agents-CrewAI-orange)](https://crewai.com)
[![ChromaDB](https://img.shields.io/badge/Memory-ChromaDB-purple)](https://trychroma.com)

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ELITE INTEL AGENT                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📡 DATA INGESTION LAYER (20+ Sources)                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │ RSS/News │ │Financial │ │ Patents  │ │Regulatory│ │ Social   │ │
│  │ Feeds    │ │ Signals  │ │ Monitor  │ │ Filings  │ │ Signals  │ │
│  │(50+ RSS) │ │(yfinance)│ │(USPTO/EP)│ │(SEC/EU)  │ │(Reddit)  │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ │
│       └────────────┴────────────┴────────────┴────────────┘        │
│                              │                                      │
│  🤖 MULTI-AGENT LAYER (CrewAI + Ollama)                             │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  ResearchAgent → SignalAgent → SynthesisAgent → LearningAgent│  │
│  │  (Gather)       (Filter/Score) (Summarize)    (Self-Improve) │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
│  🧠 MEMORY LAYER (ChromaDB + SQLite)                                │
│  ┌──────────────┐  ┌─────────────────┐  ┌──────────────────────┐  │
│  │ Vector Store │  │  Knowledge Base │  │  Feedback & Learning │  │
│  │ (Embeddings) │  │  (Past Insights)│  │  (User Preferences)  │  │
│  └──────────────┘  └─────────────────┘  └──────────────────────┘  │
│                              │                                      │
│  📲 DELIVERY LAYER                                                  │
│  ┌───────────────────┐      ┌───────────────────────────────────┐  │
│  │   Telegram Bot    │      │         WhatsApp Bot              │  │
│  │  (Commands +      │      │  (Twilio/Meta Business API)       │  │
│  │   Reactions)      │      │                                   │  │
│  └───────────────────┘      └───────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🎯 What It Does

| Feature | Description |
|---|---|
| **20+ Source Ingestion** | RSS feeds, financial data, patents, SEC filings, Reddit, job boards |
| **AI Signal Scoring** | Each piece of information is scored 0–100 for signal strength |
| **Multi-Agent Synthesis** | 4 specialized agents collaborate to find insights the 99% miss |
| **Self-Learning** | Learns YOUR preferences from your feedback via Telegram reactions |
| **Memory** | Never repeats the same insight twice; tracks trends over time |
| **Delivery** | Sends formatted, actionable briefs to Telegram + WhatsApp |
| **Local-First** | Runs fully on your Mac via Ollama — no data leaves your machine |

---

## 🧬 The 4 Agents

### 1. 🔍 ResearchAgent
Crawls and ingests raw data from all configured sources every N minutes.
- Fetches RSS, scrapes web, calls APIs
- Deduplicates against memory
- Tags by domain (finance, AI, geo-political, biotech, etc.)

### 2. 📊 SignalAgent
Scores every piece of content for elite relevance:
- **Velocity**: Is this trend accelerating?
- **Asymmetry**: Does 99% of the public NOT know this yet?
- **Actionability**: Can a decision be made on this?
- **Pattern Match**: Does this connect to previously tracked signals?

### 3. 🧩 SynthesisAgent
Takes the top-scored signals and builds a narrative:
- Connects dots across unrelated domains
- Identifies "second-order" implications
- Formats as an elite intelligence brief

### 4. 🔄 LearningAgent
Processes your feedback (👍👎 reactions in Telegram) to:
- Update your preference profile
- Retrain the scoring weights
- Add new source recommendations
- Prune irrelevant categories

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) installed and running
- Docker + Docker Compose (optional)
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- WhatsApp Business API or Twilio account (optional)

### 1. Clone & Install
```bash
git clone https://github.com/shreecharana14/elite-intel-agent.git
cd elite-intel-agent
pip install -r requirements.txt
```

### 2. Pull Ollama Models
```bash
ollama pull llama3.1:8b        # Fast reasoning
ollama pull nomic-embed-text   # Embeddings for ChromaDB
```

### 3. Configure
```bash
cp .env.example .env
# Edit .env with your API keys and Telegram token
```

### 4. Run
```bash
python main.py
```

### Or with Docker
```bash
docker-compose up -d
```

---

## 📲 Telegram Commands

| Command | Description |
|---|---|
| `/start` | Start receiving intelligence briefs |
| `/brief` | Get an immediate intelligence brief |
| `/sources` | Show active data sources |
| `/focus [topic]` | Focus on a specific domain |
| `/frequency [mins]` | Set delivery frequency |
| `/feedback` | Review and rate recent insights |
| `/stats` | Show system learning stats |
| `/pause` | Pause delivery |

**React with 👍 (good signal) or 👎 (noise) to train the AI.**

---

## 📡 Data Sources Included

### 📰 News & Intelligence
- Reuters Tech, Bloomberg, FT, WSJ (RSS)
- Hacker News (top stories + comments signal)
- MIT Technology Review, IEEE Spectrum
- The Information, Stratechery

### 💰 Financial Signals
- SEC EDGAR (13F filings, 8-K events)
- Insider trading disclosures
- VC funding rounds (Crunchbase/PitchBook RSS)
- Options flow anomalies

### 🔬 Research & Patents
- USPTO new patent filings
- arXiv (AI, quantum, biotech)
- Google Scholar alerts
- European Patent Office

### 🌐 Alternative Data
- GitHub trending repositories
- LinkedIn job posting trends (proxy for company direction)
- Reddit r/investing, r/MachineLearning, r/geopolitics
- Google Trends API

### 🏛️ Regulatory
- EU AI Act implementation updates
- FTC/DOJ antitrust filings
- FDA approvals
- CFIUS national security reviews

---

## 🛠️ Tech Stack

| Component | Technology | Why |
|---|---|---|
| Agent Orchestration | CrewAI + LangGraph | Best multi-agent coordination |
| Local LLM | Ollama (llama3.1:8b) | Private, runs on your Mac |
| Embeddings | nomic-embed-text via Ollama | Local, no API costs |
| Vector Memory | ChromaDB | Lightweight, self-hosted |
| Database | SQLite | Simple, zero-config |
| Scheduling | APScheduler | Flexible cron-like jobs |
| Telegram | python-telegram-bot | Best Telegram library |
| WhatsApp | Twilio / Meta API | Most reliable WhatsApp access |
| Web Scraping | Playwright + BeautifulSoup | JS-capable scraping |
| Config | YAML + python-dotenv | Easy to modify |

---

## 🔄 Self-Learning Loop

```
You receive a brief
        ↓
You react (👍 or 👎) or ignore
        ↓
LearningAgent processes feedback
        ↓
Scoring weights updated in SQLite
        ↓
Next brief is MORE relevant to you
        ↓
(Repeat — system gets smarter every cycle)
```

---

## 📁 Project Structure

```
elite-intel-agent/
├── main.py                    # Entry point
├── requirements.txt
├── docker-compose.yml
├── .env.example
├── config/
│   ├── sources.yaml           # All data sources
│   └── scoring.yaml           # Signal scoring weights
├── agents/
│   ├── orchestrator.py        # CrewAI crew setup
│   ├── research_agent.py      # Data gathering agent
│   ├── signal_agent.py        # Signal scoring agent
│   ├── synthesis_agent.py     # Insight synthesis agent
│   └── learning_agent.py      # Self-learning agent
├── ingestion/
│   ├── rss_fetcher.py         # RSS + news
│   ├── financial_data.py      # Financial signals
│   ├── patent_monitor.py      # Patent tracking
│   ├── regulatory_monitor.py  # Regulatory filings
│   └── social_signals.py      # Reddit, HN signals
├── scoring/
│   ├── signal_scorer.py       # ML scoring engine
│   └── feedback_learner.py    # Feedback processing
├── memory/
│   ├── vector_store.py        # ChromaDB interface
│   └── knowledge_base.py      # Knowledge management
├── delivery/
│   ├── telegram_bot.py        # Telegram delivery
│   └── whatsapp_bot.py        # WhatsApp delivery
└── scheduler/
    └── job_scheduler.py       # Task scheduling
```

---

## 🔐 Privacy

All processing happens **locally on your machine** via Ollama. No data is sent to OpenAI or any cloud LLM unless you explicitly configure it. Your intelligence profile stays on your device.

---

## 📄 License

MIT License — use freely, build on top of it.
