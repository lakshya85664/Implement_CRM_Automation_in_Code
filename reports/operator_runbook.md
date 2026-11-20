
# CRM Automation — Operator Runbook

## 1. Purpose

This project implements an observable CRM automation workflow for lead qualification, CRM record creation, sales-owner assignment, and follow-up task creation.

The implementation uses a local fake CRM adapter. It does not connect to a production CRM system.

## 2. Environment setup

Open Command Prompt in the project directory:

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

## 3. Run the workflow

Run the main workflow:

```cmd
python crm_automation.py
```

Run the Task 2 happy-path evidence:

```cmd
python -c "from crm_automation import run_task2_fixture; import json; print(json.dumps(run_task2_fixture(), indent=4))"
```

Run the Task 3 recovery evidence:

```cmd
python -c "from crm_automation import run_task3_fixture; import json; print(json.dumps(run_task3_fixture(), indent=4))"
```

Run the Task 4 integration and monitoring evidence:

```cmd
python -c "from crm_automation import run_task4_fixture; import json; print(json.dumps(run_task4_fixture(), indent=4))"
```

## 4. Run automated tests

Run the complete test suite:

```cmd
python -m pytest -v
```

Run with a concise summary:

```cmd
python -m pytest -q
```

## 5. Failure and recovery drills

| Scenario | Expected behavior | Operator action |
|---|---|---|
| Qualified lead | CRM record and follow-up created | Verify assigned owner |
| Unqualified lead | No CRM side effects | No action required |
| Invalid email | Validation rejects lead | Correct lead data |
| Timeout before commit | Bounded retry | Inspect dependency and retry safely |
| Malformed response | Needs review | Inspect response and quarantine invalid data |
| Permanent failure | Needs review | Escalate to CRM administrator |
| Duplicate trigger | Duplicate prevented | Verify original CRM record |
| Timeout after commit | Reconcile existing side effects | Check record and follow-up before replay |
| Follow-up timeout | Partial state exposed | Create or reconcile missing follow-up task |

## 6. Evidence files

### Outputs

- `outputs/task2_crm_automation.json`
- `outputs/task3_crm_recovery.json`
- `outputs/task4_integration.json`

### Traces

- `traces/task3_crm_recovery_traces.json`
- `traces/task4_crm_traces.json`

### Reports

- `reports/task4_measurement_report.json`

## 7. Measurement results

Task 4 local fixture results:

| Metric | Result |
|---|---:|
| Total runs | 2 |
| Successful runs | 1 |
| Failed runs | 1 |
| Success rate | 50% |
| Adapter operations attempted | 3 |
| CRM records created | 1 |
| Follow-up tasks created | 1 |
| Average duration | 0.097 ms |

These measurements represent a small local fake-adapter run. They are not production performance benchmarks.

## 8. Known limitations

1. The fake CRM adapter uses in-memory storage.
2. Replay protection does not survive process restarts.
3. In-memory duplicate checks are not atomic across concurrent processes.
4. A follow-up creation timeout can leave a CRM record without a follow-up task.
5. The retry implementation is a deterministic simulation rather than a production scheduler.
6. The measurement results are based on local execution, not real network latency.
7. The adapter does not implement authentication, authorization, or a real CRM API.

## 9. Production improvements

- Use persistent database-backed idempotency keys.
- Implement transactional writes or an outbox pattern.
- Add real HTTP timeouts and exponential backoff.
- Add authenticated CRM API integration.
- Introduce structured log aggregation and alerting.
- Add concurrency and integration tests.
- Implement automated reconciliation for incomplete follow-up tasks.

## 10. Security

- Do not commit API keys, access tokens, passwords, or personal credentials.
- Read secrets from environment variables or a managed secret store.
- Redact sensitive fields from structured traces.
- Use synthetic lead data for assessment and demonstrations.
