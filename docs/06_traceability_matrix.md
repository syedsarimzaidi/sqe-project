# Traceability Matrix

Maps every functional requirement (FR) and business rule (BR) from `docs/01_scope.md` to the
concrete test(s) that cover it, across all test layers actually built in this project (unit,
API/EP-BVA, mutation). Compiled from the test files themselves (function names below are
copy-pasted from source, not re-typed from memory) so this matrix cannot silently drift from
what's actually committed.

Columns: **Unit** = `tests/team/unit/test_stock_add_remove.py`. **API** =
`tests/team/api/test_stock_api.py`. **Mutation** = mutant(s) in `tests/team/mutation/mutants.py`
whose kill/survival specifically exercises this requirement (see `docs/mutation_report.md` for
full kill/survive detail per mutant).

## Functional Requirements

| ID | Requirement | Unit test(s) | API test(s) | Mutation |
|---|---|---|---|---|
| FR-1 | Allow authenticated user w/ add-stock permission to increase quantity | `test_add_positive_quantity_increases_balance` | `test_add_endpoint_increases_quantity`, `test_add_endpoint_requires_authentication` | M06 (CR on final `return True`), M08 (AOR on `+`), M14 (lock-guard deletion) |
| FR-2 | Reject stock-add request with quantity ≤ 0 | `test_add_zero_quantity_is_rejected`, `test_add_negative_quantity_is_rejected`, `test_add_non_numeric_quantity_is_rejected` | `test_add_endpoint_ep_classes` (EP: zero/negative/non-numeric classes) | **M01** (ROR on the `quantity <= 0` guard, killed) |
| FR-3 | Record tracking/history entry for every successful stock addition | `test_add_stock_records_tracking_history` | — (covered at unit level; API test suite asserts quantity readback, not history entries directly) | — (no mutant targets the `tracking_event(STOCK_ADD, ...)` call itself — see "Known gaps" below) |
| FR-4 | Allow authenticated user w/ remove-stock permission to decrease quantity | `test_take_stock_within_available_decreases_balance` | `test_remove_endpoint_decreases_quantity`, `test_remove_endpoint_requires_authentication` | M07 (CR on final `return True`), M09 (AOR on `-`), M15 (lock-guard deletion) |
| FR-5 | Reject stock-remove request with quantity ≤ 0 | `test_take_stock_zero_quantity_is_rejected`, `test_take_stock_negative_quantity_is_rejected`, `test_take_stock_non_numeric_quantity_is_rejected` | `test_remove_endpoint_ep_classes` (EP classes) | **M02 — SURVIVED** (true equivalent mutant: the pre-clamp `<= 0` guard it mutates is backed by an identical, unmutated post-clamp guard — see mutation report for the full trace) |
| FR-6 | Never allow quantity to fall below zero regardless of removal amount (BR-1) | `test_take_stock_just_below_available_quantity`, `test_take_stock_exactly_available_quantity`, `test_take_stock_just_above_available_quantity_is_clamped`, `test_take_stock_from_zero_balance_is_rejected` | `test_remove_just_below_available_quantity`, `test_remove_at_available_quantity_boundary`, `test_remove_just_above_available_quantity_clamps` (BVA triples, generated from OpenAPI spec) | **M10 `ClampInversion`** (custom operator, killed), M03 (ROR on the post-clamp guard, killed) |
| FR-7 | Record tracking/history entry for every removal, incl. clamped case | `test_take_stock_records_tracking_history_even_when_clamped`, `test_take_stock_with_record_tracking_false_skips_history` | — | **M13 — SURVIVED** (collapses the `record_tracking` conditional; existing test only asserts return value + quantity, not which tracking path ran — documented test gap, see mutation report) |
| FR-8 | Net effect of combined add/remove sequences reflected correctly | `test_add_then_remove_nets_correctly`, `test_remove_then_add_nets_correctly`, `test_remove_more_than_available_then_add_recovers_from_zero` | `test_quantity_readback_after_add_then_remove`, `test_quantity_readback_after_rejected_request`, `test_repeating_the_same_add_request_applies_each_time_independently` | — (covered by composition of the FR-1/FR-4/FR-6 mutants above, not a distinct mutant of its own) |

