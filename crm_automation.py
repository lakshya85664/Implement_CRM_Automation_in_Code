
# crm_automation.py

from dataclasses import dataclass, field
from typing import Any


@dataclass
class LeadInput:
    lead_id: str
    name: str
    email: str
    company: str
    source: str
    score: int


@dataclass
class TaskRecord:
    task_id: str
    task_type: str
    status: str = "pending"
    owner: str | None = None


@dataclass
class WorkflowEvent:
    run_id: str
    event: str
    state: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowResult:
    run_id: str
    business_key: str
    status: str
    crm_record_id: str | None = None
    owner: str | None = None
    follow_up_task_id: str | None = None


@dataclass
class WorkflowTrace:
    run_id: str
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class WorkflowRun:
    run_id: str
    business_key: str
    state: str = "created"
    attempts: int = 0
    context: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)

    def record(self, event: str, **details: Any) -> None:
        self.events.append({
            "run_id": self.run_id,
            "event": event,
            "state": self.state,
            "details": details,
        })


LEGAL_TRANSITIONS = {
    ("created", "start"): "running",
    ("running", "complete"): "completed",
    ("running", "pause"): "waiting",
    ("waiting", "resume"): "running",
    ("running", "fail"): "needs_review",
}


def transition(run: WorkflowRun, event: str) -> WorkflowRun:
    """Apply a validated workflow state transition."""

    next_state = LEGAL_TRANSITIONS.get((run.state, event))

    if next_state is None:
        raise ValueError(
            f"Illegal transition: {run.state} + {event}"
        )

    previous_state = run.state
    run.state = next_state

    run.record(
        event=event,
        previous_state=previous_state,
        next_state=next_state,
    )

    return run


def create_workflow(
    run_id: str,
    business_key: str,
    lead: LeadInput,
) -> WorkflowRun:
    """Create a workflow run for one CRM lead."""

    run = WorkflowRun(
        run_id=run_id,
        business_key=business_key,
        context={"lead": lead.__dict__},
    )

    run.record("workflow_created", lead_id=lead.lead_id)
    return run


def create_workflow_result(run: WorkflowRun) -> WorkflowResult:
    """Build a result from the workflow context."""

    return WorkflowResult(
        run_id=run.run_id,
        business_key=run.business_key,
        status=run.state,
        crm_record_id=run.context.get("crm_record_id"),
        owner=run.context.get("owner"),
        follow_up_task_id=run.context.get("follow_up_task_id"),
    )


def create_workflow_trace(run: WorkflowRun) -> WorkflowTrace:
    """Return a copy of the workflow event history."""

    return WorkflowTrace(
        run_id=run.run_id,
        events=list(run.events),
    )


def run_topic_fixture() -> dict:
    """Run a deterministic CRM workflow state demonstration."""

    lead = LeadInput(
        lead_id="LEAD-001",
        name="Aarav Shah",
        email="aarav@example.com",
        company="Example Technologies",
        source="website",
        score=85,
    )

    run = create_workflow(
        run_id="RUN-CRM-001",
        business_key="LEAD-001",
        lead=lead,
    )

    transition(run, "start")
    transition(run, "complete")

    result = create_workflow_result(run)
    trace = create_workflow_trace(run)

    return {
        "status": result.status,
        "run_id": result.run_id,
        "business_key": result.business_key,
        "result": result.__dict__,
        "events": trace.events,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run_topic_fixture(), indent=4))


# ============================================================
# TASK 2 — CRM AUTOMATION IMPLEMENTATION
# Append this section below the existing Task 1 code.
# ============================================================

import re
import json
from dataclasses import dataclass, field


QUALIFICATION_THRESHOLD = 70

OWNER_RULES = {
    "high_value": "senior_sales",
    "standard": "sales_team",
}


@dataclass
class CRMStore:
    """In-memory CRM repository for deterministic local testing."""

    records: dict[str, dict[str, Any]] = field(default_factory=dict)
    follow_up_tasks: dict[str, dict[str, Any]] = field(default_factory=dict)


