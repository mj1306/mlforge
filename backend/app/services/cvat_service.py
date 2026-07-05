import asyncio
import logging
import time

import httpx

from app.core.config import Settings
from app.domain.jobs.manager import JobManager
from app.domain.schemas.cvat import CvatState, CvatStatus

logger = logging.getLogger(__name__)

COMPOSE_PROJECT = "mlforge-cvat"


class CvatService:
    """Manages CVAT's own docker-compose stack as an optional, additive
    feature. The backend needs the Docker CLI + /var/run/docker.sock
    mounted to shell out to `docker compose` -- an accepted trade-off for a
    local-first, single-user tool (see docs/cvat-integration.md)."""

    def __init__(self, settings: Settings, job_manager: JobManager) -> None:
        self.settings = settings
        self.job_manager = job_manager
        self._lock = asyncio.Lock()
        self._last_job_id: str | None = None

    async def status(self) -> CvatStatus:
        running = await self._containers_running()
        if not running:
            return CvatStatus(state=CvatState.STOPPED, job_id=self._last_job_id)

        healthy = await self._is_healthy()
        if healthy:
            return CvatStatus(
                state=CvatState.RUNNING, url=self.settings.cvat_url, job_id=self._last_job_id
            )
        return CvatStatus(state=CvatState.STARTING, job_id=self._last_job_id)

    async def start(self, owner_id: str | None = None) -> CvatStatus:
        async with self._lock:
            current = await self.status()
            if current.state in (CvatState.RUNNING, CvatState.STARTING):
                return current

            def work(progress_callback, cancel_check):
                asyncio.run(self._run_compose("up", "-d"))
                deadline = time.monotonic() + self.settings.cvat_startup_timeout_s
                while time.monotonic() < deadline:
                    if asyncio.run(self._is_healthy()):
                        progress_callback({"state": CvatState.RUNNING.value})
                        return {"url": self.settings.cvat_url}
                    time.sleep(2)
                raise TimeoutError("CVAT did not become healthy within the startup timeout")

            record = self.job_manager.submit_cvat_lifecycle(work, owner_id=owner_id)
            self._last_job_id = str(record.id)
            return CvatStatus(state=CvatState.STARTING, job_id=self._last_job_id)

    async def stop(self) -> CvatStatus:
        async with self._lock:
            await self._run_compose("stop")
            return CvatStatus(state=CvatState.STOPPED, job_id=self._last_job_id)

    async def _run_compose(self, *args: str) -> None:
        proc = await asyncio.create_subprocess_exec(
            "docker",
            "compose",
            "-p",
            COMPOSE_PROJECT,
            "-f",
            str(self.settings.cvat_compose_file),
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            logger.error("docker compose %s failed: %s", args, stderr.decode(errors="replace"))
            raise RuntimeError(f"docker compose {' '.join(args)} failed: {stderr.decode(errors='replace')}")
        logger.info("docker compose %s: %s", args, stdout.decode(errors="replace"))

    async def _containers_running(self) -> bool:
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker",
                "compose",
                "-p",
                COMPOSE_PROJECT,
                "-f",
                str(self.settings.cvat_compose_file),
                "ps",
                "--status",
                "running",
                "-q",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _stderr = await proc.communicate()
            return bool(stdout.strip())
        except FileNotFoundError:
            logger.warning("docker CLI not available; reporting CVAT as stopped")
            return False

    async def _is_healthy(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                response = await client.get(f"{self.settings.cvat_url}/api/server/health/")
                return response.status_code == 200
        except httpx.HTTPError:
            return False
