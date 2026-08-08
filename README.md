# InterviewAI — Your Personal Technical Interviewer

> **Adaptive AI Technical Interview Agent Platform for AI Engineering Evaluation**

InterviewAI is an intelligent, multi-turn AI interviewing platform designed to conduct realistic, adaptive technical interviews for students finishing a 31-day AI Engineering Cohort.

Unlike basic question-answer chatbots, InterviewAI features a stateful **LangGraph reasoning graph** that tracks candidate knowledge, adjusts difficulty dynamically (Levels 1–5), explores weak/skipped topics, generates evidence-backed evaluations, and produces senior engineering hiring recommendations.

---

## 🌟 Key Features

- 🧠 **LangGraph Agent Reasoning State Machine**: Planner, Dynamic Question Generator, Evaluator (0–10 scoring & misconception tracking), Difficulty Controller, Topic Selector, Coverage Tracker, and Feedback/Hiring Recommender.
- 🎯 **Curriculum-Aware Adaptation**: Ingests a 31-Day AI Engineering Cohort curriculum graph covering Embeddings, RAG, Chunking, Vector DBs, Agents, Fine-tuning, and Guardrails.
- 👤 **Candidate Personalization**: Considers completed days, skipped topics, mission attempts, and past performance signals to formulate customized interview strategies.
- ⚡ **Multi-LLM Abstraction & Mock Mode**: Native support for **Google Gemini**, **OpenAI**, and **Mock Mode** (enables zero-credit offline testing & instant hackathon judge demos).
- 📊 **Multi-Dimensional Radar Analytics**: Interactive candidate radar chart visualizing technical depth, engineering thinking, problem-solving, communication, and confidence.
- 🛡️ **Prompt Injection Defenses**: Strictly delimits untrusted candidate input to prevent instruction overrides or score manipulation.

---

## 🏗️ Architecture

```
                         Next.js 14 Frontend (App Router + TailwindCSS + Shadcn/Recharts)
                                                         │
                                                         ▼
                                             FastAPI REST Backend (Python 3.12)
                                                         │
               ┌─────────────────────────────────────────┼────────────────────────────────────────┐
               ▼                                         ▼                                        ▼
    Candidate Repository                       Curriculum Repository                     Interview Engine
  (Profiles, Progress, History)               (31-Day AI Graph, Prereqs)            (Session & State Management)
               │                                         │                                        │
               └─────────────────────────────────────────┼────────────────────────────────────────┘
                                                         ▼
                                              LangGraph AI Agent Engine
                                                         │
        ┌─────────────────────┬──────────────────────────┼─────────────────────────┬──────────────┐
        ▼                     ▼                          ▼                         ▼              ▼
  Planner Node        Question Generator           Evaluator Node           Memory Manager   Feedback / Hiring
  (Strategy)          (Dynamic Questions)        (Scoring & Misconceptions)   (Summarization)    (Report & Decision)
        │                     │                          │                         │              │
        └─────────────────────┴──────────────────────────┼─────────────────────────┴──────────────┘
                                                         ▼
                                            LLM Provider Abstraction Layer
                                            (Gemini / OpenAI / Mock Mode)
                                                         │
                                                         ▼
                                            SQLModel / SQLite Database
```

---

## 🚀 Quick Start (Local Setup)

### 1. Backend Setup
```bash
cd backend
pip install -r requirements.txt
python -m app.database.seed
uvicorn app.main:app --reload --port 8000
```

FastAPI Swagger Documentation: `http://localhost:8000/docs`

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Next.js Application: `http://localhost:3000`

---

## 🐳 Docker Deployment

To launch both frontend and backend using Docker Compose:

```bash
docker compose up --build
```

---

## 🧪 Testing Suite

Run the full pytest backend test suite and End-to-End interview simulation:

```bash
cd backend
python -m pytest tests/ -v
```

---

## 🏆 Judge Demonstration Flow

1. Open `http://localhost:3000/dashboard`.
2. Select **Alex Chen** (Candidate with completed Days 1-9 & weak topics in Chunk Overlap & Vector Indices).
3. Click **Start Technical Interview**.
4. Experience real-time adaptive questions, countdown timer, markdown response editor, and live state transition indicators.
5. Complete 8+ questions to view the comprehensive **Senior Engineering Feedback Report** featuring radar performance charts, evidence-backed strengths & weaknesses, misconception report, personalized learning roadmap, and final Hiring Recommendation card (Strong Hire to Not Ready).
