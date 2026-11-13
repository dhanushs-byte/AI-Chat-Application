# 🤖 AI Chat Application

A full-stack AI-powered chatbot built using **FastAPI, PostgreSQL, SQLAlchemy, OpenRouter, HTML, CSS and JavaScript**.

The application supports real-time streaming AI responses, persistent chat history, API key authentication, sliding-window conversation memory, rate limiting, automatic retries, and token and cost tracking.

This project was developed as part of **Week 5 – Day 5: LLM Application Development**.

---

## 🚀 Features

- **AI Chat:** Generate intelligent responses using OpenRouter.
- **Streaming Responses:** Display AI responses progressively using Server-Sent Events (SSE).
- **Chat Persistence:** Store conversations and messages in PostgreSQL.
- **Session Management:** Create, retrieve and delete chat sessions.
- **Conversation History:** Reload previous conversations.
- **API Key Authentication:** Secure API endpoints using `x-api-key`.
- **Sliding Window Memory:** Maintain recent conversation context while preserving full database history.
- **Rate Limiting:** Maximum 20 messages per API key per hour.
- **Retry Mechanism:** Handle temporary LLM failures using Tenacity.
- **Token Tracking:** Monitor input, output and total tokens.
- **Cost Tracking:** Estimate API usage cost per session.
- **Responsive Frontend:** Interactive chatbot interface.
- **Stop Generation:** Allow users to stop an active browser streaming request.

---

## 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Programming Language | Python |
| Backend Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| AI Provider | OpenRouter |
| LLM SDK | OpenAI Python SDK |
| Streaming | StreamingResponse, SSE |
| Authentication | API Key Authentication |
| Retry Handling | Tenacity |
| Token Counting | tiktoken |
| Frontend | HTML, CSS, JavaScript |
| Testing | Pytest, HTTPX |
| Code Coverage | pytest-cov |

---

## 📁 Project Structure

```text
AI-Chat-Application/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── routes.py
│   ├── chat.py
│   ├── llm.py
│   └── rate_limit.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_sessions.py
│   ├── test_chat.py
│   └── test_rate_limit.py
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🗄️ Database Schema

The application uses PostgreSQL with three tables.

### 1. Sessions Table

Stores individual chat sessions.

| Column | Data Type | Description |
|---|---|---|
| id | UUID | Primary key |
| created_at | TIMESTAMP | Session creation time |
| total_tokens | INTEGER | Total tokens used |
| total_cost | FLOAT | Estimated session cost |

### 2. Messages Table

Stores user and assistant messages.

| Column | Data Type | Description |
|---|---|---|
| id | SERIAL | Primary key |
| session_id | UUID | Foreign key |
| role | VARCHAR | user / assistant |
| content | TEXT | Message content |
| tokens | INTEGER | Message token count |
| created_at | TIMESTAMP | Message creation time |

### 3. Rate Limit Events Table

Tracks API requests using hashed API keys.

| Column | Data Type | Description |
|---|---|---|
| id | SERIAL | Primary key |
| api_key_hash | VARCHAR(64) | SHA-256 API key hash |
| created_at | TIMESTAMP | Request timestamp |

---

## ⚙️ Installation and Setup

### Prerequisites

- Python 3.10 or later
- PostgreSQL
- VS Code
- OpenRouter API key

### Step 1: Clone the repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL

cd AI-Chat-Application
```

### Step 2: Create virtual environment

```bash
python -m venv .venv
```

Activate on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Create PostgreSQL database

Open pgAdmin or PostgreSQL command line.

Execute:

```sql
CREATE DATABASE ai_chat_db;
```

### Step 5: Configure environment variables

Create a `.env` file in the project root.

Copy the configuration from `.env.example`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=ai_chat_db
DB_USER=postgres
DB_PASSWORD=your_postgres_password

API_KEYS=my_chat_secret_key_123

OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=your_supported_model

MAX_HISTORY_TURNS=10
MAX_MESSAGES_PER_HOUR=20

INPUT_COST_PER_MILLION=0.15
OUTPUT_COST_PER_MILLION=0.60

CORS_ORIGINS=http://localhost:5500
```

Replace the database password, API key and model ID with your actual configuration.

The cost values above are example configuration values. Use the actual pricing for your selected model.

**Important:** Never upload `.env` or expose API credentials on GitHub.

### Step 6: Run the backend

```bash
python -m uvicorn app.main:app --reload
```

Backend URL:

http://127.0.0.1:8000

API documentation:

http://127.0.0.1:8000/docs

### Step 7: Run the frontend

Open another terminal:

```bash
python -m http.server 5500 --directory frontend
```

Open the application:

http://localhost:5500

---

## 🔗 API Endpoints

All endpoints require API key authentication through the `x-api-key` header.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/sessions` | Create a new session |
| GET | `/sessions` | Retrieve all sessions |
| GET | `/sessions/{id}/messages` | Retrieve conversation history |
| DELETE | `/sessions/{id}` | Delete a session |
| POST | `/sessions/{id}/chat` | Stream an AI response |
| GET | `/health` | Check application health |

