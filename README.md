# Job Finder

A portfolio-grade job recommendation system that uses NLP/ML to match your resume to job postings with explainable recommendations.

## Features

- **Resume Parsing:** Upload your resume (PDF/TXT) and extract skills automatically
- **Semantic Matching:** Uses sentence-transformers to find jobs that match your experience
- **Hybrid Scoring:** Combines embedding similarity, skill overlap, location, salary, and recency
- **Explainable Recommendations:** See why each job was recommended
- **Modern React UI:** Fast, responsive interface with real-time updates
- **Local-first:** Runs entirely on your machine with persistent data

## Tech Stack

| Component | Technology |
| :--- | :--- |
| Backend | FastAPI (Python 3.11+) |
| Frontend | React 19 + TypeScript + Vite |
| NLP Model | all-MiniLM-L6-v2 (sentence-transformers) |
| Vector DB | ChromaDB |
| Metadata DB | SQLite |
| Data Source | Adzuna API |
| Resume Parsing | pdfplumber |

## Quick Start

### Option 1: Automated Setup (Recommended)

```bash
git clone https://github.com/BillSteinUNB/JobFinder.git
cd JobFinder
python scripts/setup_local.py
```

### Option 2: Manual Setup

1. Create Python environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

2. Install frontend:
```bash
cd jobhunt && npm install && cd ..
```

3. Configure environment - create .env:
```
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
```

4. Collect jobs and build index:
```bash
python scripts/collect_all_jobs.py --target 1000
python scripts/build_vector_index.py
```

## Running the App

Terminal 1 - Backend:
```bash
uvicorn api.main:app --reload --port 8000
```

Terminal 2 - Frontend:
```bash
cd jobhunt && npm run dev
```

Open: http://localhost:5173

## Public Access with ngrok

For demos/interviews:

1. Install ngrok from https://ngrok.com/download
2. Start backend: uvicorn api.main:app --reload --port 8000
3. Expose backend: ngrok http 8000
4. Update jobhunt/.env.local with ngrok URL
5. Restart frontend

## License

MIT
