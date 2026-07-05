# Architecture

## Overview

```
┌─────────────┐        HTTP/SSE        ┌──────────────┐
│  frontend    │ ─────────────────────▶ │   backend    │
│  React/Vite  │ ◀───────────────────── │   FastAPI    │
│  (nginx)     │                        │              │
└─────────────┘                        └──────┬───────┘
                                               │ shells out to
                                               │ docker compose
                                               ▼
                                        ┌──────────────┐
                                        │ CVAT stack   │
                                        │ (submodule)  │
                                        └──────────────┘
```

The frontend never talks to CVAT directly -- it calls the backend's `/cvat/*` endpoints, and the
backend manages CVAT's own Docker Compose project as a separate, independent stack.

## Backend layering

```
app/
  api/routers/     HTTP concerns only (request/response, status codes)
  services/        business logic (dataset, processing, training, cvat)
  domain/schemas/  Pydantic request/response/domain models
  domain/jobs/     job registry + manager (see below)
  ml/              YOLO training wrapper -- no FastAPI/job-registry imports
  utils/           small filesystem/YAML/dataset-format helpers
```

Each router depends only on a service (via `app/api/deps.py`, which reads services off
`app.state` -- set up once in `main.create_app()`). This is what makes the backend testable:
tests build their own `create_app(settings=...)` pointed at a `tmp_path`, instead of fighting a
process-wide singleton.

## Job registry (why it exists)

The previous backend tracked training progress in one global mutable dict shared by the whole
process, plus a couple of other bare module-level globals for "the last uploaded dataset" and
"the currently running training thread." That meant: only one training run could ever be tracked,
uploading a second dataset silently redirected in-flight processing/training calls, and there was
no way to know if training had failed vs. hung.

Instead, every training/processing/CVAT-lifecycle action gets a `JobRecord` (UUID, status,
progress dict, error, result), managed by `InMemoryJobRegistry` + `JobManager`
(`app/domain/jobs/`). Progress streams per-job over SSE at `GET /jobs/{id}/stream`: the client
gets the current snapshot immediately, then live updates, then a terminal event. A page
reload/reconnect just re-subscribes to the same job -- the training thread keeps running
regardless of whether anyone is watching.

`JobManager` uses two separate `ThreadPoolExecutor`s (training vs. processing) so a single GPU
training slot doesn't block CPU-bound image processing from running at the same time, without
pretending multiple GPU jobs can run concurrently.

This is intentionally in-memory, not Redis/Celery -- there's no multi-worker or cross-process
requirement at this app's scale (single machine, single GPU). `JobRegistry` is a `Protocol`, so
swapping in a persistent backing store later wouldn't require touching route code.

## Dataset identity

Every dataset gets an explicit `dataset_id` on upload. All later calls (processing, training) take
that id as a required parameter -- there's no shared "last uploaded dataset" state, so uploading a
second dataset can never silently redirect an in-flight request for the first one.

## Frontend

- `src/api/*` -- one HTTP client (`client.ts`) plus one module per domain (datasets/training/
  processing/cvat). No component talks to `fetch`/`EventSource` directly.
- `src/store/` -- Zustand (`useAppStore` for training/current-model, `useCvatStore` for CVAT
  status, which needs a polling loop while CVAT is starting up).
- `src/pages/Workspace/` -- the training wizard (select model → upload dataset → image
  processing → hyperparameters → train), each step a self-contained component.
- `src/config/models/` -- a typed registry of YOLO/ResNet/MobileNet variants with metadata
  (params, FLOPs, mAP, etc). Only YOLO is wired to real training today; the others are kept as a
  ready-made catalog for when their training paths are implemented.
