# Project Handoff Status — SE3002 Final Project

**Repo:** https://github.com/syedsarimzaidi/sqe-project
**Student:** Eman Hassan
**Selected MIS:** InvenTree (Stock app — receive/dispatch workflows)
**Last updated:** 2026-11-25

Read this file first. It says exactly what is done, verified, and pushed vs. what is still
needed, so work can continue (e.g. in another tool) without re-deriving context.

---

The sections below preserve the original handoff. See the continuation log at the end for subsequent verification and current blockers.

## ✅ DONE — verified, committed, and pushed to `main`

### Section 1 — Scope & registration (`docs/01_scope.md`)
- Repo: InvenTree, MIT license, baseline commit `4f5fbc091b8066d29445495d3e177078df7abfcd`
  (vendored into `mis/`)
- 2 workflows selected: receive stock (`add_stock`) / dispatch stock (`take_stock`)
- 8 functional requirements, 4 business rules (BR-1 clamp, BR-2 decision rule, BR-3
  delete-on-deplete, BR-4 row locking), 2 roles
- Full local setup/run/reset instructions (SQLite, no Docker needed — Docker Hub is
  network-blocked in the sandbox this was built in, so the dev workflow uses a plain
  Python venv instead; this works fine on a normal machine/CI too)

### Area 1 — Static analysis, white-box testing, mutation testing, CI
- **Unit tests**: `tests/team/unit/test_stock_add_remove.py` — 26/26 passing, covers
  FR-1..FR-8, BR-1 (BVA around the clamp), BR-2, BR-3 (discovered empirically, not
  assumed), BR-4
- **Coverage**: `docs/02_coverage_note.md` + `docs/coverage_html/` — **100% statement +
  branch coverage** of the two selected-workflow methods specifically (not the whole
  3,800-line file, which is explicitly out of scope and documented as such)
- **Static analysis / complexity**: `docs/03_static_analysis.md` — hand-calculated
  cyclomatic complexity for both methods, verified exactly against `radon`
  (add_stock = 5, take_stock = 7)
  - ⚠️ **SonarQube was not run** — no working Docker/SonarQube-server access in this
    environment (confirmed, not assumed). CI has a SonarCloud job wired up but disabled
    (`if: false`) pending a `SONAR_TOKEN` secret — **see "Still needed" below**.
- **Mutation testing**: `tests/team/mutation/` — custom harness (15 mutants: standard
  operators + 2 custom ones tied to BR-1/BR-2). Score: **13/15 killed = 86.7%**. Both
  survivors fully analysed in `docs/mutation_report.md` (one true equivalent mutant, one
  honestly-documented test gap — not papered over).
- **CI pipeline**: `.github/workflows/ci.yml` — test+coverage job, mutation-testing job
  (gated on tests passing), SonarCloud job (documented skip). No `continue-on-error`
  anywhere; failures actually block.
- **Documented fix PR**: #1, merged. First commit deliberately broke `add_stock()`
  (CI failed), second commit fixed it (CI passed). https://github.com/syedsarimzaidi/sqe-project/pull/1
- **Blocked/rejected PR**: #2, still open/unmerged on purpose. Deliberately removes the
  BR-1 clamp; CI `test-and-coverage` job failed, `mutation-testing` was skipped as a
  consequence. https://github.com/syedsarimzaidi/sqe-project/pull/2

### Area 2 — API testing & data generation
- **OpenAPI spec**: `docs/openapi_stock_workflows.json` — trimmed extract of InvenTree's
  own auto-generated schema, limited to `/api/stock/add/` and `/api/stock/remove/`
- **Generator**: `tests/team/api/generate_test_data.py` — reads the spec's `quantity`
  constraints, produces EP classes + 3-point BVA triples programmatically (not hand-typed)
- **API tests**: `tests/team/api/test_stock_api.py` — 18/18 passing, all parametrized from
  the generator's output, covering happy path, auth/permissions, EP classes, BVA around
  BR-1, cross-workflow shared-record readback, repeated-request behaviour

