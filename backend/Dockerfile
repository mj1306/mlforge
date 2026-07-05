# Build with --build-arg TORCH_INDEX_URL=https://download.pytorch.org/whl/cu121
# (or your CUDA version) for GPU training; defaults to CPU-only wheels so the
# image builds and runs anywhere with no GPU/driver assumptions.
ARG TORCH_INDEX_URL=""

FROM python:3.11-slim AS builder

ARG TORCH_INDEX_URL
WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# torch/torchvision/torchaudio are installed separately, first, from an
# explicit --index-url (not --extra-index-url -- pip doesn't reliably
# prefer one index over another when both have a matching version, so a
# full index swap is needed to actually get the CPU build). This matters
# because PyPI's default Linux wheel for torch bundles the full CUDA
# runtime (several hundred MB of nvidia-cusolver/cusparse/etc. wheels)
# even with no GPU involved -- "no TORCH_INDEX_URL set" must mean CPU, not
# "whatever pip's default index gives you." Pass --build-arg
# TORCH_INDEX_URL=https://download.pytorch.org/whl/cu121 (or your CUDA
# version) for GPU wheels instead.
RUN pip install --no-cache-dir torch torchvision \
      --index-url "${TORCH_INDEX_URL:-https://download.pytorch.org/whl/cpu}"
# Everything else (fastapi, ultralytics, opencv, ...) comes from regular
# PyPI; torch is already satisfied so pip won't touch it.
RUN pip install --no-cache-dir .

FROM python:3.11-slim AS runtime

# docker.io gives us the `docker` CLI to talk to the host daemon via the
# mounted socket (see docker-compose.yml); the compose v2 plugin isn't in
# Debian's default repos, so it's fetched directly from Docker's releases.
# Both are only used by the optional CVAT launch feature -- the rest of the
# app doesn't need them.
ARG COMPOSE_VERSION=v2.29.7
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    docker.io \
    curl \
    && mkdir -p /usr/local/lib/docker/cli-plugins \
    && curl -fsSL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-x86_64" \
       -o /usr/local/lib/docker/cli-plugins/docker-compose \
    && chmod +x /usr/local/lib/docker/cli-plugins/docker-compose \
    && apt-get purge -y curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY app ./app

RUN mkdir -p /data/datasets /data/models /data/logs && chown -R appuser:appuser /data /app
USER appuser

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
