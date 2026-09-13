from __future__ import annotations

from collections import Counter, defaultdict
import json
import logging
import time
import uuid

from fastapi import Request, Response


logger = logging.getLogger("rfii.api")
REQUESTS = Counter()
ERRORS = Counter()
LATENCY = defaultdict(float)
LOGIN_FAILURES = 0


async def request_observability(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    started = time.perf_counter()
    status = 500
    try:
        response: Response = await call_next(request); status = response.status_code; return response
    finally:
        duration = time.perf_counter() - started
        route = request.url.path
        REQUESTS[route] += 1; LATENCY[route] += duration
        if status >= 400: ERRORS[route] += 1
        principal = getattr(request.state, "principal", {})
        logger.info(json.dumps({
            "event": "http_request", "request_id": request_id, "user_id": principal.get("user_id"),
            "customer_id": principal.get("customer_id"), "route": route, "status": status,
            "duration_ms": round(duration * 1000, 2),
            "incident_id": request.path_params.get("incident_id"), "job_id": request.path_params.get("job_id"),
            "ingestion_run_id": request.path_params.get("run_id"),
        }, separators=(",", ":")))


def prometheus_text(*, active_jobs: int, failed_jobs: int, storage_bytes: int) -> str:
    lines = [
        "# TYPE rfii_api_requests_total counter",
        *(f'rfii_api_requests_total{{route="{route}"}} {count}' for route, count in sorted(REQUESTS.items())),
        "# TYPE rfii_api_errors_total counter",
        *(f'rfii_api_errors_total{{route="{route}"}} {count}' for route, count in sorted(ERRORS.items())),
        f"rfii_jobs_active {active_jobs}", f"rfii_jobs_failed {failed_jobs}", f"rfii_storage_bytes {storage_bytes}",
        f"rfii_login_failures_total {LOGIN_FAILURES}",
    ]
    return "\n".join(lines) + "\n"
