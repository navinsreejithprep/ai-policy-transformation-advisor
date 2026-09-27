import time

from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import (
    BenchmarkReport,
    EvidenceReport,
    FinalReport,
    ImplementationPlan,
    NinetyDayPlan,
    PolicyAnalysis,
    ReviewResult,
    ReviewVerdict,
    RiskRegister,
    StakeholderMatrix,
    TwelveMonthRoadmap,
)


def _fake_report() -> FinalReport:
    return FinalReport(
        executive_summary="A short fake executive summary for testing.",
        policy_analysis=PolicyAnalysis(objectives=["Improve access"]),
        evidence=EvidenceReport(evidence_gaps=["No data on cost."]),
        stakeholders=StakeholderMatrix(),
        risks=RiskRegister(),
        benchmarks=BenchmarkReport(),
        implementation=ImplementationPlan(
            ninety_day_plan=NinetyDayPlan(),
            twelve_month_roadmap=TwelveMonthRoadmap(),
            governance_model="Steering committee.",
        ),
        review=ReviewResult(verdict=ReviewVerdict.PASS),
    )


def test_start_analysis_rejects_short_text(isolated_kb):
    with TestClient(app) as client:
        resp = client.post("/analysis/start", json={"policy_text": "too short"})
        assert resp.status_code == 422


def test_unknown_job_returns_404(isolated_kb):
    with TestClient(app) as client:
        assert client.get("/analysis/unknown-id").status_code == 404
        assert client.get("/analysis/unknown-id/report").status_code == 404


def test_analysis_job_lifecycle(isolated_kb, monkeypatch):
    monkeypatch.setattr("app.api.analysis.run_analysis_pipeline", lambda policy_text, on_stage=None: _fake_report())

    with TestClient(app) as client:
        start_resp = client.post(
            "/analysis/start",
            json={"policy_text": "A policy about improving digital access for citizens over three years."},
        )
        assert start_resp.status_code == 200
        job_id = start_resp.json()["job_id"]

        report = None
        for _ in range(50):
            status_resp = client.get(f"/analysis/{job_id}")
            assert status_resp.status_code == 200
            if status_resp.json()["stage"] == "complete":
                report = client.get(f"/analysis/{job_id}/report")
                break
            time.sleep(0.05)

        assert report is not None
        assert report.status_code == 200
        assert report.json()["executive_summary"].startswith("A short fake")

        sources_resp = client.get(f"/analysis/{job_id}/sources")
        assert sources_resp.status_code == 200


def test_report_not_ready_returns_409(isolated_kb, monkeypatch):
    started = []

    def slow_pipeline(policy_text, on_stage=None):
        started.append(True)
        time.sleep(1)
        return _fake_report()

    monkeypatch.setattr("app.api.analysis.run_analysis_pipeline", slow_pipeline)

    with TestClient(app) as client:
        start_resp = client.post(
            "/analysis/start",
            json={"policy_text": "A policy about improving digital access for citizens over three years."},
        )
        job_id = start_resp.json()["job_id"]
        report_resp = client.get(f"/analysis/{job_id}/report")
        assert report_resp.status_code == 409
