# SE3002 — Software Quality Engineering Final Project

**Student:** Syed Sarim Zaidi
**Selected MIS:** [InvenTree](https://github.com/inventree/inventree) — open-source Inventory Management System
**Baseline commit:** `4f5fbc091b8066d29445495d3e177078df7abfcd`
**License:** MIT

## Repository layout

- `mis/` — baseline InvenTree application source, vendored at the commit above (Django backend + frontend).
  This is the **system under test**; it is not modified except where a documented fix is made (see
  `docs/` for the one deliberate fix required by the assignment).
- `tests/team/` — all test code written for this project (unit, API/integration, end-to-end).
  Upstream's own tests earn no marks and are kept separate from this folder.
- `docs/` — test plan, risk register, traceability matrix, business rules, reports, and all
  other required documentation.
- `.github/workflows/` — CI pipeline (SonarQube, tests, mutation testing, coverage gate).

## Selected module & workflows

Stock app — **Receive stock** (`add_stock`) and **Dispatch stock** (`take_stock`).
See `docs/01_scope.md` for full scope, requirements, business rules, roles, and setup
instructions.

## Running the application locally

See the "Environment — setup, start, seed, reset" section in `docs/01_scope.md`.

## AI-use disclosure

See `docs/ai_use_record.md`.