### Example: Create Session

```http
POST /sessions
x-api-key: your_api_key
```

### Example: Send Chat Message

```http
POST /sessions/{session_id}/chat
Content-Type: application/json
x-api-key: your_api_key
```

Request:

```json
{
  "message": "Explain Generative AI in simple words."
}
```

### Streaming Response

The application returns Server-Sent Events.

Example:

```text
data: {"type":"token","content":"Generative"}

data: {"type":"token","content":" AI"}

data: {"type":"token","content":" creates"}

data: {"type":"done","input_tokens":20,"output_tokens":35,"total_tokens":55,"cost":0.000024}
```

Token usage and cost values depend on the selected model and actual API response.

---

## 🔐 Authentication

API key authentication is implemented using FastAPI dependencies.

The application uses:

- `x-api-key` request header.
- Environment-based API key configuration.
- `secrets.compare_digest()` for secure comparison.

Expected responses:

| Condition | HTTP Status |
|---|---|
| Missing API key | 401 Unauthorized |
| Invalid API key | 403 Forbidden |
| Valid API key | 200 OK |

---

## ⏱️ Rate Limiting

The application enforces:

**Maximum 20 chat messages per API key per hour.**

Rate-limit events are stored in PostgreSQL.

The 21st request within the rolling one-hour window returns:

HTTP 429 – Too Many Requests

```json
{
  "detail": "Rate limit exceeded"
}
```

The response includes a `Retry-After` header indicating when another request can be accepted.

---

## 🧠 Conversation Memory

The application implements sliding-window memory.

1. Retrieve the complete conversation history from PostgreSQL.
2. Preserve the system prompt.
3. Select the latest 10 user/assistant turns.
4. Send the trimmed context to the LLM.

Older messages remain stored in PostgreSQL and can be retrieved when the user reopens a session.

---

## 📊 Token and Cost Tracking

The application tracks:

- Input tokens
- Output tokens
- Total tokens
- Estimated API cost per session

The cost calculation uses:

```text
Total Cost =
(Input Tokens × Input Price
 + Output Tokens × Output Price) / 1,000,000
```

Pricing is configurable through environment variables.

---

## 🔄 Error Handling and Retries

Tenacity is used to retry temporary failures when establishing the LLM streaming request.

The implementation uses:

- Three retry attempts.
- Exponential backoff.
- Randomized retry waiting.
- Friendly error messages when the AI service is unavailable.

---

## 🧪 Testing

The project uses Pytest for automated testing.

### Run all tests

```bash
pytest -v
```

### Run individual test modules

```bash
pytest tests/test_auth.py -v

pytest tests/test_sessions.py -v

pytest tests/test_chat.py -v

pytest tests/test_rate_limit.py -v
```

### Generate coverage report

```bash
pytest --cov=app --cov-report=term-missing
```

### Actual Test Results

| Test Module | Tests Passed |
|---|---:|
| Authentication | 3 |
| Chat Streaming | 2 |
| Rate Limiting | 1 |
| Session Management | 4 |
| **Total** | **10/10** |

### Code Coverage

**95% overall code coverage**, based on the completed test run.

```text
TOTAL
259 statements
13 missed
95% coverage
```

---

## 🖥️ Application Demo

The application provides:

1. A new chat creation interface.
2. A sidebar containing previous chat sessions.
3. Progressive AI response streaming.
4. Persistent conversation history.
5. API key configuration.
6. Error and rate-limit notifications.
7. Token and cost tracking in the backend.

---

## 🎯 Key Learning Outcomes

Through this project, I gained practical experience in:

- Building AI-powered applications with FastAPI.
- Integrating OpenRouter and LLM APIs.
- Implementing real-time streaming responses.
- Designing relational databases using PostgreSQL.
- Managing persistent chat sessions.
- Implementing API key authentication.
- Applying sliding-window conversation memory.
- Handling rate limits and API failures.
- Tracking token consumption and estimated costs.
- Developing frontend applications with HTML, CSS and JavaScript.
- Writing automated tests and measuring code coverage.

---

## 🔮 Future Enhancements

- User registration and login.
- Redis-based distributed rate limiting.
- Improved server-side generation cancellation.
- Chat export functionality.
- Markdown rendering and code highlighting.
- Production deployment.
- Conversation search.

---

## 👨‍💻 Project Information

**Project Name:** AI Chat Application

**Training:** Week 5 – Day 5

**Domain:** LLM Application Development

**Backend:** FastAPI and PostgreSQL

**LLM Provider:** OpenRouter

**Frontend:** HTML, CSS and JavaScript

**Testing:** Pytest

**Test Results:** 10 Passed

**Code Coverage:** 95%

**Development Branch:** `feature/chat-app`

---

⭐ Built as part of my hands-on LLM Application Development training.