@dataclass
class CRMAutomationResult:
    status: str
    lead_id: str
    normalized_email: str
    qualified: bool
    crm_record_id: str | None = None
    owner: str | None = None
    follow_up_task_id: str | None = None
    reason: str | None = None
    events: list[dict[str, Any]] = field(default_factory=list)


def normalize_lead(lead: LeadInput) -> LeadInput:
    """Normalize identity fields before validation or CRM operations."""

    return LeadInput(
        lead_id=lead.lead_id.strip(),
        name=" ".join(lead.name.strip().split()),
        email=lead.email.strip().lower(),
        company=" ".join(lead.company.strip().split()),
        source=lead.source.strip().lower(),
        score=lead.score,
    )


def validate_lead(lead: LeadInput) -> None:
    """Reject invalid lead data before any CRM side effect."""

    if not lead.lead_id:
        raise ValueError("Lead ID is required")

    if not lead.name:
        raise ValueError("Lead name is required")

    if not lead.company:
        raise ValueError("Company is required")

    if not lead.source:
        raise ValueError("Lead source is required")

    if not 0 <= lead.score <= 100:
        raise ValueError("Lead score must be between 0 and 100")

    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

    if not re.match(email_pattern, lead.email):
        raise ValueError("A valid email address is required")


def qualify_lead(lead: LeadInput) -> bool:
    """Return whether the lead meets the qualification threshold."""

    return lead.score >= QUALIFICATION_THRESHOLD


def assign_owner(lead: LeadInput) -> str:
    """Assign an owner deterministically using the lead score."""

    if lead.score >= 85:
        return OWNER_RULES["high_value"]

    return OWNER_RULES["standard"]


def create_crm_record(
    lead: LeadInput,
    store: CRMStore,
    owner: str,
) -> dict[str, Any]:
    """Create a CRM record using the normalized email as identity."""

    email_key = lead.email

    if email_key in store.records:
        raise ValueError("CRM record already exists for this email")

    record_id = f"CRM-{len(store.records) + 1:04d}"

    record = {
        "crm_record_id": record_id,
        "lead_id": lead.lead_id,
        "name": lead.name,
        "email": lead.email,
        "company": lead.company,
        "source": lead.source,
        "score": lead.score,
        "owner": owner,
        "status": "qualified",
    }

    store.records[email_key] = record
    return record


def create_follow_up_task(
    crm_record: dict[str, Any],
    store: CRMStore,
) -> dict[str, Any]:
    """Create a follow-up task for a qualified CRM record."""

    task_id = f"FOLLOWUP-{len(store.follow_up_tasks) + 1:04d}"

    task = {
        "task_id": task_id,
        "crm_record_id": crm_record["crm_record_id"],
        "owner": crm_record["owner"],
        "task_type": "contact_lead",
        "status": "pending",
        "due_in_days": 1,
    }

    store.follow_up_tasks[task_id] = task
    return task