### Exploratory QA pass (bug-hunting only — nothing here was fixed, per instruction)
- `docs/04_exploratory_qa_findings.md` — 11 probes run against the live API/model, 2
  genuine defects found and filed as GitHub Issues (not fixed):
  - **Issue #3**: `add_stock()`/`take_stock()` crash with unhandled
    `decimal.InvalidOperation` on a `NaN` quantity (model-level call only; the public API
    is not exposed to this because DRF's serializer catches it first)
  - **Issue #4**: a schema-valid 10-digit quantity, added to an item that already holds
    stock, can overflow the DB field's `max_digits=15` limit and **corrupt the row**
    (crashes on next read) — a real gap between serializer-level and DB-level validation

### Security assessment (dependency audit half)
- `docs/05_security_assessment.md`
  - **Backend**: `pip-audit` on `mis/src/backend/requirements.txt` — 165 packages scanned,
    **0 known vulnerabilities**.
  - **Frontend**: `npm audit` on `mis/src/frontend/package.json` — 12 found (3 high, 9
    moderate), triaged one by one: all but `react-router`/`react-router-dom` are
    build/dev-tooling only (not shipped to users); `react-router` (moderate, open redirect)
    is the one production-relevant finding, with the fix direction noted (not applied —
    QA-only scope).
  - Role-based access control: already evidenced at the **API level** (see Exploratory QA
    pass above, Probe #8, and the committed API test suite) — re-stated/cross-referenced in
    this doc. UI-level Playwright role checks and the OWASP ZAP scan are **not done** — see
    "Still needed" #3/#4 below for why.

### Traceability matrix
- `docs/06_traceability_matrix.md` — every FR-1..FR-8 and BR-1..BR-4 mapped to its actual
  covering unit test(s), API test(s), and mutant(s) (compiled directly from the test file
  source, not re-typed from memory). Honestly documents 3 known gaps rather than hiding them:
  BR-3 (delete-on-deplete) has no API/mutation coverage, BR-4 (locking) has no concurrency
  test, FR-3/FR-7 tracking-history isn't independently re-asserted at the API layer.

### Risk register
- `docs/07_risk_register.md` — 10 risks (R1–R10) across delivery, test-coverage, application,
  security, and environment categories, each rated Likelihood/Impact/Severity with an honest
  mitigation/status line. Covers the solo-submission risk, the BR-3/BR-4 coverage gaps, the
  2 unfixed bugs, the react-router CVEs, the sandbox tooling blockers (ZAP/Playwright/k6/
  SonarQube), the custom-mutation-harness methodology risk, and the viva-defense risk.

---

## ❌ STILL NEEDED — not started / not usable yet

Hand these off as-is; nothing below has been attempted beyond the scaffolding noted.

1. **Fix the 2 filed bugs (Issues #3, #4)** — intentionally left unfixed (QA-only scope
   for this pass). Each issue has a concrete repro + suggested fix direction.

2. **Area 3 — Playwright E2E tests**
   - `tests/team/e2e/` exists but is **empty** — no spec files written yet.
   - Playwright's browser binary **cannot be downloaded in this sandbox**
     (`cdn.playwright.dev` is network-blocked here — confirmed, not a config error). This
     is *not* a problem on a normal machine or in GitHub Actions — `npx playwright install
     --with-deps chromium` will just work there.
   - Useful reference: InvenTree ships its own Playwright suite at
     `mis/src/frontend/tests/*.spec.ts` (login helpers in `login.ts`/`defaults.ts`,
     e.g. `doLogin()`, `adminuser`/`allaccessuser` test fixtures) — reuse those helpers
     rather than writing login flow from scratch.
   - Needed: 2+ use-case-based E2E tests (receive stock, dispatch stock) through the real
     React UI, plus a keyboard-navigation accessibility check.

3. **Usability & accessibility** (Lighthouse + axe-core)
   - Not started at all. Needs the frontend dev server running
     (`cd mis/src/frontend && npm install && npm run dev`, or built+served) and
     Playwright wired to axe-core (`@axe-core/playwright`).
   - Assignment also wants one screen's before/after fix comparison — pick something
     concrete on the stock-item detail page.

4. **Security assessment — remaining half**
   - Dependency audit (both backend and frontend) is **done** — see
     `docs/05_security_assessment.md`. What's left:
     - **OWASP ZAP passive scan** — not run. ZAP needs Docker (or a binary download), both
       blocked in this sandbox the same way Docker/Playwright already are elsewhere in this
       file. Run `docker run -t ghcr.io/zaproxy/zaproxy zap-baseline.py -t <dev-server-url>
       -r zap_report.html` against the running dev server once Docker is available.
     - **Role-based access-control as Playwright UI tests** — API-level is already evidenced
       (Probe #8, committed API suite); the assignment also wants this walked through the
       real React UI, which needs the Playwright browser binary (see item 2 below).

5. **Performance & recovery (k6)**
   - Not started. Needs a k6 script hitting `/api/stock/add/` and `/api/stock/remove/`
     under load (p95 response time target), plus one failure-recovery scenario (e.g. kill
     the server mid-request, confirm no partial/corrupt state — note Issue #4 above is
     relevant prior art for what "corrupt state" looks like in this app).

6. **Weekly progress reports / GQM metrics** — not created.

7. **Final PDF report compiling everything above** — not created. All the raw material
   (this handoff file plus every `docs/*.md` file) should be the primary input.

8. **Viva prep** — not started (can't be automated; the student needs to actually
   understand what's in `docs/` well enough to explain and defend it live, especially
   given the solo-submission risk already discussed with the student).

---

## Environment notes for whoever continues this (so they don't waste time rediscovering)

- No Docker/Docker Hub access in *this* sandbox — but a normal dev machine or GitHub
  Actions runner will have it. Don't assume the constraint applies elsewhere.
- Same for `cdn.playwright.dev` — blocked here, fine elsewhere.
- Local run (no Docker): Python 3.12 venv, SQLite, see `docs/01_scope.md`'s "Environment"
  section for the exact env vars and commands used throughout this project.
- `tests/team/unit` and `tests/team/api` run via plain `pytest` (see `pytest.ini`,
  `conftest.py` at repo root) — both suites are green as of this handoff.

## Continuation log — Eman Hassan

| Phase | Outcome | Evidence |
|---|---|---|
| Baseline audit | Inspected the handoff, scope, requirements, existing tests, workflow, Git history and GitHub records at `4e72745`. Test and mutation jobs succeeded and SonarCloud was skipped. The coverage gate reads the XML but contains no coverage assertion. | [History](evidence/2026-11-25/history.txt), [CI jobs](evidence/2026-11-25/ci-jobs.json), [Issues](evidence/2026-11-25/issues.json) |
| Planning | Preserved the existing RTM and risk register. Added execution scope, priorities and exit criteria. | [Traceability](06_traceability_matrix.md), [Risks](07_risk_register.md), [Test plan](08_test_plan.md) |
| Unit and decision verification | 26 unit tests passed. Selected method statements and branches reached 100% in a fresh measurement. Radon confirmed 5/7 complexity. Reviewed single-condition witnesses and verified all three downstream BR-3 conditions using four additional passing cases. | [Decision coverage](09_decision_coverage.md) |
| Browser and accessibility baseline | Login keyboard check reached both credential fields and submit. Lighthouse accessibility scored 85/100. Axe reported six rule violations. | [Lighthouse](evidence/2026-11-25/lighthouse-login.json), [axe](evidence/2026-11-25/axe-login.json), [keyboard](evidence/2026-11-25/keyboard-login.json) |
| k6 latency baseline | 40 successful requests at one VU. Receive p95 68.48 ms and dispatch p95 103.94 ms. Stock balance stayed at 10 after 20 adjustment pairs. | [k6](evidence/2026-11-25/k6.log), [before](evidence/2026-11-25/k6-before.json), [after](evidence/2026-11-25/k6-after.json) |
| ZAP passive review | Three nominated local responses processed and queue drained. The report contains alerts scoped to the development topology. | [Requests](evidence/2026-11-25/zap-requests.txt), [ZAP HTML](evidence/2026-11-25/zap-report.html), [ZAP JSON](evidence/2026-11-25/zap-alerts.json) |
| Defect analysis | Validated the login contrast and hidden TOTP focus issues using axe and keyboard evidence and identified the non-enforcing CI coverage step by source inspection. Filed accessibility issues #5 and #7 and CI issue #6 in the project repository. | [Root cause and Pareto](10_defect_analysis.md) |
| Authenticated UI | Receive changed 10 to 15 and dispatch changed 10 to 7. Both balances persisted after reload. A separate view-only session reached Stock Details without enabled adjustment actions. Axe recorded seven rule violations on Stock Details. | [Playwright](evidence/2026-11-25/playwright-stock.log), [receive](evidence/2026-11-25/add-stock.png), [dispatch](evidence/2026-11-25/remove-stock.png), [stock axe](evidence/2026-11-25/axe-stock.json) |
| Restart recovery | Stopped the disposable server between requests. Observed an outage, restarted, confirmed balance 10, then executed a successful receive/dispatch pair and confirmed balance 10 again. | [Recovery](evidence/2026-11-25/recovery.log) |
| Backend dependency audit | pip-audit reported 165 packages and zero known vulnerabilities at run time. | [Audit JSON](evidence/2026-11-25/pip-audit.json) |
| SonarQube attempt | Local image extraction failed with ENOSPC on two attempts. Standalone distribution requests returned HTTP 403. The extracted official server application reached Elasticsearch startup, which exited because the runtime does not expose `/proc/self/coredump_filter`. CI SonarCloud remained skipped. | [Docker retry](evidence/2026-11-25/sonarqube-retry.log), [distribution requests](evidence/2026-11-25/sonarqube-portable.log), [CI](evidence/2026-11-25/ci-jobs.json) |
| Reporting and risk | Updated the risk register with observed outcomes. Recorded the evidenced project week, GQM metrics and AI use. | [Risk register](07_risk_register.md), [Weekly progress](11_weekly_progress.md), [AI disclosure](ai_use_record.md) |
| Mutation rerun | Detached baseline worktree reproduced 13/15 killed (86.7%). M02 and M13 still survived. | [Mutation output](evidence/2026-11-25/mutation.log) |
| Frontend dependency check | npm advisory endpoint returned 5 direct advisories for the installed tree. Input and output are retained. | [Dependency assessment](05_security_assessment.md) |
| SonarQube completed | Compatible 10.6 Community Build processed the file-level scan. Reported coverage 31.4%, 12 code smells and zero reported bugs, vulnerabilities or hotspots. First-analysis quality gate OK with zero returned conditions. | [Static analysis](03_static_analysis.md), [Scanner](evidence/2026-11-25/sonarqube-scanner.log) |
| Historical defect recheck | A rollback-only model probe reproduced issue #3 in receive and dispatch, and reproduced issue #4's successful model write followed by a SQLite readback exception. | [Probe output](evidence/2026-11-25/stock-boundary-recheck.log) |
| Final report | Compiled the verified evidence and scope limits into the PDF and retained its editable source. Frontend TypeScript check, Vite production build and Django system check passed. | [PDF](13_final_report.pdf), [Report source](13_final_report.md), [Vite build](evidence/2026-11-25/frontend-build.log), [TypeScript check](evidence/2026-11-25/frontend-typecheck.log), [Django check](evidence/2026-11-25/django-check.log) |

## Rubric completion follow-up

The assignment PDF was subsequently reviewed and revealed additional mandatory work. The previous PDF is a verified checkpoint and does not close all assignment requirements. Submission metadata and filename instructions are in [the submission checklist](14_submission_checklist.md). The requester specified a solo submission for Eman Hassan with a 17:00 PKT deadline on 25 November 2026. Load reruns are in progress and will be reported from their actual outputs.

Four sustained 60-second k6 runs completed. Both 1-VU runs passed. Both 5-VU runs failed the zero-error threshold, with 59.57% and 57.06% failed requests. See [load verification](15_load_verification.md). Release is held pending investigation and clean-state repetition. Submission metadata placeholders are present in the editable report.
