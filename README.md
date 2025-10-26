# Hinder Backend

Meet your team faster. Hack faster. Hinder's backend powers profile parsing, embedding, search, and matching.

## Quickstart

### Prerequisites

- Python 3.10+
- pip / venv
- SQLite (included with Python)
- Anthropic API key (for resume parsing)
- Optional: Bright Data API key (for LinkedIn enrichment)

### Installation

1. Clone and navigate to backend:
   ```bash
   cd hinderbackend/backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file:
   ```bash
   cp .env.example .env  # Or create manually with the vars below
   ```

5. Configure environment variables in `.env`:
   ```
   # API Keys
   ANTHROPIC_API_KEY=sk-ant-...
   CLAUDE_MODEL=claude-3-5-haiku-latest
   OPENAI_API_KEY=sk-...  # Optional, for embeddings fallback
   GEMINI_API_KEY=...     # Optional, for embeddings fallback
   
   # Database
   SQLITE_PATH=./data/hinder.db
   
   # Embeddings
   EMBEDDINGS_PROVIDER=local  # local | gemini
   
   # Chroma Vector Store
   CHROMA_DIR=./chroma_data
   CHROMA_COLLECTION=profiles_vectors
   
   # Uploads
   UPLOAD_DIR=./data/uploads
   
   # Auth
   JWT_SECRET=your_secret_key_change_me
   JWT_ALG=HS256
   
   # Bright Data (optional)
   BRIGHTDATA_API_KEY=...
   BRIGHTDATA_ENABLED=0
   
   # Frontend CORS
   NEXT_PUBLIC_API_BASE=http://localhost:3000
   ```

6. Run the server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   Server runs on `http://127.0.0.1:8000`. Docs available at `/docs`.

