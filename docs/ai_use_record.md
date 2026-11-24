# AI-Use Record

Per the assignment's AI-use and plagiarism policy, every use of a generative AI tool on this
project is disclosed here. Entries are added as work is produced; **each output listed here
must be independently reviewed, understood, and (where necessary) corrected by the student
before submission** — this record discloses use, it does not substitute for that review.

| Date | Tool | Purpose | Output produced | What was checked / changed |
|---|---|---|---|---|
| 2026-11-24 | Claude (Anthropic) | Selecting a suitable open-source MIS matching the registration criteria, and setting up a working local instance (SQLite backend, no Docker) | Repo choice (InvenTree), environment setup commands, running dev server | Verified server starts and responds (`/api/` returns 200), commit hash captured directly from `git rev-parse HEAD`, business rules verified by reading the actual `stock/models.py` source rather than assumed |
| 2026-11-24 | Claude (Anthropic) | Drafting Section 1 test scope document (requirements, business rules, roles, setup/reset steps) | `docs/01_scope.md` | Business-rule claims cross-checked against cited source file/line numbers in `mis/src/backend/InvenTree/stock/models.py` |

| 2026-11-24 | Claude (Anthropic) | Writing unit tests for `add_stock`/`take_stock` (EP, BVA, business-rule coverage) | `tests/team/unit/test_stock_add_remove.py` | Every test was actually executed against the vendored baseline (`python -m pytest`), not just written. Two initial assumptions were found to be wrong when the tests were run (tracking history API, and removal from an already-zero balance returning False rather than True) and were corrected after reading the real source. One additional real business rule (`delete_on_deplete` — see BR-3) was discovered this way and added to the scope doc rather than assumed up front. Final state: 22/22 tests passing. |

*(Continue adding a row for every further AI-assisted artifact — test code, CI config, report
sections, etc. Keep prompts used, per the assignment's requirement to "keep your prompts.")*
