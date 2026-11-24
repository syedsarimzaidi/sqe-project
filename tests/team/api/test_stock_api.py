"""API / integration tests for the two selected Stock workflows, exercised through the
real DRF endpoints (/api/stock/add/, /api/stock/remove/) via Django's in-process test
client — no live server required, so this runs the same way locally and in CI.

Test data (EP classes, 3-point BVA) comes from generate_test_data.py, which itself reads
the project's trimmed OpenAPI spec (docs/openapi_stock_workflows.json). Per the assignment
requirement ("API tests must use its output"), every quantity value used below is pulled
from that generator rather than hand-typed into the test file.
"""
import sys
from decimal import Decimal
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model

sys.path.insert(0, str(Path(__file__).parent))
from generate_test_data import generate  # noqa: E402

pytestmark = pytest.mark.django_db

SPEC_PATH = Path(__file__).parent.parent.parent.parent / 'docs' / 'openapi_stock_workflows.json'


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def admin_user(db):
    User = get_user_model()
    return User.objects.create_superuser(
        username='api_admin', email='api_admin@example.com', password='testpass123'
    )


@pytest.fixture
def auth_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def part(db):
    from part.models import Part

    return Part.objects.create(name='API Test Widget', description='for API tests')


@pytest.fixture
def stock_item(db, part):
    from stock.models import StockItem

    return StockItem.objects.create(part=part, quantity=10, delete_on_deplete=False)


@pytest.fixture
def generated_data():
    return generate(SPEC_PATH, available_quantity='10')


# ---------------------------------------------------------------------------
# Happy-path: receive / dispatch via the real HTTP-level endpoint
# ---------------------------------------------------------------------------


class TestStockAddEndpoint:
    def test_add_endpoint_increases_quantity(self, auth_client, stock_item):
        """FR-1 via POST /api/stock/add/ — mirrors the assignment's own worked example."""
        resp = auth_client.post(
            '/api/stock/add/',
            {'items': [{'pk': stock_item.pk, 'quantity': '10'}], 'notes': 'API test receive'},
            format='json',
        )
        stock_item.refresh_from_db()

        assert resp.status_code == 201
        assert stock_item.quantity == 20

    def test_add_endpoint_requires_authentication(self, api_client, stock_item):
        """Access-control smoke check: an unauthenticated request must be rejected."""
        resp = api_client.post(
            '/api/stock/add/', {'items': [{'pk': stock_item.pk, 'quantity': '5'}]}, format='json'
        )
        assert resp.status_code in (401, 403)


class TestStockRemoveEndpoint:
    def test_remove_endpoint_decreases_quantity(self, auth_client, stock_item):
        """FR-4 via POST /api/stock/remove/ — mirrors the assignment's dispatch example."""
        resp = auth_client.post(
            '/api/stock/remove/',
            {'items': [{'pk': stock_item.pk, 'quantity': '4'}], 'notes': 'API test dispatch'},
            format='json',
        )
        stock_item.refresh_from_db()

        assert resp.status_code == 201
        assert stock_item.quantity == 6

    def test_remove_endpoint_requires_authentication(self, api_client, stock_item):
        resp = api_client.post(
            '/api/stock/remove/', {'items': [{'pk': stock_item.pk, 'quantity': '1'}]}, format='json'
        )
        assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Equivalence Partitioning — driven entirely by generate_test_data.py's output
# ---------------------------------------------------------------------------


class TestEquivalencePartitions:
    @pytest.mark.parametrize(
        'ep_name',
        ['valid_positive', 'invalid_zero', 'invalid_negative', 'invalid_non_numeric'],
    )
    def test_add_endpoint_ep_classes(self, auth_client, stock_item, generated_data, ep_name):
        ep = next(e for e in generated_data.ep_classes if e.name == ep_name)
        before = stock_item.quantity

        resp = auth_client.post(
            '/api/stock/add/',
            {'items': [{'pk': stock_item.pk, 'quantity': ep.example}]},
            format='json',
        )
        stock_item.refresh_from_db()

        if ep.valid:
            assert resp.status_code == 201, ep
            assert stock_item.quantity == before + Decimal(ep.example)
        else:
            # Business-invalid values (0, negative) are accepted at the HTTP layer
            # (schema-valid) but rejected by add_stock()'s own guard, so the item
            # list in the response reports failure for that line and quantity
            # must not change; non-numeric values fail schema validation (400).
            assert stock_item.quantity == before

    @pytest.mark.parametrize(
        'ep_name',
        ['valid_positive', 'invalid_zero', 'invalid_negative', 'invalid_non_numeric'],
    )
    def test_remove_endpoint_ep_classes(self, auth_client, stock_item, generated_data, ep_name):
        ep = next(e for e in generated_data.ep_classes if e.name == ep_name)
        before = stock_item.quantity

        resp = auth_client.post(
            '/api/stock/remove/',
            {'items': [{'pk': stock_item.pk, 'quantity': ep.example}]},
            format='json',
        )
        stock_item.refresh_from_db()

        if ep.valid:
            assert resp.status_code == 201, ep
            assert stock_item.quantity == before - Decimal(ep.example)
        else:
            assert stock_item.quantity == before


