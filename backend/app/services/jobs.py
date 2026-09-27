"""In-memory analysis job store.

Design choice: a POC-scale in-memory dict is enough here — jobs don't need to
survive a restart. A production version would back this with Redis/Postgres so
job status survives process restarts and works across multiple backend workers.
"""
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from ..models.schemas import AnalysisStage, FinalReport

_STAGE_PROGRESS = {
    AnalysisStage.QUEUED: 0,
    AnalysisStage.POLICY_ANALYSIS: 10,
    AnalysisStage.EVIDENCE_RESEARCH: 25,
    AnalysisStage.STAKEHOLDER_ANALYSIS: 40,
    AnalysisStage.RISK_ASSESSMENT: 55,
    AnalysisStage.BENCHMARKING: 65,
    AnalysisStage.IMPLEMENTATION_PLANNING: 75,
    AnalysisStage.INDEPENDENT_REVIEW: 85,
    AnalysisStage.REVISION: 90,
    AnalysisStage.SYNTHESIS: 95,
    AnalysisStage.COMPLETE: 100,
    AnalysisStage.FAILED: 100,
}


@dataclass
class Job:
    job_id: str
    stage: AnalysisStage = AnalysisStage.QUEUED
    error: Optional[str] = None
    report: Optional[FinalReport] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def progress_pct(self) -> int:
        return _STAGE_PROGRESS.get(self.stage, 0)


class JobStore:
    def __init__(self):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self) -> Job:
        job = Job(job_id=uuid.uuid4().hex)
        with self._lock:
            self._jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[Job]:
        with self._lock:
            return self._jobs.get(job_id)

    def set_stage(self, job_id: str, stage: AnalysisStage):
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.stage = stage
                job.updated_at = datetime.now(timezone.utc)

    def set_error(self, job_id: str, error: str):
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.stage = AnalysisStage.FAILED
                job.error = error
                job.updated_at = datetime.now(timezone.utc)

    def set_report(self, job_id: str, report: FinalReport):
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                job.report = report
                job.stage = AnalysisStage.COMPLETE
                job.updated_at = datetime.now(timezone.utc)


job_store = JobStore()
