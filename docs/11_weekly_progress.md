# Weekly progress and GQM metrics

**Student:** Eman Hassan
**Reporting week:** 23–29 November 2026, checkpoint on 25 November (PKT)

| Date | Work recorded | Evidence |
|---|---|---|
| 24 Nov | Baseline, scope, unit/API suites, mutation harness and CI demonstration entered version control. | [Git history](evidence/2026-11-25/history.txt), [CI runs](evidence/2026-11-25/ci-runs.json) |
| 25 Nov | Initial exploratory defects, dependency audit, RTM and risk register entered version control. | [Git history](evidence/2026-11-25/history.txt), [issues](evidence/2026-11-25/issues.json) |
| 25 Nov | Re-ran unit coverage, verified the deletion decision, exercised browser workflows and a view-only user, audited accessibility and nominal local security responses, and measured latency and restart recovery. | [Continuation log](00_HANDOFF_STATUS.md), [evidence index](12_execution_evidence.md) |

The repository shows work beginning on 24 November. The checkpoint covers the single week evidenced by the Git history.

| Goal | Question | Metric and checkpoint |
|---|---|---|
| Verify stock correctness | Are both workflows measurable and repeatable? | 26 original unit cases and 4 decision witnesses passed. Both stock methods reached all measured statement and branch arcs in the baseline coverage run. Browser adjustments persisted after reload. |
| Evaluate access and usability | Can a reader inspect stock while an operator can adjust it? Can the login be navigated and read? | Browser reader check passed. Login Lighthouse accessibility 85/100. Axe reported 6 login rules and 7 stock detail rules. |
| Assess responsiveness | Do local adjustments stay below the declared 500 ms p95 under the smoke workload? | 40 requests, zero failures. Receive p95 68.48 ms, dispatch p95 103.94 ms. |
| Assess recovery | Is committed stock readable and writable after restart? | Balance 10 before and after restart. Post-restart receive and dispatch each returned 201 and balance returned to 10. |
| Improve defect visibility | Are confirmed findings traceable to evidence and an issue? | Two historical application issues and two newly confirmed product findings. Filed login issues #5 and #7 and the separately classified CI issue #6. |
