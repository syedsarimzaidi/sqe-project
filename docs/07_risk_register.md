# Risk Register

Risks affecting this project's quality, its test coverage, and its delivery — compiled
honestly from what was actually found/left undone during this pass, not a generic template.
Likelihood/Impact are rated Low/Medium/High; Severity = a simple combination of the two used
only to order the table, not a formula the rubric requires.

| # | Risk | Area | Likelihood | Impact | Severity | Mitigation / status |
|---|---|---|---|---|---|---|
| R1 | Solo submission on a project scoped for 2–3 people | Delivery | High | High | **High** | Scope was deliberately narrowed to 2 workflows / 1 module (Stock) instead of covering more of InvenTree, so the depth achieved per area stays defensible even solo. Discussed explicitly with the student early on; remaining risk is purely about available time before the deadline, not approach. |
| R2 | `delete_on_deplete` (BR-3) has no API-level or mutation-level test — only unit-level | Test coverage | Medium | Medium | **Medium** | Documented in `docs/06_traceability_matrix.md`'s "Known gaps". A regression here (e.g. a future code change that silently stops deleting depleted items) would only be caught by the 4 existing unit tests, not by CI's mutation-score gate. Mitigation: unit tests are real and passing; API/mutation coverage is a good next addition if time allows, not urgent. |
| R3 | No concurrency test for BR-4 (row locking via `lock_quantity()`) | Test coverage | Medium | High | **Medium-High** | The guard's *presence* is confirmed by mutation testing (M14/M15 killed), but no test proves it actually prevents a lost update under real concurrent requests. This is the single largest testing gap in the project — a race condition here would corrupt stock counts in production and nothing currently in CI would catch it. Needs a multi-threaded/multi-process test (two threads calling `take_stock()` on the same row with a deliberate delay) — not attempted due to time, flagged rather than hidden. |
| R4 | Two real defects found (Issues #3, #4) are filed but **not fixed** | Application correctness | Confirmed (both reproduced) | Issue #3: Low (requires internal/model-level caller, not reachable via public API) / Issue #4: High (reachable via public API with a schema-valid request, corrupts data) | **Issue #4: High**, Issue #3: Low | Per explicit project-scope decision, this QA pass reports defects rather than patching the vendored application source. Both have concrete repro steps and a suggested fix direction in `docs/04_exploratory_qa_findings.md` and the GitHub issues themselves (#3, #4) for whoever picks up the fix work next (see handoff doc). |
| R5 | Frontend dependency audit found `react-router`/`react-router-dom` with 2 moderate CVEs in the production bundle | Security | Confirmed | Medium | **Medium** | Open redirect + a deserialization issue whose SSR-specific attack surface doesn't apply here (InvenTree's frontend is a client-rendered SPA, not SSR) but the open-redirect half still does. Documented in `docs/05_security_assessment.md` with the exact advisory IDs; recommended fix is a version bump past `7.17.0`, not yet applied (QA-only scope). |
| R6 | OWASP ZAP and Playwright browser-based tests (E2E, accessibility, UI-level RBAC) could not be run in this sandbox | Test coverage / tooling | Confirmed (environment-specific) | Medium | **Medium** | Both are blocked by this sandbox's network allowlist (no Docker image pulls, `cdn.playwright.dev` unreachable for the Playwright browser binary) — confirmed empirically, not assumed, and documented as sandbox-specific in `docs/00_HANDOFF_STATUS.md`. Neither blocker exists on a normal dev machine or in GitHub Actions; this is a tooling-access gap in *this* environment, not a defect in the test design. |
| R7 | SonarQube static analysis not run (Docker-dependent) | Static analysis | Confirmed (environment-specific) | Low | **Low** | Substituted with hand-verified `radon` cyclomatic-complexity calculations (exact match against the tool, see `docs/03_static_analysis.md`) plus a CI job wired up for SonarCloud and intentionally disabled (`if: false`) pending a `SONAR_TOKEN` secret — a documented, visible skip rather than a silent one. Low impact because the complexity metric itself (the part the assignment explicitly asks to hand-calculate) was still delivered and verified. |
| R8 | k6 performance/recovery testing not started at all | Test coverage | Confirmed | Medium | **Medium** | k6 binary unavailable in this sandbox and no script has been written yet (unlike the ZAP/Playwright gaps, this isn't blocked by network access — a k6 script *could* be authored here even without running it, which was not done due to time prioritization toward items that could be fully verified). Clearly the single largest unstarted deliverable; flagged for immediate attention by whoever continues. |
| R9 | Mutation harness is custom-built (not an off-the-shelf tool like `mutmut`/`Cosmic Ray`) | Methodology / grading risk | Low | Medium | **Low-Medium** | A deliberate choice (scoped precisely to the 2 selected methods rather than mutating all 3,800 lines of `stock/models.py`), but a grader expecting a named standard tool's output format might need this rationale explained at viva — it's documented in the harness's own docstring and in `docs/mutation_report.md`, but is worth rehearsing as a talking point. |
| R10 | Viva defense of solo-submitted, partly-AI-assisted work | Delivery | Medium | High | **Medium-High** | All AI use is disclosed in `docs/ai_use_record.md` (append-only, updated after each major piece of work). The actual risk is the student being able to explain *why* each design decision was made (the custom mutation operators tied to BR-1/BR-2, the EP/BVA generator's regex-based constraint parsing, the equivalent-mutant reasoning for M02) under live questioning — this is explicitly not automatable and needs real review time before the viva. |

## How this maps back to the project

- R2, R3, R8 are gaps in what's *tested* — they don't mean the application is known-broken,
  only that certain rules/behaviours aren't independently verified by an automated gate yet.
- R4, R5 are gaps in the *application* itself — confirmed real, filed, not fixed (by design).
- R6, R7 are *environment* limitations specific to this sandbox, not design flaws — restated
  here (not just in the handoff doc) because a risk register should name environment risk
  explicitly, not bury it under "not started."
- R1, R9, R10 are *delivery/defense* risks rather than technical ones.

## Reproducing this register

This table is not generated from a tool — it is a manual compilation cross-checked against:
`docs/04_exploratory_qa_findings.md` (R4), `docs/05_security_assessment.md` (R5, R6 ZAP-half),
`docs/06_traceability_matrix.md` (R2, R3), `docs/03_static_analysis.md` (R7), and
`docs/00_HANDOFF_STATUS.md` (R6 Playwright-half, R8, R10 scope). Anyone updating one of those
source documents should re-check whether a risk's status here needs updating too.
