# MLForge

Train computer vision models from a browser UI. Upload a dataset, adjust it, tune
hyperparameters, and watch training progress live — backed by a FastAPI + PyTorch/Ultralytics
service, with an optional one-click [CVAT](https://github.com/cvat-ai/cvat) launcher for
annotating data before training.

**Features**

- **Training wizard** — pick a YOLO variant, upload a dataset (zip), preview/adjust images,
  set hyperparameters, and train, with loss curves and validation metrics streaming live.
- **Accounts** — session-based login; every user sees only their own datasets, training
  runs, and trained models, and can download their weights from the **My Models** page.
- **Live demo** — a webcam page that runs a pretrained hand-gesture model entirely in the
  browser (MediaPipe) and reacts with emoji — a zero-setup taste of what a trained vision
  model does. No account needed.
- **Annotation** — one click starts a full local CVAT stack for labeling images.

## Quick start

Requirements: [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2.

```bash
git clone <this-repo-url>
cd mlforge
cp .env.example .env
docker compose up --build
```

Then open **http://localhost:5173**, create an account, and you're in.

### GPU training

By default the backend installs CPU-only PyTorch wheels, so the golden path above works on any
machine with no GPU setup. For CUDA training:

1. Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) on the host.
2. In `.env`, set `TORCH_INDEX_URL=https://download.pytorch.org/whl/cu121` (or your CUDA version).
3. `docker compose up --build`.

On a machine with no GPU at all, remove the `deploy.resources.reservations.devices` block in
`docker-compose.yml` (Compose otherwise fails to start a service that reserves a GPU that isn't
there).

## How it works

```
┌──────────────┐        HTTP + SSE       ┌──────────────┐
│   frontend   │ ──────────────────────▶ │   backend    │
│  React/Vite  │ ◀────────────────────── │   FastAPI    │──── SQLite (users/sessions)
│   (nginx)    │   session cookie auth   │              │
└──────────────┘                         └──────┬───────┘
                                                │ shells out to docker compose
                                                ▼
                                         ┌──────────────┐
                                         │  CVAT stack  │
                                         │  (vendored)  │
                                         └──────────────┘
```

A typical training run flows like this: the browser `POST`s a dataset zip → the backend
extracts it under that user's dataset directory and finds/generates the YOLO `data.yaml` →
the browser starts a training job → the backend submits it to a worker thread and immediately
returns a job id → the browser opens `GET /jobs/{id}/stream` (Server-Sent Events) and renders
each progress event (per-batch losses, per-epoch validation metrics) as it arrives. Reloading
the page just re-subscribes to the same job; training keeps running either way. Finished
weights land in the user's models directory and appear on the **My Models** page.

### Backend (`backend/`)

FastAPI app with strict layering — each layer only imports from the ones below it:

```
app/
  api/routers/     HTTP concerns only: status codes, cookies, request/response shapes
                   (auth, datasets, processing, training, jobs, models, cvat, health)
  services/        business logic: AuthService (SQLite users/sessions, scrypt password
                   hashing), DatasetService, ProcessingService (OpenCV transforms),
                   TrainingService, CvatService
  domain/jobs/     job registry + manager (see below)
  domain/schemas/  Pydantic request/response/domain models
  ml/              YoloTrainingRunner -- wraps ultralytics.YOLO, translates its callbacks
                   into progress events; imports nothing from the app layers above
  utils/           filesystem/YAML/dataset-format helpers
core/config.py     all settings, overridable via env vars
```

Routers get their services through `app/api/deps.py`, which reads them off `app.state` — all
constructed once in `main.create_app()`. That is the testability seam: each test builds its own
app against a `tmp_path`, so there are no process-wide singletons to fight.

**Authentication.** `POST /auth/register` / `/auth/login` set an HttpOnly session cookie;
`GET /auth/me` resolves it. Users and sessions live in a single SQLite file (stdlib `sqlite3`,
scrypt-hashed passwords, only token hashes stored). Every data route requires the cookie and is
scoped to the user: datasets under `datasets/<user_id>/…`, trained models under
`models/<user_id>/…`, and job records carry an `owner_id` — another user's ids simply 404.

**Jobs.** Every long-running action (training, image processing, CVAT startup) is a job:
a `JobRecord` (UUID, status, progress, error, result) in an in-memory registry, executed on one
of two thread pools (training vs. processing, so a busy GPU never blocks CPU work). Progress
streams per-job over SSE at `GET /jobs/{id}/stream` — snapshot first, then live updates, then a
terminal event. This is deliberately in-memory rather than Redis/Celery: the app targets one
machine and one GPU, and `JobRegistry` is a `Protocol` if persistence is ever needed.

### Frontend (`frontend/`)

React 19 + Vite + Tailwind v4, served by nginx in Docker:

```
src/
  api/          one fetch/EventSource client (client.ts, sends the session cookie) plus one
                module per domain: auth, datasets, processing, training, models, cvat
  store/        Zustand stores: useAuthStore (session/user), useAppStore (training state),
                useCvatStore (CVAT status polling)
  pages/
    Auth/       login / register
    Workspace/  the training wizard (model → dataset → processing → hyperparams → train)
    Models/     "My Models": your trained weights (downloadable) + recent job activity
    Demo/       webcam hand-gesture demo (MediaPipe, lazily loaded, fully client-side)
    Annotation/ CVAT launcher
  config/models/ typed catalog of YOLO/ResNet/MobileNet variants with metadata; only YOLO
                is wired to real training today
  components/   NavBar, training widgets, small ui kit (Button/Card/Input/Modal)
```

Routes that touch per-user data are wrapped in a `RequireAuth` guard; Home and the Live Demo
are public.

## Annotation with CVAT

Click **"Launch CVAT"** on the Annotation page — the backend starts CVAT's own Docker Compose
stack (vendored, unmodified, at `docker/cvat/docker-compose.yml`) and reports back once it's
healthy, with a link to open it. See [docs/cvat-integration.md](docs/cvat-integration.md) for how
this works and its trade-offs (it requires giving the backend container access to the host's
Docker socket). CVAT manages its own accounts, separate from MLForge logins.

You can also start/stop CVAT directly without going through the app:

```bash
docker compose -p mlforge-cvat -f docker/cvat/docker-compose.yml up -d    # start
docker compose -p mlforge-cvat -f docker/cvat/docker-compose.yml stop     # stop (keeps annotation data)
```

## Repository layout

```
backend/      FastAPI + PyTorch/Ultralytics training service (see layering above)
frontend/     React + Vite web app
docker/cvat/  CVAT's docker-compose.yml, vendored unmodified from cvat-ai/cvat
docs/         architecture notes, CVAT integration details, local dev without Docker
```

See [docs/architecture.md](docs/architecture.md) for the deeper design rationale (why the job
registry exists, dataset identity, auth trade-offs), and
[docs/development.md](docs/development.md) for running each side bare-metal (without Docker)
for active development.

## Configuration

All backend settings have working defaults; override via `.env` (Docker) or env vars
(bare-metal). The interesting ones:

| Variable | Default | Meaning |
| --- | --- | --- |
| `TORCH_INDEX_URL` | *(empty = CPU wheels)* | pip index for torch; set a CUDA index for GPU |
| `TRAINING_MAX_WORKERS` | `1` | concurrent training jobs (keep 1 per GPU) |
| `PROCESSING_MAX_WORKERS` | `2` | concurrent image-processing jobs |
| `SESSION_TTL_DAYS` | `30` | login session lifetime |
| `SESSION_COOKIE_SECURE` | `false` | set `true` only behind HTTPS |
| `CVAT_URL` | `http://host.docker.internal:8080` | where the backend health-checks CVAT |
| `CORS_ALLOW_ORIGINS` | `http://localhost:5173` | comma-separated allowed origins |

The full list lives in `backend/app/core/config.py`.

## Testing

```bash
docker compose run --rm backend pytest
docker compose run --rm frontend npm test
```

Both suites also run without Docker — see [docs/development.md](docs/development.md). The
backend's fast suite needs no GPU and stubs out real training; `pytest -m slow` runs a real
1-epoch Ultralytics training.

## A note on scope

MLForge is a **local-first tool**: you run it on your own machine for yourself or your lab.
Accounts keep each user's work separate and private, but the backend is not hardened for
hosting on the open internet (see the Docker-socket trade-off in
[docs/cvat-integration.md](docs/cvat-integration.md) before exposing it anywhere public).
