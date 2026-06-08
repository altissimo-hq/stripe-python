"""Tests for altissimo.stripe.models."""

from dataclasses import FrozenInstanceError

import pytest

from altissimo.stripe.models import (
    PaymentIntentStatus,
    StripeAddress,
    StripeShipping,
    WebhookResult,
)


class TestPaymentIntentStatus:
    def test_is_str_enum(self) -> None:
        assert isinstance(PaymentIntentStatus.SUCCEEDED, str)

    def test_all_values(self) -> None:
        expected = {
            "requires_payment_method",
            "requires_confirmation",
            "requires_action",
            "processing",
            "requires_capture",
            "canceled",
            "succeeded",
        }
        assert {s.value for s in PaymentIntentStatus} == expected

    def test_string_comparison(self) -> None:
        assert PaymentIntentStatus.SUCCEEDED == "succeeded"
        assert PaymentIntentStatus.CANCELED == "canceled"

    def test_lookup_by_value(self) -> None:
        assert PaymentIntentStatus("processing") is PaymentIntentStatus.PROCESSING


class TestStripeAddress:
    def test_all_optional(self) -> None:
        addr = StripeAddress()
        assert addr.line1 is None
        assert addr.country is None

    def test_with_values(self) -> None:
        addr = StripeAddress(
            line1="123 Main St",
            city="Springfield",
            state="IL",
            postal_code="62704",
            country="US",
        )
        assert addr.line1 == "123 Main St"
        assert addr.country == "US"

    def test_serialization(self) -> None:
        addr = StripeAddress(line1="123 Main St", country="US")
        data = addr.model_dump()
        assert data["line1"] == "123 Main St"
        assert data["country"] == "US"
        assert data["line2"] is None

    def test_from_dict(self) -> None:
        data = {"line1": "456 Elm", "city": "Portland", "state": "OR"}
        addr = StripeAddress.model_validate(data)
        assert addr.line1 == "456 Elm"
        assert addr.city == "Portland"


class TestStripeShipping:
    def test_requires_name_and_address(self) -> None:
        addr = StripeAddress(line1="123 Main St")
        shipping = StripeShipping(name="Jane Doe", address=addr)
        assert shipping.name == "Jane Doe"
        assert shipping.address.line1 == "123 Main St"

    def test_missing_name_does_not_raise(self) -> None:
        shipping = StripeShipping(address=StripeAddress())
        assert shipping.name is None

    def test_phone_field(self) -> None:
        addr = StripeAddress(line1="123 Main St")
        shipping = StripeShipping(name="Jane Doe", address=addr, phone="555-0199")
        assert shipping.phone == "555-0199"

    def test_nested_serialization(self) -> None:
        shipping = StripeShipping(
            name="Jane",
            address=StripeAddress(line1="123 Main", country="US"),
        )
        data = shipping.model_dump()
        assert data["name"] == "Jane"
        assert data["address"]["line1"] == "123 Main"


class TestWebhookResult:
    def test_required_fields(self) -> None:
        result = WebhookResult(status="ok", event_type="payment_intent.succeeded")
        assert result.status == "ok"
        assert result.event_type == "payment_intent.succeeded"
        assert result.event_id is None
        assert result.error is None

    def test_all_fields(self) -> None:
        result = WebhookResult(
            status="error",
            event_type="charge.failed",
            event_id="evt_123",
            error="something broke",
        )
        assert result.event_id == "evt_123"
        assert result.error == "something broke"

    def test_frozen(self) -> None:
        result = WebhookResult(status="ok", event_type="test")
        with pytest.raises(FrozenInstanceError):
            result.status = "error"  # type: ignore[misc]

    def test_slots(self) -> None:
        assert hasattr(WebhookResult, "__slots__")