## Business Rules

| ID | Rule | Unit test(s) | API test(s) | Mutation |
|---|---|---|---|---|
| BR-1 | Removal clamp: `quantity = min(requested, available)`, never goes negative | `test_take_stock_just_below_available_quantity`, `test_take_stock_exactly_available_quantity`, `test_take_stock_just_above_available_quantity_is_clamped` | `test_remove_just_below_available_quantity`, `test_remove_at_available_quantity_boundary`, `test_remove_just_above_available_quantity_clamps` | **M10 `ClampInversion`** (custom operator — kills if the clamp direction is inverted) |
| BR-2 | Decision rule: process only if quantity valid **and** item not serialized | `test_add_stock_on_serialized_item_is_rejected`, `test_take_stock_on_serialized_item_is_rejected` (serialized half); `test_add_zero_quantity_is_rejected`, `test_take_stock_zero_quantity_is_rejected` (quantity-valid half) | Probe #11 in `docs/04_exploratory_qa_findings.md` (serialized guard holds at HTTP layer too) | **M11 / M12 `SerializedGuardRemoval`** (custom operator, both killed) |
| BR-3 | State transition: item deleted when quantity hits 0 **and** `delete_on_deplete=True` (default) | `test_default_delete_on_deplete_is_true`, `test_take_stock_to_zero_deletes_item_by_default`, `test_take_stock_over_available_also_deletes_item_by_default`, `test_take_stock_with_delete_on_deplete_false_retains_item_at_zero` | — (not exercised at API level; deletion-on-deplete is a model-level side effect not asserted via the endpoint tests) | — (not a mutation target in this pass; see "Gaps" below) |
| BR-4 | Row lock (`lock_quantity()`) taken before read/write, serializing concurrent add/remove | *Not directly tested for concurrency* — `lock_quantity()`'s call is exercised implicitly by every add/remove test (the method is invoked on every call), but no test specifically asserts concurrent-request serialization (would need a multi-threaded/multi-process test) | — | M14 (add_stock, lock-guard deletion, killed), M15 (take_stock, lock-guard deletion, killed) — confirms the guard's *presence* matters, not that locking is race-safe under real concurrency |

## Exploratory findings (not requirement-driven, but worth cross-referencing)

| Finding | Source | Related FR/BR |
|---|---|---|
| Issue #3 — NaN quantity crashes `add_stock()`/`take_stock()` at model level | `docs/04_exploratory_qa_findings.md`, Probe #9 | FR-2/FR-5 (quantity validation) — reveals the model-level guard is *not* a complete substitute for the serializer-level one |
| Issue #4 — 10-digit quantity overflows `max_digits=15`, corrupts row | `docs/04_exploratory_qa_findings.md`, Probe #10 | FR-1 (quantity increase) — reveals a gap between schema-level and DB-field-level validation |

## Known gaps (stated honestly, not hidden)

- **BR-3** has no API-level test and no mutation coverage. It is thoroughly covered at the
  unit level (4 dedicated tests), but was only discovered in this project via unit testing
  against the model directly — the API endpoints (`/api/stock/add/`, `/api/stock/remove/`)
  do not themselves expose row-deletion behaviour in their response body, so an API-level
  assertion would need a follow-up `GET` to confirm the row is gone (not currently written).
- **BR-4** (locking) has no dedicated concurrency test. Verifying it properly would require a
  multi-threaded or multi-process test harness (e.g. two threads calling `take_stock()`
  simultaneously via `transaction.atomic()` + a deliberate delay) which was out of scope for
  the time available in this pass. This is a legitimate remaining gap, not an oversight to
  paper over.
- **FR-3/FR-7** (tracking history) are unit-tested against `AuditLogEntry.objects.get_for_object()`
  directly but not independently re-asserted at the API layer (the API tests check the
  resulting `quantity`, not the audit log).

These three gaps are reasonable candidates for the "what would you add with more time" section
of the final report / viva, since they are identified and explained here rather than silently
missing.
