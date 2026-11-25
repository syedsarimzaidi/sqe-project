# Exploratory QA — Additional Findings Beyond the Committed Test Suite

Per instruction, this pass is **QA only — defects are reported, not fixed**. Each probe below
was actually executed (via Django's API test client / direct model calls against the vendored
InvenTree baseline), not hypothesized.

| # | Probe | Result | Verdict |
|---|---|---|---|
| 1 | `add_stock()` with 6-decimal-place quantity (`0.123456789`) via API | 400, rejected — schema allows max 5 decimal places | Correct behaviour |
| 2 | Scientific notation quantity (`1e2`) via API | 201, accepted, treated as `100` | Works as expected (Decimal parses it); worth a note in the report that this is non-obvious input |
| 3 | Same item referenced twice in one `items[]` request (`add` 5 then 3) | 201, both applied → quantity +8 total | No duplicate-detection/merge logic exists; not necessarily a bug, but undocumented behaviour worth flagging in the report |
| 4 | Negative quantity directly to `/api/stock/remove/` | 400, rejected at the serializer level (`min_value`) | Correct — note this is a *second*, independent guard on top of the model-level check already covered in unit tests |
| 5 | Non-existent stock item pk | 400, `does_not_exist` | Correct |
| 6 | Empty `items: []` list | 400, `"A list of stock items must be provided"` | Correct |
| 7 | Missing `quantity` key in request body | 400, `"This field is required."` | Correct |
| 8 | Non-privileged (view-only) user attempts `/api/stock/add/` | 403, request blocked, quantity unchanged | Correct — role/permission enforcement (BR / roles section) confirmed at the HTTP layer |
| 9 | **`add_stock(Decimal('NaN'), user)` called directly (model level)** | **Unhandled `decimal.InvalidOperation` exception** | **BUG — filed as GitHub Issue #3** |
| 9b | Same `"NaN"` value submitted through the public HTTP API | 400, cleanly rejected by DRF's serializer (`"A valid number is required."`) | Not exploitable through normal API use — the crash in #9 requires a direct/internal caller |
| 10 | **Quantity `9999999999` (10 digits, schema-valid) added to an item already holding `10`** | **201 success, but the row becomes unreadable afterwards — `decimal.InvalidOperation` on any subsequent read** | **BUG — filed as GitHub Issue #4 (DB field overflow / data corruption)** |
| 11 | `add_stock()` on a serialized/trackable item via the HTTP API | 403/unchanged — the serialized guard (BR-2b) holds at the API layer too | Correct — consistent with the unit-level `TestAddStock::test_add_stock_on_serialized_item_is_rejected` |

## Defects filed (not fixed, per QA-only scope)

- **Issue #3** — `add_stock()`/`take_stock()` crash with unhandled `decimal.InvalidOperation`
  on a NaN quantity passed directly at the model level (bypasses DRF validation).
- **Issue #4** — A schema-valid, maximum-digit quantity, when added to an item that already
  holds some stock, can push the *total* past the `StockItem.quantity` field's own
  `max_digits=15` storage limit, silently corrupting the row (crashes on next read).

Both are genuine gaps between validation layers (model-level guard vs. serializer-level
schema vs. DB field constraint) rather than anything already covered by the committed test
suite — they were found by probing *beyond* the EP/BVA classes already codified in
`tests/team/unit/test_stock_add_remove.py` and `tests/team/api/generate_test_data.py`.

## Suggested next steps (for whoever picks up the fix work)

1. Issue #3: add an explicit `quantity.is_nan()` (or `is_finite()`) check alongside the
   existing `quantity <= 0` guard in both `add_stock()` and `take_stock()`.
2. Issue #4: validate `self.quantity + quantity` (add) / the clamped result (remove)
   against the field's `max_digits` before calling `updateQuantity()`, or call
   `full_clean()` and catch `ValidationError` before the row is saved.
3. Both would need new regression tests added to `tests/team/unit/test_stock_add_remove.py`
   once fixed, and the corresponding mutation-harness coverage considered.
