
import pytest

from crm_automation import (
    LeadInput,
    create_workflow,
    transition,
    create_workflow_result,
    create_workflow_trace,
)


@pytest.fixture
def sample_lead():
    return LeadInput(
        lead_id="LEAD-TEST-001",
        name="Test Lead",
        email="test@example.com",
        company="Test Company",
        source="website",
        score=75,
    )


@pytest.fixture
def sample_run(sample_lead):
    return create_workflow(
        "RUN-TEST-001",
        "LEAD-TEST-001",
        sample_lead,
    )


def test_workflow_creation(sample_run):
    assert sample_run.state == "created"
    assert sample_run.business_key == "LEAD-TEST-001"


def test_legal_transition(sample_run):
    transition(sample_run, "start")

    assert sample_run.state == "running"


def test_illegal_transition_is_rejected(sample_run):
    with pytest.raises(ValueError, match="Illegal transition"):
        transition(sample_run, "complete")


def test_workflow_pause_and_resume(sample_run):
    transition(sample_run, "start")
    transition(sample_run, "pause")

    assert sample_run.state == "waiting"

    transition(sample_run, "resume")

    assert sample_run.state == "running"


def test_workflow_failure_transition(sample_run):
    transition(sample_run, "start")
    transition(sample_run, "fail")

    assert sample_run.state == "needs_review"


def test_workflow_result(sample_run):
    transition(sample_run, "start")
    transition(sample_run, "complete")

    result = create_workflow_result(sample_run)

    assert result.status == "completed"
    assert result.business_key == "LEAD-TEST-001"


def test_workflow_trace_contains_events(sample_run):
    transition(sample_run, "start")

    trace = create_workflow_trace(sample_run)

    assert trace.run_id == "RUN-TEST-001"
    assert len(trace.events) >= 2
    assert trace.events[-1]["event"] == "start"
