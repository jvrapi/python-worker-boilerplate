"""Health check HTTP server using aiohttp."""

import asyncio
from typing import Callable, Optional

try:
    from aiohttp import web
except ImportError:
    raise

from infra.adapters.logging import logger


class HealthServer:
    """
    Lightweight HTTP server for Kubernetes health checks.

    Provides liveness and readiness probes.
    """

    def __init__(
        self,
        host: str = "0.0.0.0",
        port: int = 8080,
        health_check: Optional[Callable[[], bool]] = None,
    ):
        """
        Initialize health server.

        Args:
            host: Server host
            port: Server port
            health_check: Optional callable that returns health status
        """
        if web is None:
            raise ImportError("aiohttp is required. Install with: pip install aiohttp")

        self.host = host
        self.port = port
        self.health_check = health_check or (lambda: True)
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self._is_ready = False

        self.app.router.add_get("/healthcheck", self._health_handler)

        logger.info("health_server_initialized", host=host, port=port)

    async def _health_handler(self, request: web.Request) -> web.Response:
        """Combined health check endpoint."""
        is_healthy = self.health_check()

        if is_healthy and self._is_ready:
            return web.json_response({"status": "healthy", "ready": True}, status=200)
        else:
            return web.json_response(
                {"status": "unhealthy", "ready": self._is_ready}, status=503
            )

    async def _liveness_handler(self, request: web.Request) -> web.Response:
        """
        Liveness probe endpoint.

        Indicates if the application is running.
        Kubernetes will restart the pod if this fails.
        """
        is_alive = self.health_check()

        if is_alive:
            return web.json_response({"status": "alive"}, status=200)
        else:
            return web.json_response({"status": "dead"}, status=503)

    async def _readiness_handler(self, request: web.Request) -> web.Response:
        """
        Readiness probe endpoint.

        Indicates if the application is ready to receive traffic.
        Kubernetes will not send traffic if this fails.
        """
        if self._is_ready:
            return web.json_response({"status": "ready"}, status=200)
        else:
            return web.json_response({"status": "not_ready"}, status=503)

    def mark_ready(self) -> None:
        """Mark the service as ready."""
        self._is_ready = True
        logger.info("service_marked_ready")

    def mark_not_ready(self) -> None:
        """Mark the service as not ready."""
        self._is_ready = False
        logger.info("service_marked_not_ready")

    async def start(self) -> None:
        """Start the health check server."""
        try:
            import logging

            logging.getLogger("aiohttp.access").setLevel(logging.WARNING)

            self.runner = web.AppRunner(self.app)
            await self.runner.setup()

            site = web.TCPSite(self.runner, self.host, self.port)
            await site.start()

            logger.info("health_server_started", host=self.host, port=self.port)

            while True:
                await asyncio.sleep(3600)

        except asyncio.CancelledError:
            logger.info("health_server_cancelled")
        except Exception as e:
            logger.error("health_server_error", error=str(e), exc_info=True)
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop the health check server."""
        if self.runner:
            await self.runner.cleanup()
            logger.info("health_server_stopped")
