
import pytest

from crm_automation import (
    LeadInput,
    CRMStore,
    normalize_lead,
    run_crm_automation,
    run_task2_fixture,
)


@pytest.fixture
def store():
    return CRMStore()


@pytest.fixture
def qualified_lead():
    return LeadInput(
        lead_id="LEAD-101",
        name="  Priya   Mehta ",
        email=" PRIYA@EXAMPLE.COM ",
        company=" Example Ltd ",
        source=" WEBSITE ",
        score=90,
    )


def test_lead_identity_is_normalized(qualified_lead):
    normalized = normalize_lead(qualified_lead)

    assert normalized.name == "Priya Mehta"
    assert normalized.email == "priya@example.com"
    assert normalized.company == "Example Ltd"
    assert normalized.source == "website"


def test_qualified_lead_creates_crm_record_and_follow_up(
    qualified_lead, store
):
    result = run_crm_automation(qualified_lead, store)

    assert result.status == "completed"
    assert result.qualified is True
    assert result.crm_record_id == "CRM-0001"
    assert result.owner == "senior_sales"
    assert result.follow_up_task_id == "FOLLOWUP-0001"

    assert len(store.records) == 1
    assert len(store.follow_up_tasks) == 1


def test_standard_qualified_lead_gets_standard_owner(store):
    lead = LeadInput(
        lead_id="LEAD-102",
        name="Rohan Patel",
        email="rohan@example.com",
        company="Rohan Industries",
        source="referral",
        score=75,
    )

    result = run_crm_automation(lead, store)

    assert result.status == "completed"
    assert result.owner == "sales_team"


def test_unqualified_lead_does_not_create_records(store):
    lead = LeadInput(
        lead_id="LEAD-103",
        name="Low Score Lead",
        email="low@example.com",
        company="Small Company",
        source="website",
        score=40,
    )

    result = run_crm_automation(lead, store)

    assert result.status == "not_qualified"
    assert result.qualified is False
    assert result.crm_record_id is None
    assert len(store.records) == 0
    assert len(store.follow_up_tasks) == 0


def test_invalid_email_is_rejected_before_side_effects(store):
    lead = LeadInput(
        lead_id="LEAD-104",
        name="Invalid Email",
        email="not-an-email",
        company="Test Company",
        source="website",
        score=90,
    )

    with pytest.raises(ValueError, match="valid email"):
        run_crm_automation(lead, store)

    assert len(store.records) == 0
    assert len(store.follow_up_tasks) == 0


def test_duplicate_email_does_not_create_second_record(
    qualified_lead, store
):
    first = run_crm_automation(qualified_lead, store)

    duplicate = LeadInput(
        lead_id="LEAD-105",
        name="Priya Mehta",
        email="priya@example.com",
        company="Example Ltd",
        source="website",
        score=95,
    )

    second = run_crm_automation(duplicate, store)

    assert first.status == "completed"
    assert second.status == "duplicate"
    assert second.crm_record_id == first.crm_record_id

    assert len(store.records) == 1
    assert len(store.follow_up_tasks) == 1


def test_task2_fixture_creates_evidence_file():
    from pathlib import Path

    evidence = run_task2_fixture()

    assert evidence["result"]["status"] == "completed"
    assert evidence["metrics"]["crm_records_created"] == 1
    assert evidence["metrics"]["follow_up_tasks_created"] == 1
    assert Path("outputs/task2_crm_automation.json").exists()
