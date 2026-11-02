# 🧠 SoulSpace — AI-Powered Reflective Journalling Research Platform

**SoulSpace** is a full-stack web application that combines mood tracking, reflective journalling, and a multi-agent AI pipeline to study how users emotionally and behaviourally respond to AI-generated long-term reasoning about their own mental state.

> This project is the basis of a final-year research study. The system is explicitly **non-clinical** and is designed as a self-reflective journalling tool, not a diagnostic instrument.

---

## 📖 Research Abstract

Current journalling systems either provide a one-time, single-entry sentiment analysis directly to users, or reserve deeper pattern analysis for clinicians. No prior system has combined **multi-entry, long-term pattern analysis** with **direct user feedback** within a self-reflective, non-clinical setting — nor has the impact of such feedback on potentially vulnerable individuals been studied.

SoulSpace fills that gap. It uses a **four-agent pipeline** to safely surface validated emotional patterns to the user:

| Agent | Role |
|---|---|
| **Entry Analysis Agent** | Tags each journal entry for sentiment, cognitive distortions, and keywords |
| **Memory / Trend Agent** | Analyses recent entries and proposes a long-term pattern hypothesis |
| **Verification Agent** | Independently re-evaluates the same raw entries to confirm or dispute the hypothesis |
| **Disclosure Agent** | Presents validated patterns in clear, non-clinical language |

A **two-layer safety gate** (occurrence/severity threshold + agent agreement score) determines what information reaches the user. Explicit crisis language **bypasses the pipeline entirely** and routes directly to crisis resources.

The study will compare user emotional and behavioural responses to AI-generated long-term pattern insights versus standard single-entry feedback.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔐 **Authentication** | Secure signup & login with bcrypt password hashing and JWT tokens |
| 📓 **Journal** | Create, read, update, and delete private journal entries |
| 😊 **Mood Tracking** | Log moods independently or attach them to journal entries |
| 💬 **Sentiment Analysis** | Automatic NLP sentiment scoring on every entry (TextBlob) |
| 🤖 **AI Wellness Chatbot** | Supportive mental-wellness chatbot (rule-based + LLM) |
| 🧩 **Multi-Agent AI Pipeline** | Four-agent system analysing entries for emotions, cognitive distortions, and long-term patterns |
| 🚨 **Crisis Detection** | Detects high-risk language and surfaces crisis resources immediately |
| 🔒 **Two-Layer Safety Gate** | Threshold + agent agreement before any pattern is disclosed to the user |
| 📊 **Analytics Dashboard** | Mood trends, weekly/monthly summaries, and journalling streaks (Recharts) |
| 🗺️ **Journey Report** | Personalised AI-generated reflection of the user's emotional journey (gated for study participants) |
| 🎓 **Study Participant Mode** | Flag that hides and server-blocks the Journey Report for users enrolled in the research study |

---

## 🏗️ Tech Stack

### Backend
| Layer | Technology |
|---|---|
| Framework | Python 3 · Flask 3 |
| Database | PostgreSQL (via psycopg2-binary) |
| Auth | JWT (PyJWT) · bcrypt |
| NLP | TextBlob · NLTK |
| LLM Integration | Groq API (`llama-3.1-70b-versatile`) / Ollama (local) / rule-based fallback |
| Environment | python-dotenv |

### Frontend
| Layer | Technology |
|---|---|
| Framework | React 19 · Vite 7 |
| Routing | React Router DOM v7 |
| Styling | Tailwind CSS v3 |
| Charts | Recharts |

---

## 📁 Project Structure

