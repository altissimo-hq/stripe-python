"""Tests for :mod:`altissimo.stripe.client` — StripeClient wrapper."""

from __future__ import annotations

import os
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from altissimo.stripe.client import StripeClient
from altissimo.stripe.exceptions import (
    StripeApiError,
    StripeImportError,
    StripeWebhookError,
)

# ---------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------


def _make_mock_stripe_module() -> ModuleType:
    """Return a fake ``stripe`` module with the shapes the client needs."""
    mod = ModuleType("stripe")

    # stripe.StripeClient — constructor
    mod.StripeClient = MagicMock(name="stripe.StripeClient")  # type: ignore[attr-defined]

    # stripe.Webhook.construct_event
    webhook = MagicMock(name="stripe.Webhook")
    mod.Webhook = webhook  # type: ignore[attr-defined]

    # stripe.error hierarchy
    error_ns = SimpleNamespace(
        StripeError=type("StripeError", (Exception,), {}),
        SignatureVerificationError=type("SignatureVerificationError", (Exception,), {}),
    )
    mod.error = error_ns  # type: ignore[attr-defined]
    return mod


@pytest.fixture
def mock_stripe():
    """Provide a mock stripe module and patch ``_get_stripe``."""
    return _make_mock_stripe_module()


@pytest.fixture
def mock_sdk_client():
    """Provide a mock ``stripe.StripeClient`` *instance*."""
    return MagicMock(name="sdk_client")


@pytest.fixture
def client(mock_stripe, mock_sdk_client):
    """Return a :class:`StripeClient` with ``_get_stripe`` and ``_get_client`` mocked."""
    sc = StripeClient(api_key="sk_test_xxx", webhook_signing_secret="whsec_test")
    with (
        patch.object(StripeClient, "_get_stripe", return_value=mock_stripe),
        patch.object(sc, "_get_client", return_value=mock_sdk_client),
    ):
        # Store the mocks so tests can inspect them.
        sc._mock_stripe = mock_stripe  # type: ignore[attr-defined]
        sc._mock_sdk = mock_sdk_client  # type: ignore[attr-defined]
        yield sc


# ---------------------------------------------------------------
# Factory / env tests
# ---------------------------------------------------------------


class TestFromEnv:
    """Tests for ``StripeClient.from_env``."""

    def test_from_env(self):
        env = {
            "STRIPE_API_KEY": "sk_live_abc",
            "STRIPE_WEBHOOK_SIGNING_SECRET": "whsec_xyz",
        }
        with patch.dict(os.environ, env, clear=False):
            sc = StripeClient.from_env()

        assert sc._api_key == "sk_live_abc"
        assert sc._webhook_signing_secret == "whsec_xyz"

    def test_from_env_missing_key(self):
        with patch.dict(os.environ, {}, clear=True), pytest.raises(ValueError, match="STRIPE_API_KEY"):
            StripeClient.from_env()


# ---------------------------------------------------------------
# Lazy import guard
# ---------------------------------------------------------------


class TestLazyImport:
    """Verify that a missing ``stripe`` package raises ``StripeImportError``."""

    def test_lazy_import_error(self):
        sc = StripeClient(api_key="sk_test_xxx")
        with patch.object(StripeClient, "_get_stripe", side_effect=StripeImportError), pytest.raises(StripeImportError):
            sc.list_customers()


# ---------------------------------------------------------------
# Customer operations
# ---------------------------------------------------------------


