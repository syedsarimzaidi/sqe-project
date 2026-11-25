# Defect evidence, root cause and Pareto analysis

**Student:** Eman Hassan

## Product finding — login button text fails minimum contrast ([#5](https://github.com/syedsarimzaidi/sqe-project/issues/5))

**Severity:** Medium. The primary submit action remains available, but low-vision users may have difficulty reading its label.

**Reproduce:** Open the default light-theme login page at `/web/login` in a fresh Chromium context. Run axe-core and inspect the `color-contrast` result for the **Log In** button.

**Expected:** The 14 px normal-weight label meets WCAG 2.x AA's minimum ratio of 4.5:1.

**Actual:** axe measured 4.32:1 for white text (`#ffffff`) on blue (`#4c6ef5`). The keyboard focus check reached the submit button. Lighthouse independently reported a color-contrast failure on a login-page link in its mobile profile, which is a different element.

**Evidence:** [axe JSON](evidence/2026-11-25/axe-login.json), [actual screenshot](evidence/2026-11-25/login.png), [keyboard trace](evidence/2026-11-25/keyboard-login.json). Tested at project revision `4e72745` with Vite and system Chromium.

**Cause:** Default foreground/background combination in the login CTA. The contrast calculation establishes the direct cause. The originating theme token requires separate confirmation.

## Product finding — login Tab order exposes hidden, unlabeled TOTP input ([#7](https://github.com/syedsarimzaidi/sqe-project/issues/7))

**Severity:** Medium. Keyboard and screen-reader users encounter an unnamed focus stop in the standard credential flow.

**Reproduce:** Open `/web/login` in a fresh Chromium context, then press Tab from the username field through the password field toward the next action. Inspect the focus sequence and the axe `label` finding.

**Expected:** Focus advances through visible, named controls in the default form. An inactive TOTP field is absent from keyboard navigation and the accessibility tree.

**Actual:** An unnamed `INPUT` receives keyboard focus after the password field. Axe identifies the input as `name="TOTP"` with `hidden` and no accessible label.

**Evidence:** [Keyboard focus trace](evidence/2026-11-25/keyboard-login.json) and [axe JSON](evidence/2026-11-25/axe-login.json).

**Cause:** The [classic form](../mis/src/frontend/src/components/forms/AuthenticationForm.tsx) renders a TOTP text input within Mantine's `VisuallyHidden` wrapper. The runtime evidence shows that its rendered visibility and focus behavior leave it reachable even with the `hidden` attribute.

## QA infrastructure finding — coverage gate has no threshold ([#6](https://github.com/syedsarimzaidi/sqe-project/issues/6))

**Severity:** Medium. CI can give a false pass when the test suite still passes after losing measured coverage.

**Reproduce:** Open [.github/workflows/ci.yml](../.github/workflows/ci.yml) at `4e72745`. Inspect the pytest command (`--cov-fail-under=0`) and the step named **Enforce coverage threshold on selected workflow methods**.

**Expected:** The step fails CI if either selected method falls below its documented 100% baseline.

**Actual:** The step opens the XML, reads its contents, and prints a message. It checks no metric. The [GitHub run](https://github.com/syedsarimzaidi/sqe-project/actions/runs/45547599494) shows success for this step. The local coverage measurement passed independently.

**Cause:** The workflow uses artifact presence and test success as proxies for measured coverage. Tests can pass with assertions or cases removed, and the job has no measured threshold.

## Existing product issues

- [#3](https://github.com/syedsarimzaidi/sqe-project/issues/3), high, reproduced in a rollback-only model probe. Decimal construction accepts NaN. The subsequent comparison in both workflow methods is outside the conversion exception handler.
- [#4](https://github.com/syedsarimzaidi/sqe-project/issues/4), high, the model-layer save and failing SQLite readback were reproduced. The HTTP status remains the original issue evidence. Validation checks the submitted amount. The stored total can exceed the field precision, and SQLite's decimal conversion detects it later during readback.

The local model-level repetitions are in [the boundary probe output](evidence/2026-11-25/stock-boundary-recheck.log).

## Pareto of triaged product findings

One count per issue or issue-ready finding. This small sample groups explicit quantity validation causes together. Other automated accessibility alerts and local ZAP alerts are tracked in tool output pending detailed triage. The CI check is a QA infrastructure finding and has its own entry above.

| Root cause group | Count | Share | Cumulative |
|---|---:|---:|---:|
| Quantity validation and persistence | 2 | 50% | 50% |
| Login contrast | 1 | 25% | 75% |
| Login focus and labeling | 1 | 25% | 100% |

The first group includes two historical open issues and the two accessibility groups each include one finding verified in this continuation. These counts describe the triaged sample.
