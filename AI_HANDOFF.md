# AI Handoff Document - Job Finder Project
**Date**: December 31, 2025  
**GitHub**: https://github.com/BillSteinUNB/JobFinder  
**Last Commit**: `91735af` - "Add FastAPI backend with REST API endpoints"

---

## Project Overview

**Job Finder** is a portfolio-grade job recommendation system that:
1. Ingests job postings from APIs (Adzuna)
2. Parses resumes (PDF/text) and extracts skills
3. Computes semantic similarity using NLP (sentence-transformers)
4. Provides explainable job recommendations with hybrid scoring

### Tech Stack

| Component | Technology |
|-----------|------------|
| Backend Logic | Python 3.11+ |
| API Server | **FastAPI** (newly added) |
| Data Source | Adzuna API |
| NLP Model | `all-MiniLM-L6-v2` (sentence-transformers) |
| Vector DB | ChromaDB (local/embedded) |
| Metadata DB | SQLite |
| Resume Parsing | pdfplumber |
| Frontend | React 19 + TypeScript + Vite + Zustand + Tailwind |
| Charts | Recharts |
| Animations | Framer Motion |
| Testing | pytest, ruff, mypy |
| CI/CD | GitHub Actions |
| Containerization | Docker + docker-compose |

---

## Project Structure

```
JobFinder/
├── api/                          # FastAPI Backend (NEW - just created)
│   ├── __init__.py
│   ├── main.py                   # FastAPI app with CORS, lifespan
│   ├── state.py                  # Shared app state (DBs, embeddings)
│   ├── schemas.py                # Pydantic models matching TS types
│   └── routes/
│       ├── __init__.py
│       ├── resume.py             # POST /upload, GET /profile
│       ├── jobs.py               # GET /search, GET /{id}, PATCH /{id}/label
│       ├── applications.py       # GET, PATCH, POST endpoints
│       └── analytics.py          # GET /analytics
├── app/                          # Streamlit Dashboard (legacy, complete)
│   ├── components/
│   └── streamlit_app.py
├── jobhunt/                      # React Frontend (needs API connection)
│   ├── components/               # UI components
│   ├── views/                    # Page views
│   ├── App.tsx
│   ├── store.ts                  # Zustand store (USES MOCK DATA)
│   ├── types.ts                  # TypeScript interfaces
│   ├── constants.ts              # MOCK_JOBS, MOCK_APPLICATIONS
│   └── ...
├── src/                          # Core Python Backend Logic
│   ├── data_collection/          # Adzuna API client, Job schema
│   ├── db/                       # MetadataDB (SQLite), VectorDB (Chroma)
│   ├── matching/                 # EmbeddingManager, HybridScorer, Evidence
│   ├── processing/               # PDF parser, text cleaner, skill extraction
│   ├── evaluation/               # Metrics
│   └── utils/                    # Config, logger
├── tests/                        # pytest test suite
├── scripts/                      # CLI tools (collect_jobs, build_vector_index)
├── .github/workflows/ci.yml      # CI pipeline
├── Dockerfile
├── docker-compose.yml            # Updated for full stack
├── requirements.txt              # Updated with FastAPI deps
└── pyproject.toml                # pytest/ruff/mypy config
```

---

## What Was Just Completed

### FastAPI Backend (`api/`)

