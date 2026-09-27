import threading

from fastapi import APIRouter, HTTPException

from ..crew.runner import AnalysisError, run_analysis_pipeline
from ..models.schemas import (
    AnalysisJobStatus,
    AnalysisStage,
    AnalysisStartRequest,
    AnalysisStartResponse,
    FinalReport,
)
from ..services.jobs import job_store
from ..utils.logging import get_logger

router = APIRouter(prefix="/analysis", tags=["analysis"])
logger = get_logger(__name__)


def _run_job(job_id: str, policy_text: str):
    def on_stage(stage: AnalysisStage):
        job_store.set_stage(job_id, stage)

    try:
        report = run_analysis_pipeline(policy_text, on_stage=on_stage)
        job_store.set_report(job_id, report)
    except AnalysisError as exc:
        logger.error("analysis job failed job_id=%s error=%s", job_id, exc)
        job_store.set_error(job_id, str(exc))
    except Exception as exc:  # unexpected failure — never leave the job hanging
        logger.error("analysis job crashed job_id=%s error=%s", job_id, exc)
        job_store.set_error(job_id, f"Unexpected error: {exc}")


@router.post("/start", response_model=AnalysisStartResponse)
def start_analysis(request: AnalysisStartRequest):
    job = job_store.create()
    thread = threading.Thread(target=_run_job, args=(job.job_id, request.policy_text), daemon=True)
    thread.start()
    return AnalysisStartResponse(job_id=job.job_id, status=job.stage)


@router.get("/{job_id}", response_model=AnalysisJobStatus)
def get_status(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(404, "Unknown analysis job id.")
    return AnalysisJobStatus(
        job_id=job.job_id,
        stage=job.stage,
        progress_pct=job.progress_pct,
        error=job.error,
        created_at=job.created_at,
        updated_at=job.updated_at,
    )


@router.get("/{job_id}/report", response_model=FinalReport)
def get_report(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(404, "Unknown analysis job id.")
    if job.stage == AnalysisStage.FAILED:
        raise HTTPException(500, job.error or "Analysis failed.")
    if not job.report:
        raise HTTPException(409, f"Analysis is not complete yet (stage: {job.stage.value}).")
    return job.report


@router.get("/{job_id}/sources")
def get_sources(job_id: str):
    job = job_store.get(job_id)
    if not job:
        raise HTTPException(404, "Unknown analysis job id.")
    if not job.report:
        raise HTTPException(409, f"Analysis is not complete yet (stage: {job.stage.value}).")
    return {"sources": [s.model_dump() for s in job.report.sources]}
