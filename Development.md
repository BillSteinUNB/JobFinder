# Job Recommender System: Development Blueprint

This document serves as the primary technical guide for building the Job Recommender System. It integrates the Product Requirements, Technical Research, and Development Roadmap.

---

## 1. Project Overview
A portfolio-grade system that ingest job postings from APIs, parses a user's resume, computes semantic similarity using NLP, and provides explainable job recommendations through a Streamlit dashboard.

### Core Value Proposition
- **Automated Discovery:** No more manual searching across 10+ tabs.
- **Semantic Matching:** Goes beyond keyword matching to understand context.
- **Explainability:** Answers the question "Why is this a match?" with evidence.

---

## 2. Technical Stack (The "Best-in-Class" 2025 Stack)

| Component | Technology | Why? |
| :--- | :--- | :--- |
| **Data Source** | [Adzuna API](https://developer.adzuna.com/) | 1k free calls/month, full descriptions, salary data. |
| **Language** | Python 3.10+ | Standard for DS/ML; excellent library support. |
| **NLP Model** | `all-MiniLM-L6-v2` | Best balance of speed/accuracy for text similarity. |
| **Vector DB** | [ChromaDB](https://www.trychroma.com/) | Local, zero-config, persistent, and highly performant. |
| **Metadata DB** | SQLite | Built-in, lightweight, perfect for job metadata. |
| **Resume Parsing** | `pdfplumber` | Superior handling of multi-column resume layouts. |
| **Dashboard** | Streamlit | Rapid UI development with Python. |
| **Skill Extraction** | Lightcast Open Skills | Industry standard for professional skill taxonomy. |

---

## 3. Project Structure

```text
job-finder/
├── app/                        # Streamlit Dashboard
│   ├── components/             # Reusable UI widgets (job cards, charts)
│   └── streamlit_app.py        # Main dashboard entry point
├── data/                       # Local storage (ignored by git, except .gitkeep)
│   ├── jobs.db                 # Metadata SQLite
│   └── chromadb/               # Vector database storage
├── notebooks/                  # EDA and Model Experimentation
├── src/                        # Core Logic
│   ├── data_collection/        # API clients and scrapers
│   │   ├── adzuna_client.py
│   │   └── schema.py           # Pydantic models for validation
│   ├── db/                     # Database handlers
│   │   ├── metadata_db.py      # SQLite operations
│   │   └── vector_db.py        # ChromaDB operations
│   ├── matching/               # Ranking and NLP logic
│   │   ├── embeddings.py       # Model loading and inference
│   │   └── scorer.py           # Hybrid ranking algorithm
│   ├── processing/             # Text cleaning and parsing
│   │   ├── pdf_parser.py       # Resume extraction
│   │   └── text_cleaner.py     # Job desc normalization
│   └── utils/                  # Logging, config, and helpers
├── tests/                      # Unit and integration tests
├── scripts/                    # CLI tools for manual runs
│   ├── collect_jobs.py
│   └── setup_db.py
├── .env.example                # Template for API keys
├── Development.md              # This file
├── README.md                   # Project overview for GitHub
└── requirements.txt            # Dependency list
```

---

## 4. Database Design

### 4.1 Metadata (SQLite: `jobs` table)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | TEXT (PK) | Unique ID (Source + Source_ID) |
| `title` | TEXT | Job Title |
| `company` | TEXT | Company Name |
| `location` | TEXT | City/Region/Remote |
| `description` | TEXT | Cleaned full text |
| `salary_min` | FLOAT | Min salary (if available) |
| `salary_max` | FLOAT | Max salary (if available) |
| `url` | TEXT | Link to posting |
| `source` | TEXT | e.g., 'adzuna' |
| `created_at` | DATETIME | Ingestion timestamp |
| `label` | INTEGER | User feedback (1=Interested, 0=Not) |

### 4.2 Vectors (ChromaDB)
- **Collection Name:** `job_descriptions`
- **Embedding Model:** `all-MiniLM-L6-v2`
- **Metadata stored in Chroma:** `job_id`, `title`, `company`.

---

## 5. Development Roadmap

### Phase 1: Ingestion & Infrastructure (Week 1)
- [ ] Set up project structure and virtual environment.
- [ ] Implement `AdzunaClient` to fetch 500+ jobs.
- [ ] Build SQLite schema and persistence layer.
- [ ] Implement deduplication logic.

### Phase 2: Processing & Vectorization (Week 2)
- [ ] Implement `pdfplumber` resume parser.
- [ ] Build text cleaning pipeline (HTML removal, normalization).
- [ ] Integrate ChromaDB for job description embeddings.
- [ ] Implement `EmbeddingManager` for model loading.

### Phase 3: Matching & Basic UI (Week 3)
- [ ] Build the `HybridScorer` (Embedding Sim + Skill Match).
- [ ] Create the Streamlit dashboard: Job list view + Sidebar filters.
- [ ] Add "Job Detail" view with expanders.

### Phase 4: Explainability & Refinement (Week 4)
- [ ] Implement "Evidence Extraction" (highlighting matching sentences).
- [ ] Add "Skill Gap" visualization.
- [ ] Add user feedback buttons (Save/Reject) to the UI.
- [ ] Implement basic evaluation metrics (Precision@10).

---

## 6. Evaluation Metrics
How we measure success:
1. **Precision@10:** Out of the top 10 recommended jobs, how many would I actually apply to?
2. **Diversity:** Are the recommendations covering multiple companies/locations or just one?
3. **Latency:** End-to-end scoring of 1,000 jobs should take < 2 seconds.

---

## 7. Strategic Pitfalls & Mitigations
- **Pitfall:** Resume layout complexity breaks parsing.
  - **Mitigation:** Use `pdfplumber` with fallback to `PyMuPDF`; allow manual text override in UI.
- **Pitfall:** API rate limits or expired keys.
  - **Mitigation:** Implement robust caching in SQLite so we don't re-fetch the same jobs twice.
- **Pitfall:** "Embedding Drift" when swapping models.
  - **Mitigation:** Include the model name in the ChromaDB collection metadata.

