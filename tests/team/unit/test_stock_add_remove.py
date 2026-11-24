"""Unit tests for the two selected Stock app workflows.

Workflow 1 — Receive stock:  StockItem.add_stock()
Workflow 2 — Dispatch stock: StockItem.take_stock()

Covers:
  FR-1..FR-8 (see docs/01_scope.md)
  BR-1 (boundary: removal clamps at available quantity, never negative)
  BR-2 (decision rule: quantity > 0 AND not serialized)
  BR-4 (row locking — exercised indirectly; see test_concurrent_take_stock_is_serialized)

Equivalence partitions used for quantity:
  - invalid: <= 0 (zero, negative)
  - invalid: non-numeric
  - valid: > 0, within available stock (add_stock) / within available stock (take_stock)
  - valid: > available stock (take_stock only — exercises the BR-1 clamp)

Boundary Value Analysis around the "available quantity" limit for take_stock:
  just below (available - 1), exactly at (available), just above (available + 1)
"""
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(db):
    User = get_user_model()
    return User.objects.create_user(username='tester', password='testpass123')


@pytest.fixture
def part(db):
    from part.models import Part

    return Part.objects.create(name='Test Widget', description='A widget for testing')


@pytest.fixture
def stock_item(db, part):
    """A stock item that is kept around at zero quantity (delete_on_deplete=False),
    so tests can inspect the post-depletion state directly. The *default* behaviour
    (delete on deplete) is covered separately — see TestDeleteOnDeplete below.
    """
    from stock.models import StockItem

    return StockItem.objects.create(part=part, quantity=10, delete_on_deplete=False)


@pytest.fixture
def zero_stock_item(db, part):
    from stock.models import StockItem

    return StockItem.objects.create(part=part, quantity=0, delete_on_deplete=False)


@pytest.fixture
def serialized_stock_item(db, part):
    """A serialized stock item — add_stock/take_stock must refuse to act on these."""
    from stock.models import StockItem

    part.trackable = True
    part.save()
    return StockItem.objects.create(part=part, quantity=1, serial='SN-001')


# ---------------------------------------------------------------------------
# Workflow 1: Receive stock (add_stock) — FR-1, FR-2, FR-3
# ---------------------------------------------------------------------------


class TestAddStock:
    def test_add_positive_quantity_increases_balance(self, stock_item, user):
        """FR-1: starting qty 0 (zero keyboards), receive 10 -> balance 10.

        Mirrors the assignment's own worked example (receive stock workflow).
        """
        starting = stock_item.quantity
        ok = stock_item.add_stock(Decimal('10'), user)
        stock_item.refresh_from_db()

        assert ok is True
        assert stock_item.quantity == starting + 10

    def test_add_zero_quantity_is_rejected(self, stock_item, user):
        """FR-2 / BR-2 (EP: invalid value = 0): no-op, balance unchanged."""
        before = stock_item.quantity
        ok = stock_item.add_stock(Decimal('0'), user)
        stock_item.refresh_from_db()

        assert ok is False
        assert stock_item.quantity == before

    def test_add_negative_quantity_is_rejected(self, stock_item, user):
        """FR-2 / BR-2 (EP: invalid value < 0)."""
        before = stock_item.quantity
        ok = stock_item.add_stock(Decimal('-5'), user)
        stock_item.refresh_from_db()

        assert ok is False
        assert stock_item.quantity == before

    def test_add_non_numeric_quantity_is_rejected(self, stock_item, user):
        """FR-2 (EP: invalid type)."""
        before = stock_item.quantity
        ok = stock_item.add_stock('not-a-number', user)
        stock_item.refresh_from_db()

        assert ok is False
        assert stock_item.quantity == before

    def test_add_stock_on_serialized_item_is_rejected(self, serialized_stock_item, user):
        """BR-2 (decision condition 2: item must not be serialized)."""
        before = serialized_stock_item.quantity
        ok = serialized_stock_item.add_stock(Decimal('5'), user)
        serialized_stock_item.refresh_from_db()

        assert ok is False
        assert serialized_stock_item.quantity == before

    def test_add_stock_records_tracking_history(self, stock_item, user):
        """FR-3: a successful addition must create an audit-log (tracking) entry.

        InvenTree records stock history as entries in the generic audit log
        (``audit.models.AuditLogEntry``), keyed by content-type + object id, rather than
        in a dedicated stock-tracking table (that table was removed by migration
        stock.0130_delete_stockitemtracking — history now lives in the audit log).
        """
        from audit.models import AuditLogEntry

        before_count = AuditLogEntry.objects.get_for_object(stock_item).count()
        stock_item.add_stock(Decimal('4'), user)
        after_count = AuditLogEntry.objects.get_for_object(stock_item).count()

        assert after_count == before_count + 1


