"""MC/DC witnesses for the compound delete-on-depletion decision."""

from decimal import Decimal
from unittest.mock import Mock

import pytest

from part.models import Part
from stock.models import StockItem


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('new_quantity', 'delete_on_deplete', 'can_delete', 'deleted'),
    [
        (0, True, True, True),
        (1, True, True, False),
        (0, False, True, False),
        (0, True, False, False),
    ],
    ids=['all-true', 'nonzero', 'flag-disabled', 'deletion-denied'],
)
def test_depletion_decision(monkeypatch, new_quantity, delete_on_deplete, can_delete, deleted):
    part = Part.objects.create(name='SQE depletion witness', description='QA fixture')
    item = StockItem.objects.create(
        part=part, quantity=10, delete_on_deplete=delete_on_deplete
    )
    pk = item.pk
    deletion_allowed = Mock(return_value=can_delete)
    monkeypatch.setattr(item, 'can_delete', deletion_allowed)

    assert item.updateQuantity(Decimal(new_quantity)) is (not deleted)

    if new_quantity == 0 and delete_on_deplete:
        deletion_allowed.assert_called_once_with()
    else:
        deletion_allowed.assert_not_called()

    if deleted:
        assert not StockItem.objects.filter(pk=pk).exists()
    else:
        item.refresh_from_db()
        assert item.quantity == new_quantity