```
Final year project/
├── backend/                        # Flask API server
│   ├── main.py                     # Entry point — creates the Flask app
│   ├── routes.py                   # Blueprint registration
│   ├── database.py                 # DB connection & table initialisation
│   ├── models.py                   # SQL query helpers (CRUD)
│   ├── auth.py                     # /auth/signup, /auth/login
│   ├── journal.py                  # /journal/ CRUD + triggers AI pipeline
│   ├── mood.py                     # /api/mood standalone mood logging
│   ├── analytics.py                # /analytics/ mood trends, summary, streak
│   ├── chat.py                     # /api/chat wellness chatbot endpoint
│   ├── insights.py                 # /insights/ AI pipeline results
│   ├── agents/                     # ── Multi-Agent AI Pipeline ──
│   │   ├── pipeline.py             # Orchestrator: runs all agents in sequence
│   │   ├── entry_analysis.py       # Agent 1: emotion, stress, distortion tagger
│   │   ├── memory_agent.py         # Agent 2: builds long-term pattern hypothesis
│   │   ├── verification_agent.py   # Agent 3: independent re-evaluation
│   │   ├── safety_gate.py          # Two-layer gate (threshold + agreement)
│   │   ├── disclosure_agent.py     # Agent 4: safe, non-clinical disclosure
│   │   ├── crisis_detector.py      # Explicit crisis bypass → resources
│   │   ├── report_agent.py         # Journey Report generation
│   │   ├── nlp_preprocessor.py     # Text cleaning & keyword extraction
│   │   └── llm_provider.py         # Groq / Ollama / fallback adapter
│   ├── utils/
│   │   ├── sentiment.py            # TextBlob sentiment wrapper
│   │   ├── suggestion.py           # Rule-based wellness suggestion engine
│   │   └── chat.py                 # ChatService logic
│   ├── requirements.txt
│   ├── .env.example                # Template for environment variables
│   └── .env                        # Your local secrets (never commit this!)
│
└── mindmate/                       # React + Vite frontend (SoulSpace UI)
    ├── src/
    │   ├── App.jsx                 # Root component & routes
    │   ├── main.jsx                # ReactDOM entry point
    │   ├── pages/
    │   │   ├── Login.jsx
    │   │   ├── Signup.jsx
    │   │   └── Dashboard.jsx       # Main dashboard with AI insights panel
    │   ├── components/
    │   │   ├── Navbar.jsx
    │   │   ├── JournalForm.jsx
    │   │   ├── MoodLogger.jsx
    │   │   ├── MoodSelector.jsx
    │   │   ├── ChartView.jsx
    │   │   ├── ChatBot.jsx
    │   │   └── JourneyReportModal.jsx  # Gated for study participants
    │   ├── api/                    # Fetch wrappers per domain
    │   │   ├── api.js
    │   │   ├── auth.js
    │   │   ├── journal.js
    │   │   ├── mood.js
    │   │   └── chat.js
    │   └── context/
    │       └── AuthContext.jsx     # Global auth state (JWT + user)
    ├── package.json
    ├── vite.config.js
    └── tailwind.config.js
```

---

## ⚙️ Prerequisites