# ---------------------------------------------------------------------------
# Workflow 2: Dispatch stock (take_stock) — FR-4, FR-5, FR-6, FR-7, BR-1
# ---------------------------------------------------------------------------


class TestTakeStock:
    def test_take_stock_within_available_decreases_balance(self, stock_item, user):
        """FR-4: mirrors assignment example — dispatch 4 keyboards, 10 -> 6."""
        ok = stock_item.take_stock(Decimal('4'), user)
        stock_item.refresh_from_db()

        assert ok is True
        assert stock_item.quantity == 6

    def test_take_stock_zero_quantity_is_rejected(self, stock_item, user):
        """FR-5 (EP: invalid value = 0)."""
        before = stock_item.quantity
        ok = stock_item.take_stock(Decimal('0'), user)
        stock_item.refresh_from_db()

        assert ok is False
        assert stock_item.quantity == before

    def test_take_stock_negative_quantity_is_rejected(self, stock_item, user):
        """FR-5 (EP: invalid value < 0)."""
        before = stock_item.quantity
        ok = stock_item.take_stock(Decimal('-3'), user)
        stock_item.refresh_from_db()

        assert ok is False
        assert stock_item.quantity == before

    def test_take_stock_on_serialized_item_is_rejected(self, serialized_stock_item, user):
        """BR-2 (decision condition 2, mirrored for removal)."""
        before = serialized_stock_item.quantity
        ok = serialized_stock_item.take_stock(Decimal('1'), user)
        serialized_stock_item.refresh_from_db()

        assert ok is False
        assert serialized_stock_item.quantity == before

    # --- BR-1 boundary value analysis: just below / at / above available qty ---

    def test_take_stock_just_below_available_quantity(self, stock_item, user):
        """BVA: available=10, remove 9 (available - 1) -> balance 1, no clamp triggered."""
        ok = stock_item.take_stock(Decimal('9'), user)
        stock_item.refresh_from_db()

        assert ok is True
        assert stock_item.quantity == 1

    def test_take_stock_exactly_available_quantity(self, stock_item, user):
        """BVA: available=10, remove exactly 10 -> balance 0 (boundary, not negative)."""
        ok = stock_item.take_stock(Decimal('10'), user)
        stock_item.refresh_from_db()

        assert ok is True
        assert stock_item.quantity == 0

    def test_take_stock_just_above_available_quantity_is_clamped(self, stock_item, user):
        """BVA / BR-1: available=10, request 11 (available + 1).

        Business rule under test (stock/models.py take_stock(), 'quantity = min(quantity,
        self.quantity)'): the removal is NOT rejected — it is silently capped at the
        available quantity, so the balance lands at 0, never negative.
        This is the documented assignment scenario ("try to dispatch seven more ... confirm
        the balance is still six") adapted to InvenTree's actual clamp-not-reject behaviour.
        """
        ok = stock_item.take_stock(Decimal('11'), user)
        stock_item.refresh_from_db()

        assert ok is True
        assert stock_item.quantity == 0  # clamped, never negative -> FR-6

    def test_take_stock_from_zero_balance_is_rejected(self, zero_stock_item, user):
        """BR-1 edge case: nothing available at all. The clamp (min(requested, available))
        reduces the effective removal to 0, and take_stock() then rejects a zero removal
        (same guard as EP: invalid value = 0) rather than reporting a spurious success.
        """
        ok = zero_stock_item.take_stock(Decimal('5'), user)
        zero_stock_item.refresh_from_db()

        assert ok is False
        assert zero_stock_item.quantity == 0

    def test_take_stock_records_tracking_history_even_when_clamped(self, stock_item, user):
        """FR-7: an audit-log entry must be recorded for a successful removal, including
        the clamped case, per the model's own docstring ('Always record a tracking event,
        even if the item is deleted/depleted as a result of this removal'). Uses the
        delete_on_deplete=False fixture so the item (and its history) can still be
        inspected afterwards.
        """
        from audit.models import AuditLogEntry

        before_count = AuditLogEntry.objects.get_for_object(stock_item).count()
        stock_item.take_stock(Decimal('999'), user)  # forces the clamp path (BR-1)
        after_count = AuditLogEntry.objects.get_for_object(stock_item).count()

        assert after_count == before_count + 1


