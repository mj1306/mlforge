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
RUN if [ -n "$TORCH_INDEX_URL" ]; then \
      pip install --no-cache-dir --extra-index-url "$TORCH_INDEX_URL" .; \
    else \
      pip install --no-cache-dir .; \
    fi

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
