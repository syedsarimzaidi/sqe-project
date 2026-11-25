---
title: SQE Project — Review Status
author: Eman Hassan
date: 25 November 2026
---

# Current position

The project has working QA scripts and actual evidence across the major testing areas. Full rubric compliance remains incomplete. This review uses repository checkpoint 9f4c5ce and the supplied assignment PDF. Deadline supplied is 17:00 PKT on 25 November 2026.

Project repository: https://github.com/syedsarimzaidi/sqe-project

# Work completed and evidenced

| Area | Verified work |
|---|---|
| System and scope | InvenTree baseline saved, receive/dispatch workflows selected, 8 functional requirements, 4 business rules, 2 roles, setup instructions and traceability documented. |
| Unit testing | Original 26 cases passed with 100% statement and branch coverage of the two selected stock methods. Four additional depletion-decision cases passed. Combined suite: 30 passing cases. Whole-file Sonar coverage: 31.4%. |
| API | OpenAPI extract, quantity EP/BVA generator and 18 API cases exist. Baseline CI passed the API suite. |
| Static analysis | SonarQube Community Build 10.6 ran on stock/models.py, reporting 12 code smells. Radon complexity of receive/dispatch: 5 and 7. |
| Mutation and CI | Baseline harness killed 13/15 mutants. M02 and M13 survived. Fix PR #1 and failed/open PR #2 are documented. CI on commit 27c36c9 passed test and mutation jobs; SonarCloud was skipped. |
| Browser | Authenticated receive 10 → 15 and dispatch 10 → 7 persisted after reload. View-only account inspected stock without enabled adjustment controls. |
| Accessibility | Lighthouse login accessibility 85/100. Axe reported 6 login rule violations and 7 Stock Details rule violations. Login Tab sequence was recorded. |
| Security | ZAP processed three nominated local responses. Backend dependency audit checked 165 packages with zero known vulnerabilities. Frontend advisory lookup returned five direct advisory records. |
| Performance | Four sustained 60-second runs executed: 1 and 5 VUs, two repetitions each. Both 1-VU runs passed. Both 5-VU runs failed the error threshold. |
| Recovery | Between-request server stop/restart preserved readable stock and allowed a successful adjustment pair afterward. |
| Defects and reporting | Historical issues #3/#4 reproduced at model level. New issues #5 contrast, #6 coverage gate and #7 hidden TOTP focus filed. Weekly checkpoint, AI record, risk register, evidence index and a three-page report PDF exist. |

# Findings Eman should review

Five-user load runs failed 59.57% and 57.06% of requests. Server logs showed SQLite database locking. Receive/dispatch p95 remained below 500 ms, but the reliability criterion failed. Starting data was initialized once for the sequence; failed pairs mean strict clean-state comparability still requires reruns.

The existing report PDF predates these load failures. It must be regenerated after consolidating current evidence. The CI coverage step does not enforce a measured threshold, and SonarCloud is disabled in the workflow. Selected-method coverage was verified independently.

# Requirements still incomplete

| Requirement | Work remaining |
|---|---|
| Planning and risk | Complete numeric 5×5 matrix with at least 8 product and 2 project risks; measurable exit criteria tied to highest risks; schedule, roles and entry/suspension/resumption criteria; three-point estimates. Actual past effort was not tracked. |
| White-box and Sonar | Complete MCC tables and derive MC/DC pairs; justify uncovered server logic; CFG calculation compared directly with Sonar; duplication, debt and ratings. |
| API generation | Verify EP/BVA breadth across inputs and demonstrate changes to two spec constraints with regenerated cases. |
| Mutation and CI | Resolve the rubric's requirement to analyse at least 15 surviving mutants; the current sample has only 2 survivors. Strengthen coverage/Sonar gates and include required QA suites in CI. |
| Use cases | Two use cases per member with at least 2 alternative and 2 exception flows each; automate every flow and assert displayed results and persisted postconditions. |
| Accessibility | Stock-form keyboard submission and correction after rejected input; logged-in key-screen Lighthouse accessibility/best-practices/SEO; before/after Lighthouse and axe using an allowed standalone HTML improvement. |
| Defensive security | Four explicit role/action access decisions, workflow traffic through passive ZAP, and two corroborated control reviews. |
| Performance and recovery | Investigate five-user failures; reset data between repeats; controlled dependency failure before write completion, state verification, retry and duplicate assertions. |
| Defect management | Two major defects with 5 Whys and fishbone, corrective/preventive actions, priority and triage, with risk links. |
| Completion report | Required GQM metrics, tested/untested scope, deviations, residual risk per risk, three criteria with actual vs target, and an evidence-based release/hold decision. |
| Final package | Consolidated PDF and ZIP including .git, public repository link, area ownership/contribution disclosure, roll number, section and required filenames. |

# Details for Eman to confirm

1. Roll number and section. Replace TO_BE_FILLED in docs/13_final_report.md and regenerate the PDF.
2. Google Sheet registration status and any instructor-approved solo adaptation.
3. Which gaps the instructor has explicitly waived, if any. No waivers are currently evidenced.
4. Review the tests, results and AI-use record before submission and prepare to explain them in the viva.

Use the filename Project_<RollNumber>_<Section>.pdf and the corresponding ZIP for an approved solo format, subject to instructor confirmation. Existing commits include multiple author identities; preserve an accurate contribution history.

# Current recommendation

Hold the claim of full rubric completion. The repository contains substantial verified work, while the remaining requirements above need completion or explicit disclosure. Product defects can remain open within the requested QA-only scope.

Evidence navigation: docs/00_HANDOFF_STATUS.md, docs/12_execution_evidence.md and docs/15_load_verification.md. Raw outputs are retained under docs/evidence/.
