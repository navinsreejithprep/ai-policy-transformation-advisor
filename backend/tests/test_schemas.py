import pytest
from pydantic import ValidationError

from app.models.schemas import (
    ImpactLevel,
    PolicyAnalysis,
    PolicyAssumption,
    ReviewIssue,
    ReviewResult,
    ReviewVerdict,
    Risk,
    RiskCategory,
    SourceCitation,
)


def test_policy_analysis_defaults_to_empty_collections():
    analysis = PolicyAnalysis()
    assert analysis.objectives == []
    assert analysis.assumptions == []


def test_source_citation_label_formats_page_and_section():
    citation = SourceCitation(document_name="Annual Report 2025", page_number=43, section="Outcomes")
    assert citation.label() == "Annual Report 2025, p. 43 (Outcomes)"


def test_source_citation_label_without_page_or_section():
    citation = SourceCitation(document_name="demo_policy.txt")
    assert citation.label() == "demo_policy.txt"


def test_review_result_rejects_invalid_verdict():
    with pytest.raises(ValidationError):
        ReviewResult(verdict="MAYBE")


def test_review_result_accepts_valid_verdict_and_issues():
    result = ReviewResult(
        verdict=ReviewVerdict.NEEDS_REVISION,
        issues=[ReviewIssue(target_agent="risk", issue="Missing regulatory risk.", severity=ImpactLevel.HIGH)],
    )
    assert result.verdict == ReviewVerdict.NEEDS_REVISION
    assert result.issues[0].target_agent == "risk"


def test_risk_requires_category_enum():
    with pytest.raises(ValidationError):
        Risk(
            category="not-a-real-category",
            description="x",
            likelihood=ImpactLevel.LOW,
            impact=ImpactLevel.LOW,
            mitigation="x",
            owner="x",
        )
    risk = Risk(
        category=RiskCategory.DATA,
        description="x",
        likelihood=ImpactLevel.LOW,
        impact=ImpactLevel.HIGH,
        mitigation="x",
        owner="x",
    )
    assert risk.category == RiskCategory.DATA


def test_policy_assumption_flags_evidence_backing():
    assumption = PolicyAssumption(assumption="Uptake will be immediate", is_evidence_backed=False)
    assert assumption.is_evidence_backed is False