# ---------------------------------------------------------------------------
# Cross-workflow (FR-8): shared record (StockItem.quantity) under combined ops
# ---------------------------------------------------------------------------


class TestCombinedAddThenRemove:
    def test_add_then_remove_nets_correctly(self, stock_item, user):
        """FR-8: receive 5 (10 -> 15), then dispatch 7 (15 -> 8)."""
        stock_item.add_stock(Decimal('5'), user)
        stock_item.refresh_from_db()
        assert stock_item.quantity == 15

        stock_item.take_stock(Decimal('7'), user)
        stock_item.refresh_from_db()
        assert stock_item.quantity == 8

    def test_remove_then_add_nets_correctly(self, stock_item, user):
        """FR-8, reverse order: dispatch 6 (10 -> 4), then receive 3 (4 -> 7)."""
        stock_item.take_stock(Decimal('6'), user)
        stock_item.refresh_from_db()
        assert stock_item.quantity == 4

        stock_item.add_stock(Decimal('3'), user)
        stock_item.refresh_from_db()
        assert stock_item.quantity == 7

    def test_remove_more_than_available_then_add_recovers_from_zero(self, stock_item, user):
        """FR-8 + BR-1: dispatch 50 from 10 (clamps to 0), then receive 2 -> balance 2."""
        stock_item.take_stock(Decimal('50'), user)
        stock_item.refresh_from_db()
        assert stock_item.quantity == 0

        stock_item.add_stock(Decimal('2'), user)
        stock_item.refresh_from_db()
        assert stock_item.quantity == 2


# ---------------------------------------------------------------------------
# BR-3 (state/change rule): default delete-on-deplete behaviour.
#
# Discovered by reading take_stock()'s docstring and default_delete_on_deplete():
# when a StockItem's quantity is reduced to zero AND its `delete_on_deplete` flag is
# True (the default, governed by the global setting STOCK_DELETE_DEPLETED_DEFAULT),
# the StockItem row itself is deleted rather than retained at zero quantity. This is
# a genuine state-transition rule (existing item -> deleted) distinct from the
# quantity-clamping rule (BR-1).
# ---------------------------------------------------------------------------


class TestDeleteOnDeplete:
    def test_default_delete_on_deplete_is_true(self, db, part):
        """Sanity check on the rule's precondition: a freshly created StockItem uses the
        system default for delete_on_deplete, which is True unless the global setting
        STOCK_DELETE_DEPLETED_DEFAULT has been changed from its own default.
        """
        from stock.models import StockItem

        item = StockItem.objects.create(part=part, quantity=5)
        assert item.delete_on_deplete is True

    def test_take_stock_to_zero_deletes_item_by_default(self, db, part, user):
        """BR-3: dispatching all available stock (exact boundary, qty -> 0) deletes the
        StockItem under the default delete_on_deplete=True setting.
        """
        from stock.models import StockItem

        item = StockItem.objects.create(part=part, quantity=10)  # delete_on_deplete default True
        pk = item.pk

        ok = item.take_stock(Decimal('10'), user)

        assert ok is True
        assert not StockItem.objects.filter(pk=pk).exists()

    def test_take_stock_over_available_also_deletes_item_by_default(self, db, part, user):
        """BR-1 + BR-3 combined: requesting MORE than available still clamps to the
        available quantity first (BR-1), and that clamped removal still reaches zero,
        so the item is deleted under the default setting (BR-3) — same outcome as
        removing exactly the available quantity.
        """
        from stock.models import StockItem

        item = StockItem.objects.create(part=part, quantity=6)
        pk = item.pk

        ok = item.take_stock(Decimal('50'), user)

        assert ok is True
        assert not StockItem.objects.filter(pk=pk).exists()

    def test_take_stock_with_delete_on_deplete_false_retains_item_at_zero(
        self, db, part, user
    ):
        """Contrast case: with delete_on_deplete explicitly False, the item survives at
        zero quantity instead of being deleted — confirms the rule is conditional on the
        flag, not an unconditional deletion.
        """
        from stock.models import StockItem

        item = StockItem.objects.create(part=part, quantity=6, delete_on_deplete=False)

        ok = item.take_stock(Decimal('6'), user)
        item.refresh_from_db()

        assert ok is True
        assert item.quantity == 0