Created a complete REST API to connect the React frontend to the Python backend:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/resume/upload` | POST | Upload PDF, parse, extract skills, create embedding |
| `/api/resume/profile` | GET | Get current resume profile |
| `/api/jobs/search` | GET | Semantic job search with scoring against resume |
| `/api/jobs/{id}` | GET | Job details with match explanation |
| `/api/jobs/{id}/label` | PATCH | Save (1) or reject (0) a job |
| `/api/applications` | GET | Get all applications |
| `/api/applications/{id}` | PATCH | Update application status |
| `/api/applications/{job_id}` | POST | Create new application |
| `/api/analytics` | GET | Dashboard analytics data |

**Key Files Created**:
- `api/main.py` - FastAPI app with CORS for localhost:5173/3000
- `api/state.py` - Shared state holding DB connections, embedding manager, resume profile
- `api/schemas.py` - Pydantic models that match `jobhunt/types.ts`
- `api/routes/*.py` - Route handlers

**Dependencies Added** (requirements.txt):
```
fastapi==0.115.0
uvicorn[standard]==0.32.0
python-multipart==0.0.12
```

---

## What Needs To Be Done Next

### Priority 1: Connect React Frontend to API

The React frontend in `jobhunt/` currently uses **mock data** from `constants.ts`. It needs to be updated to fetch from the FastAPI backend.

#### Tasks:

1. **Add TanStack Query** (React Query) for data fetching:
   ```bash
   cd jobhunt
   npm install @tanstack/react-query
   ```

2. **Create API client** (`jobhunt/api/client.ts`):
   ```typescript
   const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
   
   export const api = {
     uploadResume: (file: File, settings?: {...}) => fetch(...),
     getResumeProfile: () => fetch(`${API_BASE}/api/resume/profile`),
     searchJobs: (params) => fetch(`${API_BASE}/api/jobs/search?...`),
     getJob: (id) => fetch(`${API_BASE}/api/jobs/${id}`),
     labelJob: (id, label) => fetch(`${API_BASE}/api/jobs/${id}/label`, {...}),
     getApplications: () => fetch(`${API_BASE}/api/applications`),
     updateApplication: (id, data) => fetch(...),
     getAnalytics: () => fetch(`${API_BASE}/api/analytics`),
   };
   ```

3. **Update Zustand store** (`store.ts`):
   - Remove mock data imports
   - Add React Query integration or fetch calls
   - Update state management to use real API data

4. **Update views**:
   - `ResumeView.tsx` - Connect file upload to `/api/resume/upload`
   - `JobSearch.tsx` - Fetch from `/api/jobs/search`
   - `Applications.tsx` - Fetch from `/api/applications`
   - `Analytics.tsx` - Fetch from `/api/analytics`
   - `Dashboard.tsx` - Combine data from multiple endpoints

5. **Add environment variable**:
   - Create `jobhunt/.env.local`:
     ```
     VITE_API_URL=http://localhost:8000
     ```

### Priority 2: Test the Full Stack

1. **Start the API**:
   ```bash
   # Activate venv first
   pip install -r requirements.txt
   uvicorn api.main:app --reload
   ```

2. **Start the frontend**:
   ```bash
   cd jobhunt
   npm install
   npm run dev
   ```

3. **Test the flow**:
   - Upload a resume PDF
   - Search for jobs
   - Save/reject jobs
   - Check analytics

### Priority 3: Production Considerations

1. **Persist application data** - Currently `_applications` in `applications.py` is in-memory. Should be a database table.

2. **Add authentication** - Currently no auth. Consider adding JWT or session-based auth.

3. **Add resume persistence** - Resume profile is lost on server restart. Should save to disk/DB.

4. **Update Dockerfile** - Current Dockerfile is for Streamlit. May need adjustment for FastAPI.

---

## Key Design Decisions

1. **Collection-per-version** for ChromaDB - Embedding version is in collection name to avoid mixing incompatible vectors

2. **Hybrid scoring** with 5 components:
   - Embedding similarity (55%)
   - Skill overlap (25%)
   - Recency (10%)
   - Location (7%)
   - Salary (3%)

3. **Recall-style skill matching**: `job skills covered / total job skills`

4. **Exponential decay** for recency with 30-day half-life

5. **Labels**: `1 = saved`, `0 = rejected`, `None = unlabeled`

6. **Frontend state**: Zustand for global state, will use TanStack Query for server state

---

## Running the Project

### Development

```bash
# Terminal 1: Start API
cd JobFinder
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

# Terminal 2: Start Frontend
cd JobFinder/jobhunt
npm install
npm run dev
```

### Docker

```bash
# API only
docker compose up api

# API + Frontend (dev)
docker compose --profile frontend up

# All services including Streamlit
docker compose --profile streamlit --profile frontend up
```

---

## API Schemas Quick Reference

The Pydantic schemas in `api/schemas.py` match the TypeScript types in `jobhunt/types.ts`:

| Python (api/schemas.py) | TypeScript (types.ts) |
|-------------------------|----------------------|
| `JobResponse` | `Job` |
| `CompanyResponse` | `Company` |
| `MatchedSkill` | `MatchedSkill` |
| `ApplicationResponse` | `Application` |
| `ResumeProfileResponse` | `ResumeData` |
| `AnalyticsResponse` | `AnalyticsData` |

---

## Files to Focus On

When connecting frontend to backend:

1. **Backend entry**: `api/main.py`
2. **Frontend entry**: `jobhunt/App.tsx`
3. **State management**: `jobhunt/store.ts`
4. **Type definitions**: `jobhunt/types.ts` ↔ `api/schemas.py`
5. **Mock data to replace**: `jobhunt/constants.ts`

---

## Contact

GitHub Repo: https://github.com/BillSteinUNB/JobFinder

Good luck! The backend is ready - just need to wire up the frontend.