## Project Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, router setup
│   ├── config.py               # Environment config
│   ├── deps.py                 # Dependency injection (DB session)
│   ├── db/
│   │   ├── models.py           # SQLModel schemas (User, Profile, Upload, etc.)
│   │   └── session.py          # SQLite session setup
│   ├── routers/
│   │   ├── auth.py             # Login/signup
│   │   ├── uploads.py          # Resume PDF upload
│   │   ├── profiles.py         # Profile CRUD + reembed
│   │   ├── search.py           # Vector search with filters
│   │   ├── matches.py          # Similarity-based matching
│   │   ├── brightdata.py       # LinkedIn enrichment
│   │   ├── status.py           # Profile status polling/SSE
│   │   ├── admin.py            # Admin stats/seed/clear
│   │   └── ...
│   ├── services/
│   │   ├── parsing.py          # Anthropic resume parsing
│   │   ├── pipeline.py         # Profile processing pipeline
│   │   ├── embeddings.py       # Vector embeddings (local/Gemini)
│   │   ├── chroma_store.py     # Chroma vector DB interface
│   │   ├── matching.py         # Similarity scoring
│   │   ├── normalize.py        # Skill/topic normalization
│   │   ├── brightdata.py       # Bright Data API client
│   │   └── ...
│   ├── schemas/
│   │   └── *.py                # Pydantic request/response models
│   └── utils/
│       ├── ids.py              # ID generation
│       ├── json.py             # JSON serialization helpers
│       └── ...
├── requirements.txt            # Python dependencies
└── data/                       # Local data (uploads, chroma, DB)
```

## Key Endpoints

### Auth
- `POST /auth/signup` – Register new user
- `POST /auth/login` – Login, get JWT token

### Uploads
- `POST /uploads` – Upload resume PDF (requires auth)

### Profiles
- `POST /profiles` – Create profile from resume/LinkedIn (requires auth, triggers pipeline)
- `GET /profiles/{id}` – Get profile (requires auth + ownership)
- `PATCH /profiles/{id}` – Update profile (requires auth + ownership)
- `DELETE /profiles/{id}` – Delete profile (requires auth + ownership)
- `POST /profiles/{id}/reembed` – Re-run embedding pipeline (requires auth + ownership)

### Search & Matching
- `GET /search` – Vector search with filters (skills, topics, availability, location, hackathon)
- `GET /matches?user_id=...` – Find similar profiles

### Enrichment
- `POST /brightdata/enrich` – Enrich profile with LinkedIn data (requires auth + ownership)
- `GET /brightdata/{profile_id}/status` – Check enrichment status (optional)

### Status
- `GET /status?profile_id=...` – Poll profile status
- `GET /status/stream?profile_id=...` – SSE stream for real-time status updates

### Admin (requires `is_admin=True`)
- `GET /admin/stats` – Profile/match stats
- `POST /admin/seed?count=12` – Generate synthetic profiles
- `POST /admin/clear` – Clear feedback logs

## Workflow: Resume → Profile → Search

1. **Upload Resume**
   ```bash
   curl -X POST http://localhost:8000/uploads \
     -H "Authorization: Bearer <token>" \
     -F "file=@resume.pdf"
   # Response: { "file_id": "file_...", "file_name": "..." }
   ```

2. **Create Profile**
   ```bash
   curl -X POST http://localhost:8000/profiles \
     -H "Authorization: Bearer <token>" \
     -H "Content-Type: application/json" \
     -d '{
       "consent": true,
       "resume_file_id": "file_...",
       "resume_file_name": "resume.pdf",
       "topics": ["backend", "infra"],
       "available_now": true,
       "hackathon": "HackMIT 2025"
     }'
   # Response: { "profile": {...}, "status": "pending" }
   ```
   - Pipeline runs in background: parsing → embedding → ready
   - Monitor with `GET /status?profile_id=...`

3. **Search Profiles**
   ```bash
   curl -X GET "http://localhost:8000/search?skills=Python,React&topics=backend&available_now=true&hackathon=HackMIT%202025" \
     -H "Authorization: Bearer <token>"
   # Response: { "items": [...], "total": 42, "page": 1, "page_size": 20 }
   ```

## Features

### Resume Parsing
- Uses Claude 3.5 Haiku to extract:
  - Name, headline, roles, skills (tech + domain), education, links, interests
- Falls back to derivation from experience/education/certifications if no explicit skills
- Robust error handling with verbose logging

### Embeddings
- Local embeddings (default) or Gemini API
- Profiles embedded as: `name | headline | skills | topics`
- Stored in Chroma with metadata (company, school, city, country_code, hackathon, etc.)

### Search
- Vector similarity search with optional filters
- Filters: skills, topics, availability, location, company, school, hackathon
- Pagination support

### Enrichment (Optional)
- Bright Data LinkedIn enrichment
- Derives skills from experience, education, certifications
- Backfills name, headline, company, school
- Rate-limited to once per 24h per profile

### Auth & Ownership
- JWT-based auth
- Ownership enforced on profile read/update/delete
- Admin role for `/admin` endpoints

## Database Schema

### User
- `id` (int, PK)
- `name`, `email` (unique), `password_hash`
- `is_admin` (bool, default False)
- `created_at`

### Profile
- `id` (str, PK)
- `user_id` (int, FK to User)
- `name`, `headline`, `email`, `school`, `company`, `seniority`
- `linkedin_url`, `resume_file_id`, `resume_file_name`
- `skills_norm_json`, `interests_json`, `topics_json` (JSON arrays)
- `available_now`, `hackathon`
- `status` (pending | parsing | embedding | ready | error)
- `created_at`, `updated_at`, `last_linkedin_enrich_at`

### Upload
- `file_id` (str, PK)
- `user_id` (int, FK to User)
- `path`, `mime`, `size`
- `created_at`

### MatchLog
- `id` (int, PK)
- `user_id`, `candidate_id` (str)
- `score_vector`, `score_keyword`, `score_blended`
- `rationale`, `feedback` (good | meh | bad)
- `created_at`

## Development

### Running Tests
```bash
pytest
```

### Logging
- Pipeline stages logged with `[pipeline]` prefix
- Anthropic parsing logs request/response and errors
- Bright Data enrichment logs raw data and skill extraction
- All background tasks log to stdout

### Hot Reload
```bash
uvicorn app.main:app --reload --port 8000
```

### Admin Setup
To promote a user to admin:
```bash
sqlite3 data/hinder.db "UPDATE user SET is_admin = 1 WHERE email = 'your@email.com';"
```

## Troubleshooting

### Profile stuck in "error" status
- Check server logs for pipeline exceptions
- Ensure `ANTHROPIC_API_KEY` is set and valid
- Verify Chroma directory is writable
- Re-run: `POST /profiles/{id}/reembed`

### Skills not extracted
- Check logs for "BrightData enrichment returned no skills"
- Ensure resume has clear skill sections
- Fallback derivation extracts from experience/education/certifications

### Search returns no results
- Verify profiles are in "ready" status
- Check Chroma collection is populated: `GET /admin/stats`
- Try broader filters or remove filters

### Anthropic 400 errors
- Verify `CLAUDE_MODEL` is set to a valid Messages API model
- Check API key is active and not rate-limited
- Logs show error body; share if persists

## Deployment

### Production Checklist
- [ ] Set `JWT_SECRET` to a strong random value
- [ ] Set `NEXT_PUBLIC_API_BASE` to your frontend domain
- [ ] Enable HTTPS
- [ ] Set `ANTHROPIC_API_KEY` and other secrets in env
- [ ] Use a production database (PostgreSQL recommended)
- [ ] Enable CORS for your frontend domain
- [ ] Set up log aggregation
- [ ] Monitor `/health` endpoint

### Docker (Optional)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## License

MIT (c) 2025 Hinder
