# MLForge

Train computer vision models from a browser UI. Upload a dataset, adjust it, tune
hyperparameters, and watch training progress live -- backed by a FastAPI + PyTorch/Ultralytics
service, with an optional one-click [CVAT](https://github.com/cvat-ai/cvat) launcher for
annotating data before training.

## Quick start

Requirements: [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2.

```bash
git clone <this-repo-url>
cd mlforge
cp .env.example .env
docker compose up --build
```

Then open **http://localhost:5173**.

### GPU training

By default the backend installs CPU-only PyTorch wheels, so the golden path above works on any
machine with no GPU setup. For CUDA training:

1. Install the [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) on the host.
2. In `.env`, set `TORCH_INDEX_URL=https://download.pytorch.org/whl/cu121` (or your CUDA version).
3. `docker compose up --build`.

On a machine with no GPU at all, remove the `deploy.resources.reservations.devices` block in
`docker-compose.yml` (Compose otherwise fails to start a service that reserves a GPU that isn't
there).

## Annotation with CVAT

Click **"Launch CVAT"** on the Annotation page -- the backend starts CVAT's own Docker Compose
stack (vendored, unmodified, at `docker/cvat/docker-compose.yml`) and reports back once it's
healthy, with a link to open it. See [docs/cvat-integration.md](docs/cvat-integration.md) for how
this works and its trade-offs (it requires giving the backend container access to the host's
Docker socket).

You can also start/stop CVAT directly without going through the app:

```bash
docker compose -p mlforge-cvat -f docker/cvat/docker-compose.yml up -d    # start
docker compose -p mlforge-cvat -f docker/cvat/docker-compose.yml stop     # stop (keeps annotation data)
```

## Repository layout

```
backend/    FastAPI + PyTorch/Ultralytics training service
frontend/   React + Vite web app
docker/cvat/  CVAT's docker-compose.yml, vendored unmodified from cvat-ai/cvat
docs/       Architecture notes, CVAT integration details, local dev without Docker
```

See [docs/architecture.md](docs/architecture.md) for how the pieces fit together, and
[docs/development.md](docs/development.md) for running each side bare-metal (without Docker) for
active development.

## Testing

```bash
docker compose run --rm backend pytest
docker compose run --rm frontend npm test
```

Both suites also run without Docker -- see docs/development.md.
