
# Topic 15 — Implement CRM Automation in Code

## Project Overview

This project implements an observable CRM automation workflow for lead qualification, lead identity normalization, CRM record creation, owner assignment, and follow-up task creation.

It demonstrates workflow state management, validation, dependency isolation, failure classification, bounded retries, replay protection, structured JSON traces, and operational metrics.

The implementation uses synthetic lead data and a local fake CRM adapter. No production CRM credentials or external services are required.

## Learning Objectives

- Normalize and validate lead identity.
- Qualify leads using a score threshold.
- Assign sales owners based on lead qualification.
- Create CRM records and follow-up tasks.
- Handle timeout, malformed response, and permanent failure.
- Prevent duplicate side effects during replay.
- Isolate external dependencies behind an injectable adapter.
- Record structured events and workflow measurements.
- Expose dependency health and workflow traces.

## Project Structure

```text
Implement_CRM_Automation_in_Code/
│
├── crm_automation.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── tests/
│   ├── test_task1_contract.py
│   ├── test_task2_crm_automation.py
│   ├── test_task3_recovery.py
│   └── test_task4_observability.py
│
├── outputs/
│   ├── task2_crm_automation.json
│   ├── task3_crm_recovery.json
│   └── task4_integration.json
│
├── traces/
│   ├── task3_crm_recovery_traces.json
│   └── task4_crm_traces.json
│
├── reports/
│   ├── task4_measurement_report.json
│   └── operator_runbook.md
│
└── diagrams/
    └── crm_architecture.md
```

## Implementation Tasks

### Task 1 — Workflow Contract and State Model

Implemented workflow input, run state, task/event progress, result, and trace models.

Defined legal transitions and rejected illegal transitions. Added automated tests for workflow creation, state transitions, pause/resume, failure, and trace generation.

### Task 2 — CRM Automation Implementation

Implemented lead identity normalization, validation, qualification, owner assignment, CRM record creation, and follow-up task creation.

Added validation for invalid email addresses and duplicate lead identities. Unqualified leads do not create CRM records or follow-up tasks.

### Task 3 — Failure, Retry, and Replay Safety

Implemented failure classification for timeout, malformed response, and permanent failure.

Added bounded retry behavior, duplicate-trigger prevention, and recovery after a simulated timeout following a successful commit.

The recovery trace records attempts, failure categories, and the next recommended operator action.

### Task 4 — Integration Boundary and Observability

Introduced an injectable CRM adapter contract and local fake implementation.

Added structured JSON events, dependency health reporting, workflow metrics, trace lookup, and recursive secret redaction.

Metrics include run counts, success rate, operation attempts, created records, follow-up tasks, and average execution duration.

### Task 5 — Operator Runbook and Evidence Report

Documented setup, execution, tests, failure drills, evidence files, measurements, known limitations, and production improvements.

The operator runbook is available at `reports/operator_runbook.md`.

The architecture diagram is available at `diagrams/crm_architecture.md`.

## Environment Requirements

- Python 3.10 or higher
- Pydantic
- Pytest

## Setup

Open Command Prompt:

```cmd
cd /d E:\Tayana_Projects\Workflow_Orchestration\Implement_CRM_Automation_in_Code
```

Activate the virtual environment:

```cmd
.venv\Scripts\activate
```

Install dependencies:

```cmd
pip install -r requirements.txt
```

## Execution Commands

Run the main workflow:

```cmd
python crm_automation.py
```

Generate Task 2 evidence:

```cmd
python -c "from crm_automation import run_task2_fixture; import json; print(json.dumps(run_task2_fixture(), indent=4))"
```

Generate Task 3 evidence:

```cmd
python -c "from crm_automation import run_task3_fixture; import json; print(json.dumps(run_task3_fixture(), indent=4))"
```

Generate Task 4 evidence:

```cmd
python -c "from crm_automation import run_task4_fixture; import json; print(json.dumps(run_task4_fixture(), indent=4))"
```

## Automated Testing

Run all tests:

```cmd
python -m pytest -v
```

Run a concise test summary:

```cmd
python -m pytest -q
```

### Verified Test Results

| Task | Tests passed |
|---|---:|
| Task 1 — Workflow contract | 7 |
| Task 2 — CRM automation | 7 |
| Task 3 — Failure and recovery | 9 |
| Task 4 — Integration and observability | 9 |
| **Total** | **32** |

Verified combined result: **32 passed**.

## Task 4 Measurement Results

| Metric | Observed value |
|---|---:|
| Workflow runs | 2 |
| Successful runs | 1 |
| Failed runs | 1 |
| Success rate | 50% |
| Adapter operations attempted | 3 |
| CRM records created | 1 |
| Follow-up tasks created | 1 |
| Average duration | 0.097 ms |

These figures are from the deterministic local fixture and should not be interpreted as production benchmarks.

## Evidence Inventory

### Outputs
- `outputs/task2_crm_automation.json`
- `outputs/task3_crm_recovery.json`
- `outputs/task4_integration.json`

### Traces
- `traces/task3_crm_recovery_traces.json`
- `traces/task4_crm_traces.json`

### Reports and Architecture
- `reports/task4_measurement_report.json`
- `reports/operator_runbook.md`
- `diagrams/crm_architecture.md`

## Known Limitations

- The fake CRM adapter uses in-memory storage.
- Idempotency protection is not durable across process restarts.
- Concurrent requests are not protected by atomic database transactions.
- A follow-up timeout can leave a CRM record without a corresponding follow-up task.
- Retry scenarios are simulated locally.
- No real CRM API, authentication, or production monitoring service is connected.

## Engineering Reflection

This project helped me understand how a CRM automation workflow can be designed as a reliable and observable system instead of a collection of independent API calls. I implemented lead normalization, validation, qualification, owner assignment, CRM record creation, and follow-up scheduling. Breaking the workflow into explicit stages made its behavior easier to test and troubleshoot.

The failure and recovery tasks were particularly valuable. I explored how timeouts, malformed responses, permanent failures, and duplicate triggers affect workflow execution. I learned that a timeout does not always mean an operation failed. A dependency may have completed its side effect even when the caller did not receive a successful response. This makes replay safety and reconciliation important when creating CRM records and follow-up tasks.

The adapter implementation helped me understand dependency injection and why external systems should be isolated behind clear contracts. A fake adapter allowed me to test successful and failed dependency behavior without using production credentials or modifying real CRM data. Structured events and measurement reports also made it easier to understand workflow outcomes.

The assessment reinforced the importance of validation, bounded retries, idempotency, secret redaction, and operator visibility. Automated tests provided evidence that the workflow handles the tested scenarios consistently.

There are still limitations. The current storage is in-memory, so it does not provide durable idempotency across restarts or safe coordination between concurrent processes. A production implementation would need persistent idempotency keys, transactional writes or an outbox pattern, real dependency timeouts, and automated reconciliation for incomplete follow-up tasks.

Overall, this project strengthened my understanding of workflow orchestration, CRM integration boundaries, failure recovery, and operational observability. It also showed me why a production-ready automation must make its state, side effects, and recovery actions explicit.

