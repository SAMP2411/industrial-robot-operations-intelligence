from __future__ import annotations

import argparse
import os
import socket

from packages.domain_models.database import SessionLocal
from packages.job_queue import DurableJobQueue


def default_handlers() -> dict:
    """Handlers are registered by deployments; unknown work fails visibly and retries."""
    return {}


def run_once(worker_id: str | None = None, handlers: dict | None = None) -> bool:
    identity = worker_id or f"{socket.gethostname()}:{os.getpid()}"
    with SessionLocal() as session:
        return DurableJobQueue(session).execute_one(identity, handlers or default_handlers()) is not None


def main() -> int:
    parser = argparse.ArgumentParser(description="Run one durable incident-intelligence background job")
    parser.add_argument("--worker-id")
    args = parser.parse_args()
    return 0 if run_once(args.worker_id) else 2


if __name__ == "__main__":
    raise SystemExit(main())
