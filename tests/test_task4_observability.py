
import json

from crm_automation import (
    LeadInput,
    CRMStore,
    FakeCRMAdapter,
    CRMObservability,
    run_crm_with_adapter,
    get_crm_status,
    get_crm_trace,
    redact_secrets,
    run_task4_fixture,
)


def sample_lead():
    return LeadInput(
        lead_id="LEAD-401",
        name="Meera Desai",
        email="meera@example.com",
        company="Meera Technologies",
        source="website",
        score=92,
    )


def test_injected_fake_adapter_completes_workflow():
    adapter = FakeCRMAdapter()
    metrics = CRMObservability()

    result = run_crm_with_adapter(
        sample_lead(),
        adapter,
        metrics,
        "RUN-TEST-401",
    )

    assert result["status"] == "completed"
    assert result["crm_record_id"] == "CRM-0001"
    assert result["follow_up_task_id"] == "FOLLOWUP-0001"


def test_adapter_failure_is_observable():
    adapter = FakeCRMAdapter(fail_record_creation=True)
    metrics = CRMObservability()

    result = run_crm_with_adapter(
        sample_lead(),
        adapter,
        metrics,
        "RUN-TEST-402",
    )

    assert result["status"] == "needs_review"
    assert result["error"] == "External CRM dependency timed out"
    assert metrics.failures == 1

    events = get_crm_trace(metrics, "RUN-TEST-402")
    assert any(
        event["event"] == "dependency_timeout"
        for event in events
    )


def test_metrics_are_reported():
    adapter = FakeCRMAdapter()
    metrics = CRMObservability()

    run_crm_with_adapter(
        sample_lead(),
        adapter,
        metrics,
        "RUN-TEST-403",
    )

    report = metrics.report()

    assert report["runs"] == 1
    assert report["successes"] == 1
    assert report["failures"] == 0
    assert report["success_rate_percent"] == 100.0
    assert report["crm_records_created"] == 1
    assert report["follow_up_tasks_created"] == 1
    assert report["average_duration_ms"] >= 0


def test_status_exposes_dependency_health():
    adapter = FakeCRMAdapter()
    metrics = CRMObservability()

    status = get_crm_status(adapter, metrics)

    assert status["dependency_health"]["available"] is True
    assert status["dependency_health"]["dependency"] == "fake_crm"
    assert "metrics" in status


def test_trace_lookup_returns_only_requested_run():
    adapter = FakeCRMAdapter()
    metrics = CRMObservability()

    run_crm_with_adapter(
        sample_lead(),
        adapter,
        metrics,
        "RUN-TRACE-1",
    )

    events = get_crm_trace(metrics, "RUN-TRACE-1")

    assert len(events) > 0
    assert all(event["run_id"] == "RUN-TRACE-1" for event in events)


def test_secret_values_are_redacted():
    payload = {
        "api_key": "fake-api-key-123",
        "nested": {
            "access_token": "fake-token-456",
            "username": "crm-user",
        },
    }

    safe = redact_secrets(payload)

    assert safe["api_key"] == "[REDACTED]"
    assert safe["nested"]["access_token"] == "[REDACTED]"
    assert safe["nested"]["username"] == "crm-user"


def test_structured_trace_contains_no_secret_values():
    adapter = FakeCRMAdapter()
    metrics = CRMObservability()

    run_crm_with_adapter(
        sample_lead(),
        adapter,
        metrics,
        "RUN-SECRET-1",
    )

    serialized = json.dumps(metrics.events)

    assert "fake-api-key-123" not in serialized
    assert "password" not in serialized.lower()


def test_follow_up_timeout_exposes_partial_side_effect():
    adapter = FakeCRMAdapter(fail_follow_up_creation=True)
    metrics = CRMObservability()

    result = run_crm_with_adapter(
        sample_lead(),
        adapter,
        metrics,
        "RUN-PARTIAL-1",
    )

    assert result["status"] == "needs_review"
    assert result["crm_record_id"] == "CRM-0001"
    assert result["follow_up_task_id"] is None
    assert len(adapter.store.records) == 1
    assert len(adapter.store.follow_up_tasks) == 0


def test_task4_fixture_creates_evidence_files():
    from pathlib import Path

    evidence = run_task4_fixture()

    assert evidence["success"]["status"] == "completed"
    assert evidence["failure"]["status"] == "needs_review"

    assert Path("outputs/task4_integration.json").exists()
    assert Path("traces/task4_crm_traces.json").exists()
    assert Path("reports/task4_measurement_report.json").exists()
