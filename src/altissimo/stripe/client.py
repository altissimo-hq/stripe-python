"""Altissimo Stripe — instance-based client wrapper.

Provides a typed, instance-based wrapper around the Stripe SDK with
lazy initialization and consistent error handling.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from altissimo.stripe.exceptions import (
    StripeApiError,
    StripeImportError,
    StripeWebhookError,
)
from altissimo.stripe.models import StripeShipping
from altissimo.stripe.pagination import paginate

if TYPE_CHECKING:
    from collections.abc import Iterator

logger = logging.getLogger(__name__)


class StripeClient:
    """Instance-based, typed wrapper around the Stripe SDK.

    The underlying ``stripe`` package is imported lazily — this class
    can be *instantiated* without ``stripe`` being installed, but any
    API call will raise :class:`StripeImportError` if it is missing.

    Args:
        api_key: Stripe secret API key.
        webhook_signing_secret: Webhook endpoint signing secret (optional).
    """

    def __init__(
        self,
        api_key: str,
        *,
        webhook_signing_secret: str | None = None,
    ) -> None:
        self._api_key = api_key
        self._webhook_signing_secret = webhook_signing_secret
        self._stripe_client: Any | None = None

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_env(
        cls,
        *,
        api_key_var: str = "STRIPE_API_KEY",
        webhook_secret_var: str = "STRIPE_WEBHOOK_SIGNING_SECRET",
    ) -> StripeClient:
        """Create a :class:`StripeClient` from environment variables.

        Args:
            api_key_var: Name of the env var holding the API key.
            webhook_secret_var: Name of the env var holding the webhook secret.

        Raises:
            ValueError: If the API key env var is not set.
        """
        api_key = os.environ.get(api_key_var)
        if not api_key:
            msg = f"Environment variable {api_key_var!r} is not set or empty"
            raise ValueError(msg)
        return cls(
            api_key=api_key,
            webhook_signing_secret=os.environ.get(webhook_secret_var),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _get_stripe() -> Any:
        """Lazily import and return the ``stripe`` module.

        Raises:
            StripeImportError: If the ``stripe`` package is not installed.
        """
        try:
            import stripe
        except ImportError:
            raise StripeImportError from None
        return stripe

    def _get_client(self) -> Any:
        """Return a cached ``stripe.StripeClient`` instance."""
        if self._stripe_client is None:
            stripe = self._get_stripe()
            self._stripe_client = stripe.StripeClient(api_key=self._api_key)
        return self._stripe_client

    @contextmanager
    def _api_call(self) -> Iterator[Any]:
        """Context manager that wraps Stripe API errors.

        Catches the SDK's ``stripe.error.StripeError`` and re-raises as
        :class:`StripeApiError`.
        """
        stripe = self._get_stripe()
        try:
            yield self._get_client()
        except stripe.error.StripeError as exc:
            raise StripeApiError(
                str(exc),
                status_code=getattr(exc, "http_status", None),
                code=getattr(exc, "code", None),
                original=exc,
            ) from exc

    # ------------------------------------------------------------------
    # Customer operations
    # ------------------------------------------------------------------

    def list_customers(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> Any:
        """Return a paginated list of customers.

        Args:
            limit: Max number of customers to return.
            starting_after: Cursor for pagination.
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = starting_after
        with self._api_call() as client:
            return client.customers.list(params=params)

    def create_customer(
        self,
        *,
        email: str | None = None,
        name: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> Any:
        """Create a Stripe customer.

        Args:
            email: Customer email address.
            name: Customer full name.
            metadata: Arbitrary key-value metadata.
        """
        params: dict[str, Any] = {}
        if email is not None:
            params["email"] = email
        if name is not None:
            params["name"] = name
        if metadata is not None:
            params["metadata"] = metadata
        with self._api_call() as client:
            return client.customers.create(params=params)

    def retrieve_customer(self, customer_id: str) -> Any:
        """Retrieve a customer by ID.

        Args:
            customer_id: The Stripe customer ID.
        """
        with self._api_call() as client:
            return client.customers.retrieve(customer_id)

    def iter_customers(self, *, limit: int = 100) -> Iterator[Any]:
        """Iterate over all customers using automatic pagination.

        Args:
            limit: Page size (max 100).
        """
        return paginate(lambda **kw: self.list_customers(**kw), limit=limit)

    # ------------------------------------------------------------------
    # Charge operations
    # ------------------------------------------------------------------

    def list_charges(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> Any:
        """Return a paginated list of charges.

        Args:
            limit: Max number of charges to return.
            starting_after: Cursor for pagination.
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = starting_after
        with self._api_call() as client:
            return client.charges.list(params=params)

    def iter_charges(self, *, limit: int = 100) -> Iterator[Any]:
        """Iterate over all charges using automatic pagination.

        Args:
            limit: Page size (max 100).
        """
        return paginate(lambda **kw: self.list_charges(**kw), limit=limit)

    # ------------------------------------------------------------------
    # PaymentIntent operations
    # ------------------------------------------------------------------

    def create_payment_intent(
        self,
        amount: int,
        currency: str,
        *,
        automatic_payment_methods: dict[str, Any] | None = None,
        description: str | None = None,
        shipping: StripeShipping | dict[str, Any] | None = None,
        metadata: dict[str, str] | None = None,
        receipt_email: str | None = None,
        **kwargs: Any,
    ) -> Any:
        """Create a PaymentIntent.

        Args:
            amount: Amount in the smallest currency unit (e.g. cents).
            currency: Three-letter ISO currency code.
            automatic_payment_methods: Automatic payment methods config.
            description: Description of the payment.
            shipping: Shipping information.
            metadata: Arbitrary key-value metadata.
            receipt_email: Email to send the receipt to.
            **kwargs: Extra parameters to pass directly to Stripe's PaymentIntent create endpoint.
        """
        params: dict[str, Any] = {"amount": amount, "currency": currency}
        if automatic_payment_methods is not None:
            params["automatic_payment_methods"] = automatic_payment_methods
        if description is not None:
            params["description"] = description
        if shipping is not None:
            if isinstance(shipping, StripeShipping):
                params["shipping"] = shipping.model_dump(exclude_none=True)
            else:
                params["shipping"] = shipping
        if metadata is not None:
            params["metadata"] = metadata
        if receipt_email is not None:
            params["receipt_email"] = receipt_email
        params.update(kwargs)
        with self._api_call() as client:
            return client.payment_intents.create(params=params)

    def retrieve_payment_intent(self, payment_intent_id: str) -> Any:
        """Retrieve a PaymentIntent by ID.

        Args:
            payment_intent_id: The Stripe PaymentIntent ID.
        """
        with self._api_call() as client:
            return client.payment_intents.retrieve(payment_intent_id)

    def update_payment_intent(
        self,
        payment_intent_id: str,
        **kwargs: Any,
    ) -> Any:
        """Update a PaymentIntent.

        Args:
            payment_intent_id: The Stripe PaymentIntent ID.
            **kwargs: Fields to update (e.g. ``amount``, ``metadata``).
        """
        with self._api_call() as client:
            return client.payment_intents.update(payment_intent_id, params=kwargs)

    def list_payment_intents(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> Any:
        """Return a paginated list of PaymentIntents.

        Args:
            limit: Max number of PaymentIntents to return.
            starting_after: Cursor for pagination.
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = starting_after
        with self._api_call() as client:
            return client.payment_intents.list(params=params)

    def iter_payment_intents(self, *, limit: int = 100) -> Iterator[Any]:
        """Iterate over all PaymentIntents using automatic pagination.

        Args:
            limit: Page size (max 100).
        """
        return paginate(lambda **kw: self.list_payment_intents(**kw), limit=limit)

    # ------------------------------------------------------------------
    # PaymentLink operations
    # ------------------------------------------------------------------

    def list_payment_links(self, *, limit: int | None = None) -> Any:
        """Return a list of payment links.

        Args:
            limit: Max number of payment links to return.
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        with self._api_call() as client:
            return client.payment_links.list(params=params)

    def iter_payment_links(self, *, limit: int = 100) -> Iterator[Any]:
        """Iterate over all payment links using automatic pagination.

        Args:
            limit: Page size (max 100).
        """
        return paginate(lambda **kw: self.list_payment_links(**kw), limit=limit)

    # ------------------------------------------------------------------
    # Product operations
    # ------------------------------------------------------------------

    def list_products(self, *, limit: int | None = None) -> Any:
        """Return a list of products.

        Args:
            limit: Max number of products to return.
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        with self._api_call() as client:
            return client.products.list(params=params)

    def iter_products(self, *, limit: int = 100) -> Iterator[Any]:
        """Iterate over all products using automatic pagination.

        Args:
            limit: Page size (max 100).
        """
        return paginate(lambda **kw: self.list_products(**kw), limit=limit)

    # ------------------------------------------------------------------
    # Price operations
    # ------------------------------------------------------------------

    def list_prices(
        self,
        *,
        product: str | None = None,
        active: bool | None = None,
    ) -> Any:
        """Return a list of prices, optionally filtered.

        Args:
            product: Filter by product ID.
            active: Filter by active status.
        """
        params: dict[str, Any] = {}
        if product is not None:
            params["product"] = product
        if active is not None:
            params["active"] = active
        with self._api_call() as client:
            return client.prices.list(params=params)

    def retrieve_price(self, price_id: str) -> Any:
        """Retrieve a price by ID.

        Args:
            price_id: The Stripe price ID.
        """
        with self._api_call() as client:
            return client.prices.retrieve(price_id)

    def iter_prices(
        self,
        *,
        product: str | None = None,
        active: bool | None = None,
        limit: int = 100,
    ) -> Iterator[Any]:
        """Iterate over all prices using automatic pagination.

        Args:
            product: Filter by product ID.
            active: Filter by active status.
            limit: Page size (max 100).
        """
        kwargs: dict[str, Any] = {}
        if product is not None:
            kwargs["product"] = product
        if active is not None:
            kwargs["active"] = active
        return paginate(lambda **kw: self.list_prices(**{**kwargs, **kw}), limit=limit)

    # ------------------------------------------------------------------
    # Coupon operations
    # ------------------------------------------------------------------

    def list_coupons(self, *, limit: int | None = None) -> Any:
        """Return a list of coupons.

        Args:
            limit: Max number of coupons to return.
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        with self._api_call() as client:
            return client.coupons.list(params=params)

    def iter_coupons(self, *, limit: int = 100) -> Iterator[Any]:
        """Iterate over all coupons using automatic pagination.

        Args:
            limit: Page size (max 100).
        """
        return paginate(lambda **kw: self.list_coupons(**kw), limit=limit)

    # ------------------------------------------------------------------
    # Refund operations
    # ------------------------------------------------------------------

    def list_refunds(
        self,
        *,
        limit: int | None = None,
        starting_after: str | None = None,
    ) -> Any:
        """Return a paginated list of refunds.

        Args:
            limit: Max number of refunds to return.
            starting_after: Cursor for pagination.
        """
        params: dict[str, Any] = {}
        if limit is not None:
            params["limit"] = limit
        if starting_after is not None:
            params["starting_after"] = starting_after
        with self._api_call() as client:
            return client.refunds.list(params=params)

    def iter_refunds(self, *, limit: int = 100) -> Iterator[Any]:
        """Iterate over all refunds using automatic pagination.

        Args:
            limit: Page size (max 100).
        """
        return paginate(lambda **kw: self.list_refunds(**kw), limit=limit)

    # ------------------------------------------------------------------
    # Promotion Code operations
    # ------------------------------------------------------------------

    def retrieve_promotion_code(self, promo_code_id: str) -> Any:
        """Retrieve a promotion code by ID.

        Args:
            promo_code_id: The Stripe promotion code ID.
        """
        with self._api_call() as client:
            return client.promotion_codes.retrieve(promo_code_id)

    def list_promotion_codes(
        self,
        *,
        code: str | None = None,
        active: bool | None = None,
    ) -> Any:
        """Return a list of promotion codes, optionally filtered.

        Args:
            code: Filter by the user-facing coupon code.
            active: Filter by active status.
        """
        params: dict[str, Any] = {}
        if code is not None:
            params["code"] = code
        if active is not None:
            params["active"] = active
        with self._api_call() as client:
            return client.promotion_codes.list(params=params)

    def iter_promotion_codes(
        self,
        *,
        code: str | None = None,
        active: bool | None = None,
        limit: int = 100,
    ) -> Iterator[Any]:
        """Iterate over all promotion codes using automatic pagination.

        Args:
            code: Filter by the user-facing coupon code.
            active: Filter by active status.
            limit: Page size (max 100).
        """
        kwargs: dict[str, Any] = {}
        if code is not None:
            kwargs["code"] = code
        if active is not None:
            kwargs["active"] = active
        return paginate(lambda **kw: self.list_promotion_codes(**{**kwargs, **kw}), limit=limit)

    # ------------------------------------------------------------------
    # Webhook event construction
    # ------------------------------------------------------------------

    def construct_webhook_event(
        self,
        payload: bytes | str,
        sig_header: str,
    ) -> Any:
        """Verify a webhook signature and parse the event.

        Args:
            payload: Raw request body.
            sig_header: Value of the ``Stripe-Signature`` header.

        Raises:
            StripeWebhookError: If the signature is invalid or the
                payload cannot be parsed.
            ValueError: If no webhook signing secret was configured.
        """
        if not self._webhook_signing_secret:
            msg = "No webhook_signing_secret configured on this StripeClient"
            raise ValueError(msg)

        stripe = self._get_stripe()
        try:
            return stripe.Webhook.construct_event(
                payload,
                sig_header,
                self._webhook_signing_secret,
            )
        except stripe.error.SignatureVerificationError as exc:
            raise StripeWebhookError(
                f"Webhook signature verification failed: {exc}",
                original=exc,
            ) from exc
        except ValueError as exc:
            raise StripeWebhookError(
                f"Invalid webhook payload: {exc}",
                original=exc,
            ) from exc
