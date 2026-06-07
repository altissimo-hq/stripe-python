"""Tests for altissimo.stripe.testing helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from altissimo.stripe.exceptions import StripeWebhookError
from altissimo.stripe.pagination import paginate
from altissimo.stripe.testing import FakePage, FakeStripeClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class _Item:
    """Minimal object with an ``.id`` attribute."""

    id: str


# ---------------------------------------------------------------------------
# FakeStripeClient — call recording
# ---------------------------------------------------------------------------


class TestFakeStripeClientRecordsCalls:
    """FakeStripeClient records method name, args, and kwargs for each call."""

    def test_records_list_customers(self) -> None:
        fake = FakeStripeClient()
        fake.list_customers(limit=10)

        assert len(fake.calls) == 1
        assert fake.calls[0].method == "list_customers"
        assert fake.calls[0].kwargs == {"limit": 10}

    def test_records_create_customer(self) -> None:
        fake = FakeStripeClient()
        fake.create_customer(email="test@example.com")

        assert fake.calls[0].method == "create_customer"
        assert fake.calls[0].kwargs == {"email": "test@example.com"}

    def test_records_retrieve_customer(self) -> None:
        fake = FakeStripeClient()
        fake.retrieve_customer("cus_123")

        assert fake.calls[0].method == "retrieve_customer"
        assert fake.calls[0].args == ("cus_123",)

    def test_records_multiple_calls(self) -> None:
        fake = FakeStripeClient()
        fake.list_customers(limit=5)
        fake.list_charges(customer="cus_1")

        assert len(fake.calls) == 2
        assert fake.calls[0].method == "list_customers"
        assert fake.calls[1].method == "list_charges"


# ---------------------------------------------------------------------------
# FakeStripeClient — pre-configured responses
# ---------------------------------------------------------------------------


class TestFakeStripeClientResponses:
    """FakeStripeClient returns pre-configured responses."""

    def test_returns_configured_response(self) -> None:
        page = FakePage([_Item(id="cus_1"), _Item(id="cus_2")])
        fake = FakeStripeClient(list_customers_response=page)

        result = fake.list_customers(limit=10)

        assert result is page
        assert result.data == [_Item(id="cus_1"), _Item(id="cus_2")]

    def test_returns_configured_scalar_response(self) -> None:
        customer = _Item(id="cus_42")
        fake = FakeStripeClient(retrieve_customer_response=customer)

        result = fake.retrieve_customer("cus_42")

        assert result is customer


class TestFakeStripeClientDefaultResponse:
    """FakeStripeClient returns FakePage([]) when no response is configured."""

    def test_default_is_empty_fake_page(self) -> None:
        fake = FakeStripeClient()

        result = fake.list_customers()

        assert isinstance(result, FakePage)
        assert result.data == []
        assert result.has_more is False


# ---------------------------------------------------------------------------
# FakePage attributes
# ---------------------------------------------------------------------------


class TestFakePage:
    """FakePage has .data and .has_more attributes."""

    def test_data_attribute(self) -> None:
        items = [_Item(id="a"), _Item(id="b")]
        page = FakePage(items)

        assert page.data == items

    def test_has_more_default_false(self) -> None:
        page = FakePage([])

        assert page.has_more is False

    def test_has_more_true(self) -> None:
        page = FakePage([_Item(id="x")], has_more=True)

        assert page.has_more is True


# ---------------------------------------------------------------------------
# FakeStripeClient — construct_webhook_event raises on Exception
# ---------------------------------------------------------------------------


class TestFakeStripeClientWebhookRaises:
    """construct_webhook_event raises if the configured response is an Exception."""

    def test_raises_configured_exception(self) -> None:
        error = StripeWebhookError("bad sig")
        fake = FakeStripeClient(construct_webhook_event_response=error)

        with pytest.raises(StripeWebhookError, match="bad sig"):
            fake.construct_webhook_event(b"payload", "sig_header")

    def test_raises_when_no_response_configured(self) -> None:
        fake = FakeStripeClient()

        with pytest.raises(StripeWebhookError, match="No fake webhook event configured"):
            fake.construct_webhook_event(b"payload", "sig_header")


# ---------------------------------------------------------------------------
# FakeStripeClient + paginate() integration
# ---------------------------------------------------------------------------


class TestFakeStripeClientWithPaginate:
    """FakeStripeClient works with paginate() via FakePage."""

    def test_paginate_single_page(self) -> None:
        items = [_Item(id="c1"), _Item(id="c2")]
        fake = FakeStripeClient(list_customers_response=FakePage(items))

        result = list(paginate(fake.list_customers))

        assert result == items

    def test_paginate_records_calls(self) -> None:
        fake = FakeStripeClient(list_customers_response=FakePage([]))

        list(paginate(fake.list_customers, limit=25))

        assert len(fake.calls) == 1
        assert fake.calls[0].method == "list_customers"
        assert fake.calls[0].kwargs["limit"] == 25


# ---------------------------------------------------------------------------
# iter_* methods yield from response data
# ---------------------------------------------------------------------------


class TestIterMethods:
    """iter_* methods yield individual items from the configured response."""

    def test_iter_customers(self) -> None:
        items = [_Item(id="c1"), _Item(id="c2")]
        fake = FakeStripeClient(list_customers_response=FakePage(items))

        result = list(fake.iter_customers())

        assert result == items

    def test_iter_charges(self) -> None:
        items = [_Item(id="ch_1")]
        fake = FakeStripeClient(list_charges_response=FakePage(items))

        result = list(fake.iter_charges())

        assert result == items

    def test_iter_payment_intents(self) -> None:
        items = [_Item(id="pi_1"), _Item(id="pi_2")]
        fake = FakeStripeClient(list_payment_intents_response=FakePage(items))

        result = list(fake.iter_payment_intents())

        assert result == items

    def test_iter_products(self) -> None:
        items = [_Item(id="prod_1")]
        fake = FakeStripeClient(list_products_response=FakePage(items))

        result = list(fake.iter_products())

        assert result == items

    def test_iter_prices(self) -> None:
        items = [_Item(id="price_1")]
        fake = FakeStripeClient(list_prices_response=FakePage(items))

        result = list(fake.iter_prices())

        assert result == items

    def test_iter_with_no_response_yields_nothing(self) -> None:
        fake = FakeStripeClient()

        # When no response is configured, iter_ methods yield nothing
        result = list(fake.iter_customers())

        assert result == []