def run_crm_automation(
    lead: LeadInput,
    store: CRMStore,
) -> CRMAutomationResult:
    """Execute lead qualification and CRM record/follow-up creation."""

    events: list[dict[str, Any]] = []

    def record_event(event: str, **details: Any) -> None:
        events.append({
            "event": event,
            "details": details,
        })

    # Normalize and validate before any side effects.
    normalized = normalize_lead(lead)
    record_event("lead_normalized", lead_id=normalized.lead_id)

    validate_lead(normalized)
    record_event("lead_validated", lead_id=normalized.lead_id)

    # Check for an existing lead using normalized email identity.
    if normalized.email in store.records:
        existing = store.records[normalized.email]

        record_event(
            "duplicate_lead_detected",
            existing_crm_record_id=existing["crm_record_id"],
        )

        return CRMAutomationResult(
            status="duplicate",
            lead_id=normalized.lead_id,
            normalized_email=normalized.email,
            qualified=existing["status"] == "qualified",
            crm_record_id=existing["crm_record_id"],
            owner=existing["owner"],
            reason="A CRM record already exists for this email",
            events=events,
        )

    qualified = qualify_lead(normalized)

    record_event(
        "lead_qualified" if qualified else "lead_not_qualified",
        score=normalized.score,
        threshold=QUALIFICATION_THRESHOLD,
    )

    if not qualified:
        return CRMAutomationResult(
            status="not_qualified",
            lead_id=normalized.lead_id,
            normalized_email=normalized.email,
            qualified=False,
            reason="Lead score is below the qualification threshold",
            events=events,
        )

    # Assign owner, create CRM record, and create follow-up task.
    owner = assign_owner(normalized)
    record_event("owner_assigned", owner=owner)

    crm_record = create_crm_record(normalized, store, owner)
    record_event(
        "crm_record_created",
        crm_record_id=crm_record["crm_record_id"],
    )

    follow_up = create_follow_up_task(crm_record, store)
    record_event(
        "follow_up_created",
        follow_up_task_id=follow_up["task_id"],
    )

    return CRMAutomationResult(
        status="completed",
        lead_id=normalized.lead_id,
        normalized_email=normalized.email,
        qualified=True,
        crm_record_id=crm_record["crm_record_id"],
        owner=owner,
        follow_up_task_id=follow_up["task_id"],
        events=events,
    )


def run_task2_fixture() -> dict[str, Any]:
    """Run a deterministic CRM automation example and save evidence."""

    from pathlib import Path

    store = CRMStore()

    lead = LeadInput(
        lead_id="LEAD-CRM-001",
        name="  Aarav   Shah ",
        email=" AARAV@EXAMPLE.COM ",
        company=" Example Technologies ",
        source=" WEBSITE ",
        score=90,
    )

    result = run_crm_automation(lead, store)

    evidence = {
        "result": result.__dict__,
        "crm_records": list(store.records.values()),
        "follow_up_tasks": list(store.follow_up_tasks.values()),
        "metrics": {
            "crm_records_created": len(store.records),
            "follow_up_tasks_created": len(store.follow_up_tasks),
        },
    }

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / "task2_crm_automation.json"
    output_path.write_text(
        json.dumps(evidence, indent=4),
        encoding="utf-8",
    )

    return evidence


# ============================================================
# TASK 3 — FAILURE, RETRY, AND REPLAY SAFETY
# Append below the existing Task 2 implementation.
# ============================================================

from enum import Enum


MAX_CRM_RETRIES = 2


class CRMFailureCategory(str, Enum):
    TIMEOUT = "timeout"
    MALFORMED_RESPONSE = "malformed_response"
    PERMANENT = "permanent"
    DUPLICATE = "duplicate"


class CRMRecoveryAction(str, Enum):
    RETRY = "retry"
    COMPLETED = "completed"
    NEEDS_REVIEW = "needs_review"
    DUPLICATE_PREVENTED = "duplicate_prevented"


@dataclass
class CRMRecoveryResult:
    status: str
    action: str
    failure_category: str | None
    attempts: int
    crm_record_id: str | None
    follow_up_task_id: str | None
    side_effects: int
    recovered_existing: bool
    next_action: str
    trace: list[dict[str, Any]] = field(default_factory=list)


def classify_crm_failure(outcome: str) -> CRMFailureCategory | None:
    """Classify a simulated dependency outcome."""

    mapping = {
        "timeout": CRMFailureCategory.TIMEOUT,
        "timeout_before_commit": CRMFailureCategory.TIMEOUT,
        "timeout_after_commit": CRMFailureCategory.TIMEOUT,
        "malformed_response": CRMFailureCategory.MALFORMED_RESPONSE,
        "permanent": CRMFailureCategory.PERMANENT,
        "duplicate": CRMFailureCategory.DUPLICATE,
    }

    return mapping.get(outcome)


