# SPB AI Dispatch Assistant

An AI-powered dispatch management assistant with natural language query support. The system allows users to query waybill, contractor, and route data using natural language (English and Arabic) and returns results as tables or natural language responses.

## Features

- Natural language queries (English & Arabic)
- SQL generation via LLM (Ollama)
- Scalar results returned as natural language responses
- Table results with attractive LLM-generated summaries
- CSV download for query results
- Real-time response times
- Category-based quick queries

## Prerequisites

- **Node.js** (v18 or higher)
- **Python** (3.14 or higher)
- **Ollama** with `gpt-oss` model installed

### Install Ollama

1. Download and install Ollama from https://ollama.ai
2. Pull the required model:
   ```bash
   ollama pull gpt-oss
   ```

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd spb-ai-dispatch-assistant
```

### 2. Install Frontend Dependencies

```bash
npm install
```

### 3. Install Backend Dependencies

Using `uv` (recommended):
```bash
uv sync
```

Or using `pip`:
```bash
pip install fastapi langchain langchain-ollama pandas uvicorn
```

## Running the Application

### 1. Start Ollama (if not running)

```bash
ollama serve
```

### 2. Start the Backend Server

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 3. Start the Frontend Development Server

In a new terminal:
```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/api/ai-overview` | GET | AI assistant overview data |
| `/api/usage-stats` | GET | Usage statistics |
| `/api/categories` | GET | Query categories |
| `/api/categories/{id}/queries` | GET | Queries for a category |
| `/api/query` | POST | Process natural language query |

## Project Structure

```
spb-ai-dispatch-assistant/
├── backend/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── utils.py          # Database & LLM utilities
│   └── fixed_queries.py  # Predefined SQL queries
├── components/
│   ├── ChatWidget.tsx    # Chat interface
│   ├── InfoPanel.tsx     # AI overview panel
│   ├── UsageStats.tsx    # Statistics display
│   └── ValueAddedTab.tsx # Value proposition cards
├── public/
├── App.tsx               # Main React component
├── index.tsx             # Entry point
├── types.ts              # TypeScript types
├── constants.ts          # Frontend constants
├── package.json          # Frontend dependencies
├── pyproject.toml        # Backend dependencies
├── vite.config.ts        # Vite configuration
├── all_waybills.db       # SQLite database
└── README.md
```

## Configuration

### Backend API URL

To change the backend URL (e.g., for ngrok), update `API_BASE_URL` in:
- `components/ChatWidget.tsx`
- `components/InfoPanel.tsx`
- `components/UsageStats.tsx`

### Database

The SQLite database (`all_waybills.db`) should be in the project root directory.

## Usage

1. Open the application in your browser
2. Use the category buttons to select predefined queries, or
3. Type your question in natural language (English or Arabic)
4. View results as tables or natural language responses
5. Download results as CSV using the download button

## Sample Queries

- "Show today's dispatch details"
- "List all active dispatches"
- "What is the current status of waybill 2-25-0010405?"
- "Which waybills are assigned to ALHBBAS FOR TRADING, TRANSPORT?"
- "Show contractor-wise waybill list"

## Tech Stack

**Frontend:**
- React 19
- TypeScript
- Vite
- Tailwind CSS
- Lucide React Icons
- React Markdown

**Backend:**
- FastAPI
- LangChain
- LangChain-Ollama
- Pandas
- SQLite
- Uvicorn
