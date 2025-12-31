# Job Finder (Job Recommender System)

A portfolio-grade system that ingests job postings from APIs, parses your resume, computes semantic similarity using NLP, and provides explainable job recommendations through a Streamlit dashboard.

## Features

- **Automated Job Ingestion:** Fetches jobs from Adzuna API
- **Semantic Matching:** Uses `sentence-transformers` to match resume to job descriptions
- **Vector Search:** ChromaDB for fast similarity search across thousands of jobs
- **Explainable Recommendations:** See *why* each job was recommended
- **Interactive Dashboard:** Filter, sort, and explore jobs in Streamlit

## Tech Stack

| Component | Technology |
| :--- | :--- |
| Data Source | Adzuna API |
| NLP Model | `all-MiniLM-L6-v2` |
| Vector DB | ChromaDB |
| Metadata DB | SQLite |
| Resume Parsing | pdfplumber |
| Dashboard | Streamlit |

## Quickstart

### 1) Create environment

**Recommended (2025): uv**

```bash
uv venv
uv pip install -r requirements.txt
```

**Alternative: venv + pip**

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2) Configure environment

```bash
cp .env.example .env
# Edit .env and fill in your ADZUNA_APP_ID and ADZUNA_APP_KEY
# Get your free API key at https://developer.adzuna.com/
```

### 3) Run Streamlit

```bash
streamlit run app/streamlit_app.py
```

## Project Structure

```text
job-finder/
├── app/                        # Streamlit Dashboard
│   ├── components/             # Reusable UI widgets
│   └── streamlit_app.py        # Main dashboard entry point
├── data/                       # Local storage (gitignored)
├── notebooks/                  # EDA and experimentation
├── src/                        # Core logic
│   ├── data_collection/        # API clients
│   ├── db/                     # Database handlers
│   ├── matching/               # Ranking and NLP
│   ├── processing/             # Text cleaning and parsing
│   └── utils/                  # Helpers
├── tests/                      # Unit tests
├── scripts/                    # CLI tools
├── Development.md              # Technical blueprint
└── requirements.txt            # Dependencies
```

## Documentation

See [Development.md](./Development.md) for the full technical blueprint, database schema, and development roadmap.

## License

MIT
