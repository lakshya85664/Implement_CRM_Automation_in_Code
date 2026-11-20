
import pytest

from crm_automation import (
    LeadInput,
    CRMStore,
    execute_crm_with_recovery,
    run_task3_fixture,
)


@pytest.fixture
def sample_lead():
    return LeadInput(
        lead_id="LEAD-301",
        name="Recovery Test",
        email="recovery-test@example.com",
        company="Recovery Company",
        source="website",
        score=90,
    )


@pytest.fixture
def store():
    return CRMStore()


def test_timeout_retries_then_completes(sample_lead, store):
    result = execute_crm_with_recovery(
        sample_lead,
        store,
        ["timeout", "timeout", "success"],
        max_retries=2,
    )

    assert result.status == "completed"
    assert result.attempts == 3
    assert result.crm_record_id == "CRM-0001"
    assert result.follow_up_task_id == "FOLLOWUP-0001"
    assert len(store.records) == 1
    assert len(store.follow_up_tasks) == 1


def test_retry_limit_is_enforced(sample_lead, store):
    result = execute_crm_with_recovery(
        sample_lead,
        store,
        ["timeout", "timeout", "timeout", "success"],
        max_retries=2,
    )

    assert result.status == "needs_review"
    assert result.attempts == 3
    assert result.failure_category == "timeout"
    assert len(store.records) == 0
    assert len(store.follow_up_tasks) == 0


def test_malformed_response_is_not_retried(sample_lead, store):
    result = execute_crm_with_recovery(
        sample_lead,
        store,
        ["malformed_response", "success"],
    )

    assert result.status == "needs_review"
    assert result.attempts == 1
    assert result.failure_category == "malformed_response"
    assert len(store.records) == 0


def test_permanent_failure_is_not_retried(sample_lead, store):
    result = execute_crm_with_recovery(
        sample_lead,
        store,
        ["permanent", "success"],
    )

    assert result.status == "needs_review"
    assert result.attempts == 1
    assert result.failure_category == "permanent"
    assert len(store.records) == 0


def test_duplicate_trigger_is_blocked(sample_lead, store):
    result = execute_crm_with_recovery(
        sample_lead,
        store,
        ["duplicate"],
    )

    assert result.status == "duplicate_prevented"
    assert result.action == "duplicate_prevented"
    assert result.side_effects == 0
    assert len(store.records) == 0
    assert len(store.follow_up_tasks) == 0


def test_timeout_after_commit_recovers_without_duplicate_side_effects(
    sample_lead, store
):
    result = execute_crm_with_recovery(
        sample_lead,
        store,
        ["timeout_after_commit"],
    )

    assert result.status == "completed"
    assert result.recovered_existing is True
    assert result.failure_category == "timeout"
    assert result.side_effects == 2
    assert len(store.records) == 1
    assert len(store.follow_up_tasks) == 1


def test_replay_after_completion_does_not_repeat_side_effects(
    sample_lead, store
):
    first = execute_crm_with_recovery(
        sample_lead,
        store,
        ["success"],
    )

    replay = execute_crm_with_recovery(
        sample_lead,
        store,
        ["success"],
    )

    assert first.status == "completed"
    assert replay.status == "duplicate_prevented"
    assert replay.side_effects == 0
    assert len(store.records) == 1
    assert len(store.follow_up_tasks) == 1


def test_negative_retry_limit_is_rejected(sample_lead, store):
    with pytest.raises(ValueError, match="max_retries"):
        execute_crm_with_recovery(
            sample_lead,
            store,
            ["success"],
            max_retries=-1,
        )


def test_task3_fixture_generates_evidence():
    from pathlib import Path

    results = run_task3_fixture()

    assert results["timeout_recovery"]["result"]["status"] == "completed"
    assert results["malformed_response"]["result"]["status"] == "needs_review"
    assert results["permanent_failure"]["result"]["status"] == "needs_review"
    assert results["timeout_after_commit"]["result"]["recovered_existing"] is True
    assert results["duplicate_replay"]["replay_result"]["status"] == "duplicate_prevented"

    assert Path("outputs/task3_crm_recovery.json").exists()
    assert Path("traces/task3_crm_recovery_traces.json").exists()