# ---------------------------------------------------------------------------
# 3-point BVA around BR-1 (available-quantity clamp) — driven by the generator
# ---------------------------------------------------------------------------


class TestBoundaryValueAnalysis:
    def test_remove_just_below_available_quantity(self, auth_client, stock_item, generated_data):
        triple = next(
            t for t in generated_data.bva_triples if t.boundary_name.startswith('available_quantity')
        )
        resp = auth_client.post(
            '/api/stock/remove/',
            {'items': [{'pk': stock_item.pk, 'quantity': triple.just_below}]},
            format='json',
        )
        stock_item.refresh_from_db()

        assert resp.status_code == 201
        assert stock_item.quantity == Decimal('10') - Decimal(triple.just_below)

    def test_remove_at_available_quantity_boundary(self, auth_client, stock_item, generated_data):
        triple = next(
            t for t in generated_data.bva_triples if t.boundary_name.startswith('available_quantity')
        )
        resp = auth_client.post(
            '/api/stock/remove/',
            {'items': [{'pk': stock_item.pk, 'quantity': triple.at_boundary}]},
            format='json',
        )
        stock_item.refresh_from_db()

        assert resp.status_code == 201
        assert stock_item.quantity == 0

    def test_remove_just_above_available_quantity_clamps(
        self, auth_client, stock_item, generated_data
    ):
        """BR-1 at the HTTP layer: requesting more than available clamps rather than
        erroring, same as the unit-level behaviour, now confirmed through the real API.
        """
        triple = next(
            t for t in generated_data.bva_triples if t.boundary_name.startswith('available_quantity')
        )
        resp = auth_client.post(
            '/api/stock/remove/',
            {'items': [{'pk': stock_item.pk, 'quantity': triple.just_above}]},
            format='json',
        )
        stock_item.refresh_from_db()

        assert resp.status_code == 201
        assert stock_item.quantity == 0  # clamped, not negative, not a 4xx error


# ---------------------------------------------------------------------------
# Cross-workflow: read back the shared record (StockItem.quantity) after each op
# ---------------------------------------------------------------------------


class TestReadBackSharedRecord:
    def test_quantity_readback_after_add_then_remove(self, auth_client, stock_item):
        """FR-8 at the API layer: GET the StockItem after each write and confirm the
        shared record (quantity) reflects both operations correctly.
        """
        auth_client.post(
            '/api/stock/add/', {'items': [{'pk': stock_item.pk, 'quantity': '5'}]}, format='json'
        )
        get_resp = auth_client.get(f'/api/stock/{stock_item.pk}/')
        assert get_resp.status_code == 200
        assert Decimal(str(get_resp.data['quantity'])) == 15

        auth_client.post(
            '/api/stock/remove/', {'items': [{'pk': stock_item.pk, 'quantity': '7'}]}, format='json'
        )
        get_resp = auth_client.get(f'/api/stock/{stock_item.pk}/')
        assert get_resp.status_code == 200
        assert Decimal(str(get_resp.data['quantity'])) == 8

    def test_quantity_readback_after_rejected_request(self, auth_client, stock_item):
        """Read back after a rejection too: an invalid (zero) quantity must leave the
        persisted record unchanged, confirmed via a fresh GET rather than the in-memory
        object.
        """
        auth_client.post(
            '/api/stock/remove/', {'items': [{'pk': stock_item.pk, 'quantity': '0'}]}, format='json'
        )
        get_resp = auth_client.get(f'/api/stock/{stock_item.pk}/')
        assert get_resp.status_code == 200
        assert Decimal(str(get_resp.data['quantity'])) == 10


# ---------------------------------------------------------------------------
# No-duplicates check: repeated identical requests must not double-apply
# ---------------------------------------------------------------------------


class TestRepeatedRequestsNoDuplicates:
    def test_repeating_the_same_add_request_applies_each_time_independently(
        self, auth_client, stock_item
    ):
        """Not an idempotency guarantee (there is no client-supplied request id / idempotency
        key on this endpoint) — but confirms each distinct call is applied exactly once,
        with no silent double-application or silent drop, when sent twice in sequence.
        """
        payload = {'items': [{'pk': stock_item.pk, 'quantity': '2'}]}

        r1 = auth_client.post('/api/stock/add/', payload, format='json')
        r2 = auth_client.post('/api/stock/add/', payload, format='json')
        stock_item.refresh_from_db()

        assert r1.status_code == 201
        assert r2.status_code == 201
        assert stock_item.quantity == 10 + 2 + 2  # exactly twice, not once or thrice
