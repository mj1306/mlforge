# CVAT integration

## How it's vendored

CVAT is included as a git submodule at `docker/cvat/cvat`, pinned to a specific release tag
(currently `v2.69.0`), used **unmodified** -- we run its own `docker-compose.yml` directly rather
than copying/merging it into our own compose file. CVAT's stack (server, db, redis, several rq
workers, UI, traefik, opa, clickhouse, grafana) is non-trivial and changes across releases;
vendoring a copy would drift silently every time we wanted to bump versions. A submodule keeps
"what CVAT version are we on" a single pinned commit, and `git submodule update --remote` is the
whole upgrade process.

If you clone this repo without `--recurse-submodules`, the `docker/cvat/cvat` directory will be
empty -- run `git submodule update --init` once to fetch it. This is only needed if you actually
want to use the annotation feature; the rest of the app doesn't depend on it.

## How the backend manages it

`app/services/cvat_service.py`:

- **`status()`** -- checks whether CVAT's containers are running (`docker compose ps --status
  running`), then probes `GET {CVAT_URL}/api/server/health/` to distinguish "containers up but
  not ready yet" (`starting`) from actually `running`.
- **`start()`** -- runs `docker compose -p mlforge-cvat -f <submodule>/docker-compose.yml up -d` via
  `asyncio.create_subprocess_exec` (never `shell=True`), tracked as a job so the frontend can poll
  the same way it polls training jobs, and polls health until it's up or `CVAT_STARTUP_TIMEOUT_S`
  elapses.
- **`stop()`** -- runs `docker compose ... stop`, not `down` -- this preserves CVAT's Postgres
  volumes (your annotations) between sessions. A full teardown would need `docker compose ...
  down -v`, which this app doesn't expose as a casual one-click action on purpose.

## The trade-off worth knowing about

For the backend container to run `docker compose` against CVAT, it needs the Docker CLI
installed and the host's `/var/run/docker.sock` bind-mounted in (see `docker-compose.yml`). That
gives the backend container effectively root-equivalent control over the host's Docker daemon.

That's an acceptable trade-off **for this app's actual scope**: a local-first, single-user tool
you run on your own machine, not a multi-tenant hosted service. If this ever becomes something
other users' untrusted requests can reach, that socket mount needs to be reconsidered (e.g., drop
the backend's ability to control Docker entirely, and have `/cvat/start` just return the copyable
`docker compose up -d` command for the user to run themselves).

## Networking note

`CVAT_URL` defaults to `http://host.docker.internal:8080` when running via `docker compose up`
(the backend container reaching CVAT's traefik, which publishes port 8080 on the host) and to
`http://localhost:8080` for bare-metal dev (see `docs/development.md`). `host.docker.internal` is
resolved via the `extra_hosts: host-gateway` entry in `docker-compose.yml`, which works on both
Docker Desktop and Linux Docker Engine 20.10+.