class TestCustomers:
    def test_list_customers(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.customers.list.return_value = sentinel

        result = client.list_customers(limit=10, starting_after="cus_abc")

        mock_sdk_client.customers.list.assert_called_once_with(
            params={"limit": 10, "starting_after": "cus_abc"},
        )
        assert result is sentinel

    def test_create_customer(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.customers.create.return_value = sentinel

        result = client.create_customer(email="a@b.com", name="Alice", metadata={"k": "v"})

        mock_sdk_client.customers.create.assert_called_once_with(
            params={"email": "a@b.com", "name": "Alice", "metadata": {"k": "v"}},
        )
        assert result is sentinel

    def test_retrieve_customer(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.customers.retrieve.return_value = sentinel

        result = client.retrieve_customer("cus_123")

        mock_sdk_client.customers.retrieve.assert_called_once_with("cus_123")
        assert result is sentinel


# ---------------------------------------------------------------
# Charge operations
# ---------------------------------------------------------------


class TestCharges:
    def test_list_charges(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.charges.list.return_value = sentinel

        result = client.list_charges()

        mock_sdk_client.charges.list.assert_called_once_with(params={})
        assert result is sentinel


# ---------------------------------------------------------------
# PaymentIntent operations
# ---------------------------------------------------------------


class TestPaymentIntents:
    def test_create_payment_intent(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.payment_intents.create.return_value = sentinel

        result = client.create_payment_intent(5000, "usd", description="Test charge")

        mock_sdk_client.payment_intents.create.assert_called_once_with(
            params={"amount": 5000, "currency": "usd", "description": "Test charge"},
        )
        assert result is sentinel

    def test_create_payment_intent_with_stripe_shipping_and_kwargs(self, client, mock_sdk_client):
        from altissimo.stripe import StripeAddress, StripeShipping

        sentinel = object()
        mock_sdk_client.payment_intents.create.return_value = sentinel

        shipping_info = StripeShipping(
            name="John Doe",
            address=StripeAddress(line1="123 Main St", city="Boston", postal_code="02108", country="US"),
            phone="555-0199",
        )

        result = client.create_payment_intent(
            5000,
            "usd",
            description="Test charge",
            shipping=shipping_info,
            statement_descriptor="DARWINSARK",
        )

        mock_sdk_client.payment_intents.create.assert_called_once_with(
            params={
                "amount": 5000,
                "currency": "usd",
                "description": "Test charge",
                "shipping": {
                    "name": "John Doe",
                    "address": {
                        "line1": "123 Main St",
                        "city": "Boston",
                        "postal_code": "02108",
                        "country": "US",
                    },
                    "phone": "555-0199",
                },
                "statement_descriptor": "DARWINSARK",
            },
        )
        assert result is sentinel

    def test_retrieve_payment_intent(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.payment_intents.retrieve.return_value = sentinel

        result = client.retrieve_payment_intent("pi_abc")

        mock_sdk_client.payment_intents.retrieve.assert_called_once_with("pi_abc")
        assert result is sentinel

    def test_update_payment_intent(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.payment_intents.update.return_value = sentinel

        result = client.update_payment_intent("pi_abc", amount=9999)

        mock_sdk_client.payment_intents.update.assert_called_once_with("pi_abc", params={"amount": 9999})
        assert result is sentinel

    def test_list_payment_intents(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.payment_intents.list.return_value = sentinel

        result = client.list_payment_intents()

        mock_sdk_client.payment_intents.list.assert_called_once_with(params={})
        assert result is sentinel


# ---------------------------------------------------------------
# PaymentLink operations
# ---------------------------------------------------------------


class TestPaymentLinks:
    def test_list_payment_links(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.payment_links.list.return_value = sentinel

        result = client.list_payment_links()

        mock_sdk_client.payment_links.list.assert_called_once_with(params={})
        assert result is sentinel


# ---------------------------------------------------------------
# Product operations
# ---------------------------------------------------------------


class TestProducts:
    def test_list_products(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.products.list.return_value = sentinel

        result = client.list_products()

        mock_sdk_client.products.list.assert_called_once_with(params={})
        assert result is sentinel


# ---------------------------------------------------------------
# Price operations
# ---------------------------------------------------------------


class TestPrices:
    def test_list_prices(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.prices.list.return_value = sentinel

        result = client.list_prices(product="prod_abc", active=True)

        mock_sdk_client.prices.list.assert_called_once_with(
            params={"product": "prod_abc", "active": True},
        )
        assert result is sentinel

    def test_retrieve_price(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.prices.retrieve.return_value = sentinel

        result = client.retrieve_price("price_xyz")

        mock_sdk_client.prices.retrieve.assert_called_once_with("price_xyz")
        assert result is sentinel


# ---------------------------------------------------------------
# Coupon operations
# ---------------------------------------------------------------


class TestCoupons:
    def test_list_coupons(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.coupons.list.return_value = sentinel

        result = client.list_coupons()

        mock_sdk_client.coupons.list.assert_called_once_with(params={})
        assert result is sentinel


# ---------------------------------------------------------------
# Refund operations
# ---------------------------------------------------------------


class TestRefunds:
    def test_list_refunds(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.refunds.list.return_value = sentinel

        result = client.list_refunds()

        mock_sdk_client.refunds.list.assert_called_once_with(params={})
        assert result is sentinel


# ---------------------------------------------------------------
# Promotion Code operations
# ---------------------------------------------------------------


class TestPromotionCodes:
    def test_retrieve_promotion_code(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.promotion_codes.retrieve.return_value = sentinel

        result = client.retrieve_promotion_code("promo_abc")

        mock_sdk_client.promotion_codes.retrieve.assert_called_once_with("promo_abc")
        assert result is sentinel

    def test_list_promotion_codes(self, client, mock_sdk_client):
        sentinel = object()
        mock_sdk_client.promotion_codes.list.return_value = sentinel

        result = client.list_promotion_codes(code="SAVE20", active=True)

        mock_sdk_client.promotion_codes.list.assert_called_once_with(
            params={"code": "SAVE20", "active": True},
        )
        assert result is sentinel


# ---------------------------------------------------------------
# Webhook event construction
# ---------------------------------------------------------------


class TestWebhookEvent:
    def test_construct_webhook_event(self, mock_stripe):
        """Happy path — signature is valid."""
        sc = StripeClient(api_key="sk_test_xxx", webhook_signing_secret="whsec_test")
        expected_event = {"type": "checkout.session.completed"}
        mock_stripe.Webhook.construct_event.return_value = expected_event

        with patch.object(StripeClient, "_get_stripe", return_value=mock_stripe):
            result = sc.construct_webhook_event(b"body", "sig_header")

        mock_stripe.Webhook.construct_event.assert_called_once_with(b"body", "sig_header", "whsec_test")
        assert result == expected_event

    def test_construct_webhook_event_no_secret(self):
        """Raises ``ValueError`` when no signing secret is configured."""
        sc = StripeClient(api_key="sk_test_xxx")
        with pytest.raises(ValueError, match="webhook_signing_secret"):
            sc.construct_webhook_event(b"body", "sig_header")

    def test_construct_webhook_event_invalid_sig(self, mock_stripe):
        """SDK ``SignatureVerificationError`` is wrapped as ``StripeWebhookError``."""
        sc = StripeClient(api_key="sk_test_xxx", webhook_signing_secret="whsec_test")
        mock_stripe.Webhook.construct_event.side_effect = mock_stripe.error.SignatureVerificationError("bad sig")

        with (
            patch.object(StripeClient, "_get_stripe", return_value=mock_stripe),
            pytest.raises(StripeWebhookError, match="signature verification"),
        ):
            sc.construct_webhook_event(b"body", "sig_header")


# ---------------------------------------------------------------
# API error wrapping
# ---------------------------------------------------------------


class TestApiErrorWrapping:
    def test_api_error_wrapping(self, mock_stripe, mock_sdk_client):
        """SDK ``StripeError`` is wrapped as ``StripeApiError``."""
        sc = StripeClient(api_key="sk_test_xxx")

        sdk_error = mock_stripe.error.StripeError("boom")
        sdk_error.http_status = 402
        sdk_error.code = "card_declined"
        mock_sdk_client.customers.list.side_effect = sdk_error

        with (
            patch.object(StripeClient, "_get_stripe", return_value=mock_stripe),
            patch.object(sc, "_get_client", return_value=mock_sdk_client),
            pytest.raises(StripeApiError) as exc_info,
        ):
            sc.list_customers()

        err = exc_info.value
        assert err.status_code == 402
        assert err.code == "card_declined"
        assert err.original is sdk_error
