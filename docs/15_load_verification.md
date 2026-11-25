# Sustained load verification — Eman Hassan

Four constant-VU runs used the unchanged application build and the same local machine, each measured for 60 seconds. Each VU used a separate stock fixture at starting quantity 1000. Paired add/remove requests used quantity 1. Targets were p95 below 500 ms per operation, zero unexpected failures and all status checks passing. These targets protect interactive stock adjustment latency and inventory write reliability.

| VUs | Repeat | Receive p95 ms | Dispatch p95 ms | Requests/s | Unexpected failures | Result |
|---|---|---:|---:|---:|---:|---|
| 1 | 1 | 33.38 | 72.51 | 8.118 | 0% | Pass |
| 1 | 2 | 31.00 | 71.51 | 8.208 | 0% | Pass |
| 5 | 1 | 137.93 | 143.20 | 26.296 | 59.57% | Fail |
| 5 | 2 | 136.36 | 142.01 | 26.942 | 57.06% | Fail |

The workload failure rate fails the release criterion despite acceptable measured latency. Diagnose error responses and database contention before making a production-readiness claim. SQLite and the development server limit generalization. Raw outputs and process exit codes are in docs/evidence/load-rerun/. Initial configuration failures are retained separately. The earlier 40-request smoke result remains historical evidence.

The fixture state was initialized before the four-run sequence. Failed pairs can change subsequent starting balances, so the failed five-user measurements are diagnostic and require clean-state reruns for strict comparability. No clean-state equivalence is claimed for those runs.
