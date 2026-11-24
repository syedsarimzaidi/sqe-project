# SE3002 — Section 1: Test Scope Definition

## Repository

| Field | Value |
|---|---|
| Name | InvenTree |
| Upstream URL | https://github.com/inventree/inventree/ |
| License | MIT |
| Baseline commit hash | `4f5fbc091b8066d29445495d3e177078df7abfcd` |
| Backend | Python 3.12 / Django 5.2 |
| Interface | Web UI (React/Mantine frontend) + full REST/HTTP API |
| Storage | SQLite (dev) / PostgreSQL (prod) — persistent |
| Module selected | **Stock** app (`src/backend/InvenTree/stock/`) |

Chosen because it satisfies all registration criteria: usable browser interface, HTTP API for
the selected workflows, persistent storage, testable source code, and is **not** ERPNext.

## Selected Workflows (same module: Stock)

### Workflow 1 — Receive Stock (`add_stock`)
- **Starting condition:** A `StockItem` exists with a known quantity (e.g. 0).
- **User action:** Authenticated user with stock-add permission calls `POST /api/stock/add/`
  (or UI equivalent) with a positive quantity.
- **Expected outcome:** `StockItem.quantity` increases by the supplied amount; a tracking
  history entry (`StockHistoryCode.STOCK_ADD`) is recorded.
- **Source:** `stock/models.py`, `StockItem.add_stock()`, lines 3409–3459 (commit above).

### Workflow 2 — Dispatch Stock (`take_stock`)
- **Starting condition:** A `StockItem` exists with a known non-zero quantity.
- **User action:** Authenticated user with stock-remove permission calls `POST /api/stock/remove/`
  with a quantity to remove.
- **Expected outcome:** `StockItem.quantity` decreases by the supplied amount, **clamped** to
  never go below zero (business rule — see BR-1 below); a tracking history entry
  (`StockHistoryCode.STOCK_REMOVE`) is recorded.
- **Source:** `stock/models.py`, `StockItem.take_stock()`, lines 3462–3529 (commit above).

### Shared record between workflows
`StockItem.quantity` (and its tracking history) — Workflow 1 writes to it (increases),
Workflow 2 reads it (to clamp) and writes to it (decreases). This is the shared record
required by the assignment.

## Functional Requirements (8 total, ≥3 per workflow)

**Receive stock (Workflow 1):**
1. FR-1: The system shall allow an authenticated user with add-stock permission to increase
   the quantity of an existing, non-serialized `StockItem`.
2. FR-2: The system shall reject a stock-add request with quantity ≤ 0.
3. FR-3: The system shall record a tracking/history entry for every successful stock addition.

**Dispatch stock (Workflow 2):**
4. FR-4: The system shall allow an authenticated user with remove-stock permission to decrease
   the quantity of an existing, non-serialized `StockItem`.
5. FR-5: The system shall reject a stock-remove request with quantity ≤ 0.
6. FR-6: The system shall never allow `StockItem.quantity` to fall below zero, regardless of
   the requested removal amount (see BR-1).
7. FR-7: The system shall record a tracking/history entry for every successful stock removal,
   including the case where the removed amount was clamped.

**Cross-workflow:**
8. FR-8: The system shall reflect the net effect of combined add/remove operations correctly
   in `StockItem.quantity` when operations are issued in sequence (add then remove, or
   remove then add).

## Business Rules (4 total)

- **BR-1 (boundary/limit):** Removing more stock than is currently available does not error —
  the removal is silently capped at the available quantity
  (`quantity = min(requested_quantity, self.quantity)`), so `StockItem.quantity` can never go
  negative. *Boundary values to test: just below available qty, exactly available qty, just
  above available qty.*
- **BR-2 (decision with ≥2 Boolean conditions):** A stock addition/removal is only processed
  when **(a)** the supplied quantity is a valid positive Decimal **and** **(b)** the
  `StockItem` is **not** serialized (`self.serialized == False`). If either condition is
  false, the operation is rejected/no-ops.
- **BR-3 (state transition — delete on deplete):** When a stock removal reduces
  `StockItem.quantity` to exactly zero, and the item's `delete_on_deplete` flag is `True`
  (the default, governed by the global setting `STOCK_DELETE_DEPLETED_DEFAULT`), the
  `StockItem` row itself is **deleted** rather than retained at zero quantity
  (`stock/models.py`, `default_delete_on_deplete()`, lines 363–373, and `take_stock()`'s own
  docstring: *"whether or not this item survives the removal"*). With `delete_on_deplete`
  explicitly set `False`, the item instead survives at zero quantity. This is a genuine
  state-transition rule (existing → deleted) distinct from the quantity-clamping rule (BR-1),
  and was confirmed empirically by unit tests (`tests/team/unit/test_stock_add_remove.py`,
  class `TestDeleteOnDeplete`) rather than assumed from documentation alone.
- **BR-4 (concurrency/locking rule):** Both operations acquire a row lock
  (`self.lock_quantity()`) before reading/writing quantity, so concurrent add/remove requests
  on the same `StockItem` are serialized rather than racing (prevents lost updates).

## User Roles (2, different permissions)

InvenTree uses a `RuleSet`-based permission system (per-app `view` / `add` / `change` /
`delete` flags assigned to Groups — `users/models.py`, `RuleSet` class, line 438).

| Role | Permissions on `stock` app |
|---|---|
| **Stock Operator** | view + add + change (can receive and dispatch stock) |
| **Auditor / Viewer** | view only (can see stock levels and history, cannot add/remove) |

## Test basis

Expected behaviour above is taken directly from the `StockItem.add_stock()` and
`StockItem.take_stock()` source (cited with file/line numbers), not from assumption, except
where noted. This satisfies "state the expected behaviour using repository documentation or
a justified assumption."

## Environment — setup, start, seed, reset

```bash
# Install
git clone https://github.com/inventree/inventree/
cd inventree
git checkout 4f5fbc091b8066d29445495d3e177078df7abfcd
uv venv --python 3.12 .venv
source .venv/bin/activate
uv pip install -r src/backend/requirements.txt -r src/backend/requirements-dev.txt

# Configure (SQLite, no Docker needed)
mkdir -p data/static data/media data/backup
export INVENTREE_DEBUG=True
export INVENTREE_DB_ENGINE=sqlite3
export INVENTREE_DB_NAME=$(pwd)/inventree_db.sqlite3
export INVENTREE_SECRET_KEY=dev-only-key
export INVENTREE_PLUGINS_ENABLED=False
export INVENTREE_SITE_URL=http://localhost:8000
export INVENTREE_STATIC_ROOT=$(pwd)/data/static
export INVENTREE_MEDIA_ROOT=$(pwd)/data/media
export INVENTREE_BACKUP_DIR=$(pwd)/data/backup

cd src/backend/InvenTree
python manage.py migrate
DJANGO_SUPERUSER_USERNAME=admin DJANGO_SUPERUSER_PASSWORD=AdminPass123! \
  DJANGO_SUPERUSER_EMAIL=admin@example.com python manage.py createsuperuser --noinput
python manage.py collectstatic --noinput

# Start
python manage.py runserver 0.0.0.0:8000
# UI:  http://localhost:8000
# API: http://localhost:8000/api/
# OpenAPI schema: http://localhost:8000/api/schema/

# Reset between test runs
rm /path/to/inventree_db.sqlite3
# then re-run migrate + createsuperuser above
```
