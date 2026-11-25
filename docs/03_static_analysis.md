# Static Analysis & Cyclomatic Complexity

## Tooling note (honest deviation from SonarQube)

SonarQube requires a running SonarQube server. This project's workspace has no working
Docker daemon with registry access (Docker Hub pulls are blocked by the sandbox's network
policy — confirmed empirically, not assumed), so a local SonarQube Community server could
not be stood up in the available time. Two substitutes are used instead, documented here
rather than silently swapped in:

1. **`radon`** (open-source, pip-installable) for cyclomatic complexity — used below for
   the hand-calculation comparison the assignment specifically asks for.
2. **SonarCloud** (free for public GitHub repositories) is configured in the CI pipeline
   (`.github/workflows/ci.yml`) as the closer substitute for the other SonarQube metrics
   (duplication, code smells, bugs, vulnerabilities, ratings) — this requires the repo
   owner to create a free SonarCloud account and add a `SONAR_TOKEN` repository secret;
   until that is done, the Sonar job in CI is a documented, intentionally-skipped step
   rather than a silent failure (see the workflow file's comments).

## Cyclomatic complexity: hand-calculation vs tool, for `take_stock()`

`take_stock()` (`stock/models.py`, lines 3461–3529) is the critical business-rule function
for Workflow 2 (dispatch stock) and implements BR-1, BR-2, and the `record_tracking`
branch.

**Hand-calculated from its CFG**, using McCabe's formula `M = (decision points) + 1`:

| # | Decision point | Line (approx.) |
|---|---|---|
| 1 | `if self.serialized:` | 3478 |
| 2 | `except InvalidOperation:` | 3483 |
| 3 | `if quantity <= 0:` (pre-clamp) | 3486 |
| 4 | `if not self.lock_quantity():` | 3490 |
| 5 | `if quantity <= 0:` (post-clamp, BR-1) | 3499 |
| 6 | `if record_tracking: ... else: ...` | 3519 |

6 decision points → **M = 6 + 1 = 7**

**Tool-calculated** (`radon cc stock/models.py -s`):

```
M 3462:4 StockItem.take_stock - B (7)
```

**Result: 7 = 7 — hand-calculation matches the tool exactly.**

## Cyclomatic complexity for `add_stock()` (Workflow 1, cross-check)

| # | Decision point |
|---|---|
| 1 | `if self.serialized:` |
| 2 | `except InvalidOperation:` |
| 3 | `if quantity <= 0:` |
| 4 | `if not self.lock_quantity():` |

4 decision points → **M = 4 + 1 = 5**, matching radon's `A (5)` rating exactly.

## Reproducing

```bash
pip install radon
radon cc mis/src/backend/InvenTree/stock/models.py -s -a | grep -A1 "add_stock\|take_stock"
```

## Continuation SonarQube verification — Eman Hassan

SonarQube Community Build 10.6.0.92116 successfully processed a scanner report for `mis/src/backend/InvenTree/stock/models.py` at revision `4e72745`. Scanner 7.2.0.5079 imported the baseline unit coverage XML. The current Community Build could not start Elasticsearch in this environment, so the run used the compatible earlier release.

| SonarQube file scope | Observed |
|---|---:|
| Lines of code | 2,186 |
| Cyclomatic complexity | 480 |
| Cognitive complexity | 503 |
| Coverage | 31.4% |
| Line coverage | 37.6% |
| Branch coverage | 16.3% |
| Code smells | 12 |
| Bugs, vulnerabilities and security hotspots reported | 0 each |

The first-analysis quality gate returned `OK` with zero conditions. The two method complexity values of 5 and 7 remain the independent Radon results. The local Sonar report is scoped to one file and uses the installed rule profile. See [measures](evidence/2026-11-25/sonarqube-measures.json), [findings](evidence/2026-11-25/sonarqube-findings.json), [quality gate](evidence/2026-11-25/sonarqube-quality-gate.json) and [scanner output](evidence/2026-11-25/sonarqube-scanner.log).