- **Python 3.10+**
- **Node.js 18+** and **npm**
- **PostgreSQL** (running locally or remotely)
- _(Optional)_ A free **Groq API key** from [console.groq.com](https://console.groq.com) for LLM features

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd "Final year project"
```

### 2. Create the PostgreSQL database

```sql
CREATE DATABASE soulspace_db;
```

### 3. Configure the backend environment

```bash
cd backend
copy .env.example .env
```

Open `.env` and fill in your values:

```env
# PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=soulspace_db
DB_USER=postgres
DB_PASSWORD=yourpassword

# JWT — generate with: python -c "import secrets; print(secrets.token_hex(32))"
JWT_SECRET=your_long_random_secret

# LLM provider: groq | ollama | fallback
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-70b-versatile

# Ollama (only if LLM_PROVIDER=ollama)
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
```

### 4. Install backend dependencies

```bash
pip install -r requirements.txt
```

### 5. Start the Flask backend

```bash
python main.py
```

The server starts at **http://localhost:5000**. All database tables are created automatically on first run.

### 6. Install frontend dependencies

```bash
cd ../mindmate
npm install
```

### 7. Start the frontend dev server

```bash
npm run dev
```

The app opens at **http://localhost:5173**.

---

## 🌐 API Reference

All protected endpoints require:
```
Authorization: Bearer <jwt_token>
```

### Auth
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/auth/signup` | ✗ | Register a new account |
| `POST` | `/auth/login` | ✗ | Login and receive a JWT |

### Journal
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/journal/` | ✓ | Create entry — triggers the full AI pipeline |
| `GET` | `/journal/` | ✓ | List all entries for the logged-in user |
| `GET` | `/journal/<id>` | ✓ | Get a single entry |
| `PUT` | `/journal/<id>` | ✓ | Update an entry |
| `DELETE` | `/journal/<id>` | ✓ | Delete an entry |
| `GET` | `/journal/moods` | ✗ | List available mood options |

### Mood Logging
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/mood` | ✓ | Log a standalone mood check-in |
| `GET` | `/api/mood` | ✓ | Get today's mood log |

### Analytics
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/analytics/mood-trends` | ✓ | Mood counts for the last 7 days |
| `GET` | `/analytics/summary` | ✓ | Weekly & monthly sentiment summary |
| `GET` | `/analytics/streak` | ✓ | Current journalling streak (days) |

### AI Insights & Chatbot
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/chat` | ✗ | Send a message to the wellness chatbot |
| `GET` | `/insights/timeline` | ✓ | Emotional timeline from pipeline analyses |
| `GET` | `/insights/patterns` | ✓ | Validated long-term patterns |
| `GET` | `/insights/reflection` | ✓ | Current disclosure reflection text |
| `GET` | `/insights/journey-report` | ✓ | Full Journey Report (blocked for study participants) |

### Health Check
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `GET` | `/` | ✗ | Verify the API is running |

---

## 🤖 Multi-Agent AI Pipeline

Every journal entry triggers this pipeline automatically. It is **non-fatal** — if any step fails, the entry is still saved.

```
New Journal Entry
       │
       ▼
 NLP Preprocessor          ← cleans text, extracts keywords
       │
       ▼
 Entry Analysis Agent       ← Agent 1: sentiment · emotion · stress ·
       │                              cognitive distortions · risk flag
       ▼
 Memory / Trend Agent       ← Agent 2: reviews recent entries,
       │                              proposes a pattern hypothesis
       ▼
 Verification Agent         ← Agent 3: independently re-evaluates
       │                              the same raw entries
       ▼
 ┌────┴──────────────────┐
 │    Safety Gate         │  ← Two-layer check:
 │  (threshold + agreement│    1. Occurrence / severity threshold
 └────┬──────────────────┘    2. Memory ↔ Verification agreement score
      │
   ┌──┴──────────────────┐
   ▼                     ▼
Crisis Detector      Disclosure Agent    ← Agent 4: generates safe,
(explicit crisis →   (patterns clear     non-clinical reflection text
 bypass to resources) the gate →
                      user sees it)
```

### Key Safety Mechanisms

| Mechanism | Purpose |
|---|---|
| **Crisis bypass** | Explicit crisis language skips all agents and returns immediate resources |
| **Occurrence threshold** | A pattern must appear across multiple entries before being considered |
| **Severity threshold** | Low-intensity signals are suppressed regardless of frequency |
| **Agent agreement** | Memory and Verification agents must agree before Disclosure runs |
| **Study participant flag** | `is_study_participant = TRUE` blocks the Journey Report at both server and UI level |

---

## 🔒 Security Notes

- Passwords are hashed with **bcrypt** (salted rounds); plain-text passwords are never stored.
- JWTs expire after **24 hours**; every protected endpoint verifies the signature and expiry.
- The `.env` file is in `.gitignore` — **never commit it**.
- In production, replace `CORS(origins="*")` with your actual frontend domain.
- Set `debug=False` and use a production WSGI server (e.g., **Gunicorn**) when deploying.

---

## 🛠️ Available Scripts

### Backend
```bash
python main.py          # Start Flask dev server on port 5000
```

### Frontend
```bash
npm run dev             # Start Vite dev server on port 5173
npm run build           # Build for production → dist/
npm run preview         # Preview the production build locally
npm run lint            # Run ESLint
```

---

## 🗄️ Database Schema (summary)

| Table | Purpose |
|---|---|
| `users` | User accounts (username, email, bcrypt hash, study flag) |
| `moods` | Mood lookup table (Happy, Sad, Anxious, Calm, Angry) |
| `journals` | Journal entries with sentiment score, label, and suggestion |
| `mood_logs` | Standalone daily mood check-ins |
| `entry_analyses` | Agent 1 output: emotion, stress, distortions, risk, keywords |
| `memory_patterns` | Agent 2 output: long-term pattern hypothesis |
| `verification_results` | Agent 3 output: independent pattern evaluation |
| `disclosure_history` | What patterns were ultimately disclosed to the user and when |
| `safety_logs` | Records of every safety gate decision (pass/block + reasoning) |
| `crisis_events` | Log of every crisis detection event |

---

## 📝 License

This project was built as a Final Year Research Project. All rights reserved.
