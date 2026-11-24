# Unit Test Coverage — Selected Workflows

Full HTML report: `docs/coverage_html/index.html` (open `stock_models_py.html` for the
line-by-line view).

## Scope of the 100% coverage claim

`stock/models.py` is 1,408 statements in total, covering many unrelated model classes
(`StockLocation`, `StockItemTestResult`, label/report mixins, serial-number helpers, etc.)
that are **outside this project's two selected workflows**. File-wide coverage is
therefore 38% — this is expected and not a shortfall, because the assignment's 100%
coverage requirement applies to "all server-side business logic" for the workflows
actually chosen, not to the entire upstream file.

**The two methods that implement the selected workflows —
`StockItem.add_stock()` (lines 3409–3459) and `StockItem.take_stock()`
(lines 3461–3529) — are 100% statement- and branch-covered** by
`tests/team/unit/test_stock_add_remove.py`. Verified directly against the coverage
report: none of lines 3409–3529 appear in the "Missing" list for the final run.

## Branches exercised (for the MC/DC requirement)

| Condition | Covered by |
|---|---|
| `self.serialized` True / False | `test_add_stock_on_serialized_item_is_rejected`, `test_take_stock_on_serialized_item_is_rejected` |
| `Decimal(quantity)` raises `InvalidOperation` / succeeds | `test_add_non_numeric_quantity_is_rejected`, `test_take_stock_non_numeric_quantity_is_rejected` |
| `quantity <= 0` True / False (pre-clamp) | `test_add_zero_quantity_is_rejected`, `test_add_positive_quantity_increases_balance` |
| `self.lock_quantity()` False (unsaved item) / True | `test_add_stock_on_unsaved_item_is_rejected`, `test_take_stock_on_unsaved_item_is_rejected` |
| `quantity = min(quantity, self.quantity)` clamp taken / not taken (BR-1) | `test_take_stock_just_above_available_quantity_is_clamped`, `test_take_stock_just_below_available_quantity` |
| post-clamp `quantity <= 0` True / False | `test_take_stock_from_zero_balance_is_rejected`, `test_take_stock_within_available_decreases_balance` |
| `record_tracking` True / False | default-path tests, `test_take_stock_with_record_tracking_false_skips_history` |
| `delete_on_deplete` True / False (BR-3) | `TestDeleteOnDeplete` class (all 4 tests) |

## Reproducing

```bash
source .venv/bin/activate   # or wherever the project venv lives
export INVENTREE_DEBUG=True INVENTREE_DB_ENGINE=sqlite3 \
  INVENTREE_DB_NAME=$(pwd)/data/test_db.sqlite3 \
  INVENTREE_SECRET_KEY=test-only-key-not-for-production \
  INVENTREE_PLUGINS_ENABLED=False INVENTREE_SITE_URL=http://localhost:8000 \
  INVENTREE_STATIC_ROOT=$(pwd)/data/static INVENTREE_MEDIA_ROOT=$(pwd)/data/media \
  INVENTREE_BACKUP_DIR=$(pwd)/data/backup
python -m pytest tests/team/unit/test_stock_add_remove.py --create-db \
  --cov=stock.models --cov-report=term-missing --cov-report=html:docs/coverage_html
```
