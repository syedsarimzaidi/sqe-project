# Stock workflow test plan

**Student:** Eman Hassan
**Baseline:** project commit `4e7274524d382f7a296e251fbc0031848b905de4`

## Scope and approach

Verify receive and dispatch for an authorized operator, quantity validation, balance readback, history, serialized items, depletion, and role restrictions. Use disposable SQLite data and a loopback application. Track requirements in [the matrix](06_traceability_matrix.md) and prioritize failure modes using [the risk register](07_risk_register.md). PostgreSQL locking and production scalability require a representative environment.

| Priority | Check | Oracle |
|---|---|---|
| P0 | Unit coverage and independent condition outcomes | Expected return value, persisted balance, coverage arcs, named witness pairs |
| P0 | Receive and dispatch through React | Successful mutation and persisted balance after reload |
| P0 | UI role restriction | View-only user can inspect stock and cannot invoke adjustments through UI |
| P1 | Keyboard, axe-core and Lighthouse | Keyboard reaches labeled controls and visible focus. Record tool findings per page and device profile |
| P1 | ZAP passive analysis | Inspect representative local responses, record rule IDs, risk and scope |
| P1 | k6 bounded load and recovery | Track request count, errors, p95 and stock balance. Check recovery independently from latency |
| P1 | Static analysis and mutation | Report exact tool scope, severity and score with exclusions |
| P2 | Issue triage | Retain reproduction evidence, severity, expectations and distinct root-cause grouping |

A QA pass requires reproducible results tied to an exact revision. Record explicit failures, unexecuted cases, and environment blockers. A passing subset cannot close unexecuted work. Product fixes and the associated before/after change are deferred under the QA-only scope.
