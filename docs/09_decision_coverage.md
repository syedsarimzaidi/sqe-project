# Decision coverage verification

**Student:** Eman Hassan

The 26 existing unit cases passed. The coverage JSON includes separate function totals for `StockItem.add_stock` (20/20 statements and 6/6 branch arcs) and `StockItem.take_stock` (27/27 and 10/10). The same run measured 31% combined line and branch coverage across the entire module. Radon reported complexity 5 and 7 respectively. See [pytest](evidence/2026-11-25/pytest-unit.log), [coverage JSON](evidence/2026-11-25/coverage.json) and [Radon](evidence/2026-11-25/radon.txt).

## MC/DC witness review

The two selected methods implement BR-2 as serial single-condition guards. The table identifies an existing passing case pair for each guard and outcome. Successful fixtures are nonserialized with a valid positive amount and a lockable row. The conversion exceptions and `min()` are separate control-flow behavior. The compound deletion decision resides in the downstream helper and was verified separately.

| Decision | True outcome witness | False outcome witness |
|---|---|---|
| Receive serialized guard | `test_add_stock_on_serialized_item_is_rejected` | `test_add_positive_quantity_increases_balance` |
| Receive amount ≤ 0 | `test_add_zero_quantity_is_rejected` | `test_add_positive_quantity_increases_balance` |
| Receive lock unsuccessful | `test_add_stock_on_unsaved_item_is_rejected` | `test_add_positive_quantity_increases_balance` |
| Dispatch serialized guard | `test_take_stock_on_serialized_item_is_rejected` | `test_take_stock_within_available_decreases_balance` |
| Dispatch input amount ≤ 0 | `test_take_stock_zero_quantity_is_rejected` | `test_take_stock_within_available_decreases_balance` |
| Dispatch lock unsuccessful | `test_take_stock_on_unsaved_item_is_rejected` | `test_take_stock_within_available_decreases_balance` |
| Dispatch clamped amount ≤ 0 | `test_take_stock_from_zero_balance_is_rejected` | `test_take_stock_within_available_decreases_balance` |
| Dispatch tracking enabled | `test_take_stock_records_tracking_history_even_when_clamped` | `test_take_stock_with_record_tracking_false_skips_history` |

The tracking-disabled case currently checks quantity and the return value. Mutation M13 remains relevant to validation of the tracking side effect. The observed branch arcs establish execution of both paths, while the strength of the side-effect oracle is still limited.

## BR-3 compound decision

For `A && B && C` in `updateQuantity()`, A is zero balance, B enables deletion on depletion, and C permits deletion. The additional [unit test](../tests/team/unit/test_stock_depletion_decision.py) ran four witness cases. It controls the result from `can_delete()` and checks whether the actual database row survives. In short-circuited cases C is configured but not evaluated, and the tests assert the absence of that call.

| Witness | A | B | C configured | Row deleted |
|---|---|---|---|---|
| All true | T | T | T | Yes |
| Nonzero balance | F | T | T | No |
| Flag disabled | T | F | T | No |
| Deletion denied | T | T | F | No |

Each false witness differs from the all-true case in one condition. All four targeted tests passed. The new cases verify this decision independently of the internals of `can_delete()`. The BR-3 summary in the original RTM should be read with this predicate in mind. See [pytest MC/DC output](evidence/2026-11-25/pytest-mcdc.log).
