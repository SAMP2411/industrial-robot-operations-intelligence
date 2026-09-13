from __future__ import annotations

from datetime import datetime, timedelta, timezone
import traceback
from typing import Callable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from packages.domain_models.models import Job, JobAttempt, JobEvent


TERMINAL = {"succeeded", "failed", "cancelled"}


class DurableJobQueue:
    """Database-backed queue with auditable attempts and retry state."""

    def __init__(self, session: Session):
        self.session = session

    def enqueue(self, job_type: str, payload: dict, idempotency_key: str, max_retries: int = 3, customer_id: str | None = None) -> Job:
        existing = self.session.scalar(
            select(Job).where(Job.job_type == job_type, Job.idempotency_key == idempotency_key)
        )
        if existing:
            return existing
        job = Job(job_type=job_type, payload=payload, idempotency_key=idempotency_key, max_retries=max_retries, customer_id=customer_id)
        self.session.add(job)
        try:
            self.session.flush()
        except IntegrityError:
            self.session.rollback()
            return self.session.scalar(
                select(Job).where(Job.job_type == job_type, Job.idempotency_key == idempotency_key)
            )
        self.session.add(JobEvent(job_id=job.id, event_type="queued", details={}))
        self.session.commit()
        return job

    def claim(self, worker_id: str) -> Job | None:
        now = datetime.now(timezone.utc)
        query = (
            select(Job)
            .where(Job.status.in_(("queued", "retrying")), Job.available_at <= now)
            .order_by(Job.created_at)
            .limit(1)
            .with_for_update(skip_locked=True)
        )
        job = self.session.scalar(query)
        if not job:
            return None
        job.status = "running"
        job.heartbeat_at = now
        attempt = JobAttempt(job_id=job.id, attempt_number=job.retry_count + 1, status="running", worker_id=worker_id)
        self.session.add_all([attempt, JobEvent(job_id=job.id, event_type="running", details={"worker_id": worker_id})])
        self.session.commit()
        return job

    def heartbeat(self, job: Job) -> None:
        if job.status != "running":
            raise ValueError("only running jobs can heartbeat")
        job.heartbeat_at = datetime.now(timezone.utc)
        self.session.commit()

    def complete(self, job: Job, result: dict | None = None) -> None:
        job.status = "succeeded"
        self._finish_attempt(job, "succeeded")
        self.session.add(JobEvent(job_id=job.id, event_type="succeeded", details=result or {}))
        self.session.commit()

    def fail(self, job: Job, exc: BaseException) -> None:
        details = "".join(traceback.format_exception(exc))
        job.retry_count += 1
        job.error_summary = str(exc)[:500]
        job.error_details = details
        status = "retrying" if job.retry_count <= job.max_retries else "failed"
        job.status = status
        if status == "retrying":
            job.available_at = datetime.now(timezone.utc) + timedelta(seconds=min(300, 2 ** job.retry_count))
        self._finish_attempt(job, status, details)
        self.session.add(JobEvent(job_id=job.id, event_type=status, details={"error_summary": job.error_summary}))
        self.session.commit()

    def cancel(self, job: Job, reason: str) -> None:
        if job.status in TERMINAL:
            return
        job.status = "cancelled"
        self._finish_attempt(job, "cancelled", reason)
        self.session.add(JobEvent(job_id=job.id, event_type="cancelled", details={"reason": reason}))
        self.session.commit()

    def execute_one(self, worker_id: str, handlers: dict[str, Callable[[dict], dict | None]]) -> Job | None:
        job = self.claim(worker_id)
        if not job:
            return None
        try:
            if job.job_type not in handlers:
                raise KeyError(f"no handler for job type {job.job_type}")
            self.complete(job, handlers[job.job_type](job.payload))
        except BaseException as exc:
            self.fail(job, exc)
        return job

    def _finish_attempt(self, job: Job, status: str, details: str | None = None) -> None:
        attempt = self.session.scalar(
            select(JobAttempt).where(JobAttempt.job_id == job.id, JobAttempt.status == "running").order_by(JobAttempt.created_at.desc())
        )
        if attempt:
            attempt.status = status
            attempt.finished_at = datetime.now(timezone.utc)
            attempt.error_details = details