def find_existing_crm_result(
    lead: LeadInput,
    store: CRMStore,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Find an existing CRM record and its follow-up task."""

    normalized = normalize_lead(lead)
    record = store.records.get(normalized.email)

    if record is None:
        return None, None

    follow_up = next(
        (
            task
            for task in store.follow_up_tasks.values()
            if task["crm_record_id"] == record["crm_record_id"]
        ),
        None,
    )

    return record, follow_up


def execute_crm_with_recovery(
    lead: LeadInput,
    store: CRMStore,
    outcomes: list[str],
    max_retries: int = MAX_CRM_RETRIES,
) -> CRMRecoveryResult:
    """
    Execute CRM automation with bounded retries and replay safety.

    Supported simulated outcomes:
      success
      timeout
      timeout_before_commit
      timeout_after_commit
      malformed_response
      permanent
      duplicate
    """

    if max_retries < 0:
        raise ValueError("max_retries cannot be negative")

    trace: list[dict[str, Any]] = []
    attempts = 0
    side_effects_before = (
        len(store.records) + len(store.follow_up_tasks)
    )
    last_failure: str | None = None

    def record(event: str, **details: Any) -> None:
        trace.append({
            "event": event,
            "attempt": attempts,
            "details": details,
        })

    normalized = normalize_lead(lead)
    validate_lead(normalized)

    # A previously completed business operation must not be repeated.
    existing_record, existing_follow_up = find_existing_crm_result(
        normalized,
        store,
    )

    if existing_record is not None:
        record(
            "duplicate_replay_prevented",
            crm_record_id=existing_record["crm_record_id"],
        )

        side_effects_after = (
            len(store.records) + len(store.follow_up_tasks)
        )

        return CRMRecoveryResult(
            status="duplicate_prevented",
            action=CRMRecoveryAction.DUPLICATE_PREVENTED.value,
            failure_category=CRMFailureCategory.DUPLICATE.value,
            attempts=0,
            crm_record_id=existing_record["crm_record_id"],
            follow_up_task_id=(
                existing_follow_up["task_id"]
                if existing_follow_up else None
            ),
            side_effects=side_effects_after - side_effects_before,
            recovered_existing=True,
            next_action="Verify the original CRM record; do not resubmit.",
            trace=trace,
        )

    for outcome in outcomes:
        attempts += 1
        record("attempt_started", simulated_outcome=outcome)

        # A duplicate trigger is explicitly blocked.
        if outcome == "duplicate":
            record("duplicate_trigger_blocked")
            return CRMRecoveryResult(
                status="duplicate_prevented",
                action=CRMRecoveryAction.DUPLICATE_PREVENTED.value,
                failure_category=CRMFailureCategory.DUPLICATE.value,
                attempts=attempts,
                crm_record_id=None,
                follow_up_task_id=None,
                side_effects=(
                    len(store.records) + len(store.follow_up_tasks)
                    - side_effects_before
                ),
                recovered_existing=False,
                next_action="Inspect the business key before replay.",
                trace=trace,
            )

        failure = classify_crm_failure(outcome)

        # Simulate an ambiguous timeout before any side effect.
        if outcome in ("timeout", "timeout_before_commit"):
            last_failure = CRMFailureCategory.TIMEOUT.value
            record("dependency_timeout", phase="before_commit")

            if attempts <= max_retries:
                record("retry_scheduled", category=last_failure)
                continue

            record("retry_limit_reached")

            return CRMRecoveryResult(
                status="needs_review",
                action=CRMRecoveryAction.NEEDS_REVIEW.value,
                failure_category=last_failure,
                attempts=attempts,
                crm_record_id=None,
                follow_up_task_id=None,
                side_effects=(
                    len(store.records) + len(store.follow_up_tasks)
                    - side_effects_before
                ),
                recovered_existing=False,
                next_action="Inspect the dependency and retry only after review.",
                trace=trace,
            )

        # Malformed and permanent failures are not safe to retry.
        if failure in (
            CRMFailureCategory.MALFORMED_RESPONSE,
            CRMFailureCategory.PERMANENT,
        ):
            last_failure = failure.value
            record("failure_classified", category=last_failure)

            return CRMRecoveryResult(
                status="needs_review",
                action=CRMRecoveryAction.NEEDS_REVIEW.value,
                failure_category=last_failure,
                attempts=attempts,
                crm_record_id=None,
                follow_up_task_id=None,
                side_effects=(
                    len(store.records) + len(store.follow_up_tasks)
                    - side_effects_before
                ),
                recovered_existing=False,
                next_action="Quarantine the response and request operator review.",
                trace=trace,
            )

        # Run the CRM operation for a normal success or a timeout
        # that occurs after the CRM side effects have committed.
        if outcome in ("success", "timeout_after_commit"):
            result = run_crm_automation(normalized, store)

            if result.status != "completed":
                record("crm_operation_not_completed", status=result.status)

                return CRMRecoveryResult(
                    status="needs_review",
                    action=CRMRecoveryAction.NEEDS_REVIEW.value,
                    failure_category="crm_operation_not_completed",
                    attempts=attempts,
                    crm_record_id=result.crm_record_id,
                    follow_up_task_id=result.follow_up_task_id,
                    side_effects=(
                        len(store.records) + len(store.follow_up_tasks)
                        - side_effects_before
                    ),
                    recovered_existing=False,
                    next_action="Inspect the existing CRM record and follow-up task.",
                    trace=trace,
                )

            record(
                "crm_side_effects_committed",
                crm_record_id=result.crm_record_id,
                follow_up_task_id=result.follow_up_task_id,
            )

            if outcome == "timeout_after_commit":
                last_failure = CRMFailureCategory.TIMEOUT.value
                record("dependency_timeout", phase="after_commit")

                if attempts <= max_retries:
                    record("retry_scheduled", category=last_failure)

                    # Reconcile the committed operation rather than
                    # creating a second record or follow-up task.
                    existing_record, existing_follow_up = (
                        find_existing_crm_result(normalized, store)
                    )

                    if existing_record and existing_follow_up:
                        record(
                            "recovery_reconciled_existing_side_effects",
                            crm_record_id=existing_record["crm_record_id"],
                            follow_up_task_id=existing_follow_up["task_id"],
                        )

                        return CRMRecoveryResult(
                            status="completed",
                            action=CRMRecoveryAction.COMPLETED.value,
                            failure_category=last_failure,
                            attempts=attempts,
                            crm_record_id=existing_record["crm_record_id"],
                            follow_up_task_id=existing_follow_up["task_id"],
                            side_effects=(
                                len(store.records) + len(store.follow_up_tasks)
                                - side_effects_before
                            ),
                            recovered_existing=True,
                            next_action="No further retry required; verify the CRM record.",
                            trace=trace,
                        )

                return CRMRecoveryResult(
                    status="needs_review",
                    action=CRMRecoveryAction.NEEDS_REVIEW.value,
                    failure_category=last_failure,
                    attempts=attempts,
                    crm_record_id=result.crm_record_id,
                    follow_up_task_id=result.follow_up_task_id,
                    side_effects=(
                        len(store.records) + len(store.follow_up_tasks)
                        - side_effects_before
                    ),
                    recovered_existing=False,
                    next_action="Inspect committed side effects before any manual replay.",
                    trace=trace,
                )

            record("crm_workflow_completed")

            return CRMRecoveryResult(
                status="completed",
                action=CRMRecoveryAction.COMPLETED.value,
                failure_category=None,
                attempts=attempts,
                crm_record_id=result.crm_record_id,
                follow_up_task_id=result.follow_up_task_id,
                side_effects=(
                    len(store.records) + len(store.follow_up_tasks)
                    - side_effects_before
                ),
                recovered_existing=False,
                next_action="Verify the CRM record and scheduled follow-up.",
                trace=trace,
            )

    record("outcome_sequence_exhausted")

    return CRMRecoveryResult(
        status="needs_review",
        action=CRMRecoveryAction.NEEDS_REVIEW.value,
        failure_category=last_failure or "no_outcome",
        attempts=attempts,
        crm_record_id=None,
        follow_up_task_id=None,
        side_effects=(
            len(store.records) + len(store.follow_up_tasks)
            - side_effects_before
        ),
        recovered_existing=False,
        next_action="Inspect the trace and determine the next safe action.",
        trace=trace,
    )


def run_task3_fixture() -> dict[str, Any]:
    """Generate deterministic failure and recovery evidence."""

    from pathlib import Path

    scenarios = [
        (
            "timeout_recovery",
            LeadInput(
                "LEAD-301", "Timeout Lead", "timeout@example.com",
                "Timeout Ltd", "website", 90
            ),
            ["timeout", "timeout", "success"],
        ),
        (
            "malformed_response",
            LeadInput(
                "LEAD-302", "Malformed Lead", "malformed@example.com",
                "Malformed Ltd", "referral", 90
            ),
            ["malformed_response", "success"],
        ),
        (
            "permanent_failure",
            LeadInput(
                "LEAD-303", "Permanent Lead", "permanent@example.com",
                "Permanent Ltd", "website", 90
            ),
            ["permanent", "success"],
        ),
        (
            "timeout_after_commit",
            LeadInput(
                "LEAD-304", "Recovery Lead", "recovery@example.com",
                "Recovery Ltd", "website", 95
            ),
            ["timeout_after_commit"],
        ),
    ]

    scenario_results = {}
    all_traces = []

    for name, lead, outcomes in scenarios:
        store = CRMStore()
        result = execute_crm_with_recovery(
            lead=lead,
            store=store,
            outcomes=outcomes,
        )

        scenario_results[name] = {
            "result": result.__dict__,
            "crm_record_count": len(store.records),
            "follow_up_count": len(store.follow_up_tasks),
        }

        all_traces.append({
            "scenario": name,
            "events": result.trace,
        })

    # Replay the already committed recovery lead.
    replay_store = CRMStore()
    replay_lead = scenarios[3][1]

    first_result = execute_crm_with_recovery(
        replay_lead,
        replay_store,
        ["timeout_after_commit"],
    )

    replay_result = execute_crm_with_recovery(
        replay_lead,
        replay_store,
        ["success"],
    )

    scenario_results["duplicate_replay"] = {
        "first_status": first_result.status,
        "replay_result": replay_result.__dict__,
        "crm_record_count": len(replay_store.records),
        "follow_up_count": len(replay_store.follow_up_tasks),
    }

    all_traces.append({
        "scenario": "duplicate_replay",
        "events": replay_result.trace,
    })

    output_dir = Path("outputs")
    trace_dir = Path("traces")
    output_dir.mkdir(exist_ok=True)
    trace_dir.mkdir(exist_ok=True)

    (output_dir / "task3_crm_recovery.json").write_text(
        json.dumps(scenario_results, indent=4),
        encoding="utf-8",
    )

    (trace_dir / "task3_crm_recovery_traces.json").write_text(
        json.dumps(all_traces, indent=4),
        encoding="utf-8",
    )

    return scenario_results


# ============================================================
# TASK 4 — INTEGRATION BOUNDARY AND OBSERVABILITY
# ============================================================

import os
import time
from typing import Protocol


class CRMAdapter(Protocol):
    """Contract required by an external CRM integration."""

    def create_record(
        self,
        lead: LeadInput,
        owner: str,
    ) -> dict[str, Any]:
        ...

    def create_follow_up(
        self,
        crm_record: dict[str, Any],
    ) -> dict[str, Any]:
        ...

    def health_check(self) -> dict[str, Any]:
        ...


@dataclass
class FakeCRMAdapter:
    """Local fake CRM implementation for assessment testing."""

    store: CRMStore = field(default_factory=CRMStore)
    fail_record_creation: bool = False
    fail_follow_up_creation: bool = False

    def create_record(
        self,
        lead: LeadInput,
        owner: str,
    ) -> dict[str, Any]:

        if self.fail_record_creation:
            raise TimeoutError("Simulated CRM record timeout")

        return create_crm_record(lead, self.store, owner)

    def create_follow_up(
        self,
        crm_record: dict[str, Any],
    ) -> dict[str, Any]:

        if self.fail_follow_up_creation:
            raise TimeoutError("Simulated follow-up timeout")

        return create_follow_up_task(crm_record, self.store)

    def health_check(self) -> dict[str, Any]:
        return {
            "dependency": "fake_crm",
            "available": True,
            "record_count": len(self.store.records),
            "follow_up_count": len(self.store.follow_up_tasks),
        }


@dataclass
class CRMObservability:
    """Metrics and structured events for CRM workflow execution."""

    runs: int = 0
    successes: int = 0
    failures: int = 0
    attempts: int = 0
    records_created: int = 0
    follow_ups_created: int = 0
    total_duration_ms: float = 0.0
    events: list[dict[str, Any]] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        if self.runs == 0:
            return 0.0

        return round(self.successes / self.runs * 100, 2)

    @property
    def average_duration_ms(self) -> float:
        if self.runs == 0:
            return 0.0

        return round(self.total_duration_ms / self.runs, 3)

    def report(self) -> dict[str, Any]:
        return {
            "runs": self.runs,
            "successes": self.successes,
            "failures": self.failures,
            "success_rate_percent": self.success_rate,
            "attempts": self.attempts,
            "crm_records_created": self.records_created,
            "follow_up_tasks_created": self.follow_ups_created,
            "average_duration_ms": self.average_duration_ms,
        }


def redact_secrets(value: Any) -> Any:
    """Recursively redact sensitive fields before logging."""

    sensitive_names = {
        "api_key",
        "apikey",
        "authorization",
        "access_token",
        "refresh_token",
        "password",
        "secret",
        "client_secret",
    }

    if isinstance(value, dict):
        redacted = {}

        for key, item in value.items():
            normalized_key = str(key).lower().replace("-", "_")

            if normalized_key in sensitive_names:
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_secrets(item)

        return redacted

    if isinstance(value, list):
        return [redact_secrets(item) for item in value]

    return value


def run_crm_with_adapter(
    lead: LeadInput,
    adapter: CRMAdapter,
    metrics: CRMObservability,
    run_id: str,
) -> dict[str, Any]:
    """Execute CRM automation through an injected adapter."""

    start = time.perf_counter()
    metrics.runs += 1
    trace: list[dict[str, Any]] = []

    def emit(event: str, **details: Any) -> None:
        safe_details = redact_secrets(details)

        entry = {
            "run_id": run_id,
            "event": event,
            "timestamp": time.time(),
            "details": safe_details,
        }

        trace.append(entry)
        metrics.events.append(entry)

    result: dict[str, Any] = {
        "run_id": run_id,
        "status": "needs_review",
        "crm_record_id": None,
        "owner": None,
        "follow_up_task_id": None,
        "error": None,
        "trace": trace,
    }

    try:
        normalized = normalize_lead(lead)
        validate_lead(normalized)

        emit("lead_validated", lead_id=normalized.lead_id)

        qualified = qualify_lead(normalized)
        emit(
            "lead_qualification_checked",
            qualified=qualified,
            score=normalized.score,
        )

        if not qualified:
            result["status"] = "not_qualified"
            emit("workflow_not_qualified")
            return result

        # Check for an existing lead before calling the adapter.
        if normalized.email in getattr(
            getattr(adapter, "store", None), "records", {}
        ):
            existing = adapter.store.records[normalized.email]

            result.update({
                "status": "duplicate",
                "crm_record_id": existing["crm_record_id"],
                "owner": existing["owner"],
            })

            emit(
                "duplicate_prevented",
                crm_record_id=existing["crm_record_id"],
            )
            return result

        owner = assign_owner(normalized)
        result["owner"] = owner
        emit("owner_assigned", owner=owner)

        metrics.attempts += 1
        crm_record = adapter.create_record(normalized, owner)

        result["crm_record_id"] = crm_record["crm_record_id"]
        metrics.records_created += 1

        emit(
            "crm_record_created",
            crm_record_id=crm_record["crm_record_id"],
        )

        metrics.attempts += 1
        follow_up = adapter.create_follow_up(crm_record)

        result["follow_up_task_id"] = follow_up["task_id"]
        metrics.follow_ups_created += 1

        emit(
            "follow_up_created",
            follow_up_task_id=follow_up["task_id"],
        )

        result["status"] = "completed"
        metrics.successes += 1
        emit("workflow_completed")

    except ValueError as exc:
        result["error"] = str(exc)
        metrics.failures += 1
        emit("validation_or_duplicate_error", error=str(exc))

    except TimeoutError:
        result["error"] = "External CRM dependency timed out"
        metrics.failures += 1
        emit(
            "dependency_timeout",
            next_action="Inspect dependency status and review partial side effects",
        )

    except Exception as exc:
        result["error"] = "Unexpected CRM integration error"
        metrics.failures += 1
        emit(
            "integration_error",
            error_type=type(exc).__name__,
            next_action="Request operator review",
        )

    finally:
        duration_ms = (time.perf_counter() - start) * 1000
        metrics.total_duration_ms += duration_ms

        emit("workflow_measurement", duration_ms=round(duration_ms, 3))

    return result


def get_crm_status(
    adapter: CRMAdapter,
    metrics: CRMObservability,
) -> dict[str, Any]:
    """Expose dependency health and monitoring metrics."""

    return {
        "dependency_health": adapter.health_check(),
        "metrics": metrics.report(),
    }


def get_crm_trace(
    metrics: CRMObservability,
    run_id: str,
) -> list[dict[str, Any]]:
    """Retrieve structured events for one workflow run."""

    return [
        event
        for event in metrics.events
        if event["run_id"] == run_id
    ]


def run_task4_fixture() -> dict[str, Any]:
    """Run fake adapter success and failure scenarios."""

    from pathlib import Path

    output_dir = Path("outputs")
    trace_dir = Path("traces")
    report_dir = Path("reports")

    output_dir.mkdir(exist_ok=True)
    trace_dir.mkdir(exist_ok=True)
    report_dir.mkdir(exist_ok=True)

    metrics = CRMObservability()
    adapter = FakeCRMAdapter()

    successful_lead = LeadInput(
        lead_id="LEAD-401",
        name="Meera Desai",
        email="meera@example.com",
        company="Meera Technologies",
        source="website",
        score=92,
    )

    failed_adapter = FakeCRMAdapter(
        fail_record_creation=True
    )

    failed_lead = LeadInput(
        lead_id="LEAD-402",
        name="Failure Lead",
        email="failure@example.com",
        company="Failure Ltd",
        source="referral",
        score=88,
    )

    success_result = run_crm_with_adapter(
        successful_lead,
        adapter,
        metrics,
        "RUN-CRM-401",
    )

    failure_result = run_crm_with_adapter(
        failed_lead,
        failed_adapter,
        metrics,
        "RUN-CRM-402",
    )

    status = get_crm_status(adapter, metrics)

    traces = {
        "success": get_crm_trace(metrics, "RUN-CRM-401"),
        "failure": get_crm_trace(metrics, "RUN-CRM-402"),
    }

    evidence = {
        "success": success_result,
        "failure": failure_result,
        "status": status,
    }

    (output_dir / "task4_integration.json").write_text(
        json.dumps(redact_secrets(evidence), indent=4),
        encoding="utf-8",
    )

    (trace_dir / "task4_crm_traces.json").write_text(
        json.dumps(redact_secrets(traces), indent=4),
        encoding="utf-8",
    )

    (report_dir / "task4_measurement_report.json").write_text(
        json.dumps(metrics.report(), indent=4),
        encoding="utf-8",
    )

    return evidence
