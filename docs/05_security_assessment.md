# Security Assessment

Per the assignment's security-assessment requirement: role-based access checks, a passive
vulnerability scan (OWASP ZAP), and a dependency audit. Each sub-item below was actually run
where this sandbox allows it; where a tool could not run here, that is stated plainly rather
than silently skipped.

## 1. Role-based access control checks

Already evidenced at the API level by the committed/exploratory test suites (not duplicated
here):

- `tests/team/api/test_stock_api.py::TestStockAddEndpoint` / `TestStockRemoveEndpoint` —
  unauthenticated and non-privileged users are rejected (401/403) before any quantity change.
- `docs/04_exploratory_qa_findings.md`, Probe #8 — a read-only (view-permission) user attempts
  `/api/stock/add/`: request is blocked with 403, item quantity is unchanged. Confirms BR
  enforcement at the HTTP layer, not just in the model.

**Not done**: role-based checks as Playwright *UI* tests (i.e. logging in as each of the 2
project roles through the real React frontend and confirming the add/remove-stock controls
are hidden or rejected in the UI, not just the API). This needs a running frontend dev server
and a working Playwright browser binary — see Area 3 / Section 3 below for why that binary
could not be installed in this sandbox. Left for whoever continues with Playwright available.

## 2. OWASP ZAP passive scan

**Not run.** `zap.sh` / `zap-cli` / the ZAP Docker image are not available in this sandbox:

```
$ which zap.sh zap-cli
(no output — neither binary exists on PATH)
```

ZAP itself is normally run either as a Docker container (`ghcr.io/zaproxy/zaproxy`) or a
downloaded desktop/CLI install. Both routes are blocked here for the same reason already
documented for SonarQube and Playwright: this sandbox's network allowlist does not permit
Docker Hub/GHCR image pulls or arbitrary binary downloads from outside the allowlisted
package registries.

This is **sandbox-specific, not a real-world blocker** — a normal dev machine or GitHub
Actions runner (ZAP publishes an official `zaproxy/action-full-scan` GitHub Action) can run
this against the dev server with no code changes needed. Recommended command for whoever
continues:

```bash
# with the InvenTree dev server running locally on :8000
docker run -t ghcr.io/zaproxy/zaproxy zap-baseline.py -t http://host.docker.internal:8000 -r zap_report.html
```

## 3. Dependency audit

Both halves of this sub-requirement **were** run successfully in this sandbox — no Docker
or browser binary is needed for a pure dependency-metadata scan.

### 3a. Backend — `pip-audit` on `mis/src/backend/requirements.txt`

```bash
pip install --break-system-packages pip-audit
pip-audit -r mis/src/backend/requirements.txt --format json
```

**Result: clean. 165 packages scanned, 0 with known vulnerabilities** (every package's
`vulns` array is empty — a genuine clean scan, not merely "no CVE lookup attempted"). Sample
of scanned packages: `django==5.2.19`, `djangorestframework==3.18.3`, `cryptography==50.0.2`,
`pillow==13.0.0`, `requests==2.34.2`, plus 160 others — all current/recent pinned versions,
consistent with why the scan is clean.

### 3b. Frontend — `npm audit` on `mis/src/frontend/package.json`

```bash
cd mis/src/frontend
npm install --package-lock-only --legacy-peer-deps   # generate a lockfile only; no browser
                                                       # binaries are downloaded by this step
npm audit --json
```

**Result: 12 vulnerabilities found (3 high, 9 moderate, 0 critical)** across 946 resolved
packages (360 prod, 584 dev, 59 optional). All are in **build-tooling / dev dependencies**,
not in code shipped to end users in production — notable since that materially limits real
exploitability, and that distinction is itself a thing a security assessment should state
rather than just quoting counts:

| Package | Severity | Issue | In production bundle? |
|---|---|---|---|
| `zod` (`<4.6.6`) | High | Memory-exhaustion DoS validating oversized constrained collections ([GHSA-mrhx-c7xc-m3w5](https://github.com/advisories/GHSA-mrhx-c7xc-m3w5)) | Used by `@codecov/*` build plugins (coverage-upload tooling), not app runtime code |
| `@codecov/bundler-plugin-core`, `@codecov/vite-plugin` | High | Transitively pull the vulnerable `zod` above | No — Vite build-time coverage-upload plugin only |
| `react-router` / `react-router-dom` (`6.0.0 - 7.17.0`) | Moderate | Open redirect via backslash in `<Link>`/`useNavigate` ([GHSA-wrjc-x8rr-h8h6](https://github.com/advisories/GHSA-wrjc-x8rr-h8h6)); arbitrary constructor injection via `deserializeErrors()` in SSR hydration ([GHSA-337j-9hxr-rhxg](https://github.com/advisories/GHSA-337j-9hxr-rhxg)) | **Yes** — this is a real runtime dependency and the one finding here that matters for production; InvenTree's React SPA does not use SSR, which removes the second CVE's attack surface, but the open-redirect issue is still relevant client-side routing behaviour |
| `glob`, `minimatch`, `rimraf`, `nyc`, `test-exclude`, `vite-plugin-istanbul` | Moderate | ReDoS / path-traversal-adjacent issues in file-globbing used by test/coverage tooling | No — dev/test tooling only |
| `@lingui/cli` | Moderate | (transitive, via the same glob/minimatch chain) | No — i18n build-time CLI only |

**Action implication for whoever continues (not performed here, per QA-only scope):** bump
`react-router`/`react-router-dom` past `7.17.0` is the one fix with real production
relevance; the rest are `npm audit fix` candidates in dev tooling with low urgency.

## Reproducing

```bash
# backend
pip install --break-system-packages pip-audit
pip-audit -r mis/src/backend/requirements.txt

# frontend
cd mis/src/frontend
npm install --legacy-peer-deps   # or --package-lock-only if you only want the audit,
                                   # not the full node_modules install
npm audit
```

## Summary

| Sub-requirement | Status |
|---|---|
| Role-based access checks (API level) | ✅ Done — see `test_stock_api.py`, `04_exploratory_qa_findings.md` Probe #8 |
| Role-based access checks (UI/Playwright level) | ❌ Blocked on Playwright browser binary (sandbox network restriction) |
| OWASP ZAP passive scan | ❌ Blocked — ZAP needs Docker/binary download, unavailable in this sandbox |
| Dependency audit — backend (`pip-audit`) | ✅ Done — 165 packages, 0 vulnerabilities |
| Dependency audit — frontend (`npm audit`) | ✅ Done — 12 found (3 high / 9 moderate), triaged above; 1 production-relevant (react-router) |

## Continuation verification — Eman Hassan

Playwright confirmed the view-only user can inspect Stock Details and has no enabled adjustment controls. The portable ZAP daemon processed three nominated unauthenticated local responses. The reported framing and CSP alerts arose on the Vite development page. The run also reported content-type/header information findings. The scope covers development responses only. See [execution evidence](12_execution_evidence.md).

The backend rerun audited 165 packages and returned zero known vulnerabilities. For the frontend, a frozen Yarn install provided the observed versions. The npm registry Bulk Advisory endpoint returned five direct records across four packages: `glob`, `minimatch`, `react-router` and `zod`. Four advisories were moderate and one high. The snapshot included 638 unique package names. npm's tree listing flagged existing resolution mismatches, so the input and raw response are retained for interpretation. Direct advisory counts differ from npm audit's dependency-chain aggregation. These results do not establish reachability. See [versions](evidence/2026-11-25/npm-bulk-input.json) and [response](evidence/2026-11-25/npm-bulk-output.json).
