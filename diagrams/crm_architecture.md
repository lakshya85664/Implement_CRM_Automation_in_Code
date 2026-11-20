
# CRM Automation — Architecture

```mermaid
flowchart TD
    A[Lead Input] --> B[Normalize Lead Identity]
    B --> C[Validate Lead]
    C --> D{Qualified?}

    D -->|No| E[Mark Not Qualified]
    D -->|Yes| F[Assign Owner]

    F --> G[CRM Adapter Interface]
    G --> H[Fake CRM Adapter]
    H --> I[Create CRM Record]
    I --> J[Create Follow-up Task]
    J --> K[Workflow Completed]

    G --> L{Dependency Failure?}
    L -->|Timeout| M[Bounded Retry / Recovery]
    L -->|Malformed or Permanent| N[Needs Review]
    M --> O[Replay / Idempotency Check]
    O --> K
    O --> N

    B --> P[Structured Events]
    F --> P
    G --> P
    I --> P
    J --> P
    M --> P
    N --> P

    P --> Q[JSON Traces]
    P --> R[Metrics and Measurement Report]
    P --> S[Operator Status]
```

## Main components

- **Lead processing:** Normalizes lead identity and validates required fields.
- **Qualification:** Evaluates the lead score and determines eligibility.
- **Assignment:** Assigns a sales owner based on qualification rules.
- **CRM adapter:** Separates external CRM operations from workflow logic.
- **Recovery:** Handles timeout, malformed response, permanent failure, and replay.
- **Observability:** Records structured events, execution metrics, and traces.
- **Operator interface:** Exposes dependency health, workflow status, and next actions.
