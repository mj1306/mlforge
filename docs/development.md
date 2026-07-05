# Local development without Docker

## Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Env vars (all optional, see `app/core/config.py` for defaults): `DATASET_DIR`, `MODELS_DIR`,
`LOGS_DIR`, `CORS_ALLOW_ORIGINS`, `TRAINING_MAX_WORKERS`, `PROCESSING_MAX_WORKERS`, `CVAT_URL`,
`CVAT_COMPOSE_FILE`, `CVAT_STARTUP_TIMEOUT_S`.

Tests:

```bash
pytest                    # fast suite (no GPU, no real training)
pytest -m slow            # includes real 1-epoch Ultralytics training, slow
```

## Frontend

```bash
cd frontend
npm install
cp .env.example .env      # VITE_API_BASE_URL=http://localhost:8000
npm run dev                # http://localhost:5173
```

Tests:

```bash
npm test          # vitest run
npm run test:watch
```

## Running both together

Start the backend (port 8000) and frontend (port 5173) as above in two terminals -- no Docker
needed for day-to-day iteration. CVAT still requires Docker (it's CVAT's own multi-container
stack); in bare-metal dev mode `CVAT_URL` defaults to `http://localhost:8080`, matching a CVAT
stack started directly via `docker compose -p mlforge-cvat -f docker/cvat/docker-compose.yml up -d`.
