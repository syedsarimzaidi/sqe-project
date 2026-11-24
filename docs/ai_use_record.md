# AI-Use Record

Per the assignment's AI-use and plagiarism policy, every use of a generative AI tool on this
project is disclosed here. Entries are added as work is produced; **each output listed here
must be independently reviewed, understood, and (where necessary) corrected by the student
before submission** — this record discloses use, it does not substitute for that review.

| Date | Tool | Purpose | Output produced | What was checked / changed |
|---|---|---|---|---|
| 2026-11-24 | Claude (Anthropic) | Selecting a suitable open-source MIS matching the registration criteria, and setting up a working local instance (SQLite backend, no Docker) | Repo choice (InvenTree), environment setup commands, running dev server | Verified server starts and responds (`/api/` returns 200), commit hash captured directly from `git rev-parse HEAD`, business rules verified by reading the actual `stock/models.py` source rather than assumed |
| 2026-11-24 | Claude (Anthropic) | Drafting Section 1 test scope document (requirements, business rules, roles, setup/reset steps) | `docs/01_scope.md` | Business-rule claims cross-checked against cited source file/line numbers in `mis/src/backend/InvenTree/stock/models.py` |

*(Continue adding a row for every further AI-assisted artifact — test code, CI config, report
sections, etc. Keep prompts used, per the assignment's requirement to "keep your prompts.")*
