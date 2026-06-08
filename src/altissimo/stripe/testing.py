"""Altissimo Stripe — reusable test helpers.

Provides in-memory fakes for :class:`StripeClient` and paginated Stripe
responses so downstream projects don't need to write their own.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from altissimo.stripe.exceptions import StripeWebhookError

if TYPE_CHECKING:
    from collections.abc import Iterator


@dataclass
class _CallRecord:
    """Record of a single method invocation on :class:`FakeStripeClient`."""

    method: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]


class FakePage:
    """Simulates a paginated Stripe list response.

    This object has ``.data`` and ``.has_more`` attributes matching the
    shape returned by the Stripe SDK's list methods, making it compatible
    with :func:`altissimo.stripe.pagination.paginate`.

    Args:
        data: The list of items in this page.
        has_more: Whether more pages exist after this one.
    """

    def __init__(self, data: list[Any], *, has_more: bool = False) -> None:
        self.data = data
        self.has_more = has_more


@dataclass
class FakeStripeClient:
    """In-memory fake for :class:`StripeClient`.

    Records all method calls for assertion in tests and returns
    pre-configured responses.

    Example::

        fake = FakeStripeClient(
            list_customers_response=FakePage([customer_1, customer_2]),
        )
        result = fake.list_customers(limit=10)
        assert result.data == [customer_1, customer_2]
        assert fake.calls[0].method == "list_customers"

    Attributes:
        calls: List of :class:`_CallRecord` instances for all calls made.
    """

    # Pre-configured responses for each method
    list_customers_response: Any = None
    create_customer_response: Any = None
    retrieve_customer_response: Any = None
    list_charges_response: Any = None
    create_payment_intent_response: Any = None
    retrieve_payment_intent_response: Any = None
    update_payment_intent_response: Any = None
    list_payment_intents_response: Any = None
    list_payment_links_response: Any = None
    list_products_response: Any = None
    list_prices_response: Any = None
    retrieve_price_response: Any = None
    list_coupons_response: Any = None
    list_refunds_response: Any = None
    retrieve_promotion_code_response: Any = None
    list_promotion_codes_response: Any = None
    construct_webhook_event_response: Any = None

    # Call recording
    calls: list[_CallRecord] = field(default_factory=list)

    def _record(self, method: str, *args: Any, **kwargs: Any) -> Any:
        """Record a call and return the pre-configured response."""
        self.calls.append(_CallRecord(method=method, args=args, kwargs=kwargs))
        response = getattr(self, f"{method}_response", None)
        if response is None:
            return FakePage([])
        return response

    # ------------------------------------------------------------------
    # Customer operations
    # ------------------------------------------------------------------

    def list_customers(self, **kwargs: Any) -> Any:
        return self._record("list_customers", **kwargs)

    def create_customer(self, **kwargs: Any) -> Any:
        return self._record("create_customer", **kwargs)

    def retrieve_customer(self, customer_id: str) -> Any:
        return self._record("retrieve_customer", customer_id)

    def iter_customers(self, **kwargs: Any) -> Iterator[Any]:
        self._record("iter_customers", **kwargs)
        resp = self.list_customers_response
        if resp is not None:
            yield from resp.data
        return

    # ------------------------------------------------------------------
    # Charge operations
    # ------------------------------------------------------------------

    def list_charges(self, **kwargs: Any) -> Any:
        return self._record("list_charges", **kwargs)

    def iter_charges(self, **kwargs: Any) -> Iterator[Any]:
        self._record("iter_charges", **kwargs)
        resp = self.list_charges_response
        if resp is not None:
            yield from resp.data
        return

    # ------------------------------------------------------------------
    # PaymentIntent operations
    # ------------------------------------------------------------------

    def create_payment_intent(self, amount: int, currency: str, **kwargs: Any) -> Any:
        return self._record("create_payment_intent", amount, currency, **kwargs)

    def retrieve_payment_intent(self, payment_intent_id: str) -> Any:
        return self._record("retrieve_payment_intent", payment_intent_id)

    def update_payment_intent(self, payment_intent_id: str, **kwargs: Any) -> Any:
        return self._record("update_payment_intent", payment_intent_id, **kwargs)

    def list_payment_intents(self, **kwargs: Any) -> Any:
        return self._record("list_payment_intents", **kwargs)

    def iter_payment_intents(self, **kwargs: Any) -> Iterator[Any]:
        self._record("iter_payment_intents", **kwargs)
        resp = self.list_payment_intents_response
        if resp is not None:
            yield from resp.data
        return

    # ------------------------------------------------------------------
    # PaymentLink operations
    # ------------------------------------------------------------------

    def list_payment_links(self, **kwargs: Any) -> Any:
        return self._record("list_payment_links", **kwargs)

    def iter_payment_links(self, **kwargs: Any) -> Iterator[Any]:
        self._record("iter_payment_links", **kwargs)
        resp = self.list_payment_links_response
        if resp is not None:
            yield from resp.data
        return

    # ------------------------------------------------------------------
    # Product operations
    # ------------------------------------------------------------------

    def list_products(self, **kwargs: Any) -> Any:
        return self._record("list_products", **kwargs)

    def iter_products(self, **kwargs: Any) -> Iterator[Any]:
        self._record("iter_products", **kwargs)
        resp = self.list_products_response
        if resp is not None:
            yield from resp.data
        return

    # ------------------------------------------------------------------
    # Price operations
    # ------------------------------------------------------------------

    def list_prices(self, **kwargs: Any) -> Any:
        return self._record("list_prices", **kwargs)

    def retrieve_price(self, price_id: str) -> Any:
        return self._record("retrieve_price", price_id)

    def iter_prices(self, **kwargs: Any) -> Iterator[Any]:
        self._record("iter_prices", **kwargs)
        resp = self.list_prices_response
        if resp is not None:
            yield from resp.data
        return

    # ------------------------------------------------------------------
    # Coupon operations
    # ------------------------------------------------------------------

    def list_coupons(self, **kwargs: Any) -> Any:
        return self._record("list_coupons", **kwargs)

    def iter_coupons(self, **kwargs: Any) -> Iterator[Any]:
        self._record("iter_coupons", **kwargs)
        resp = self.list_coupons_response
        if resp is not None:
            yield from resp.data
        return

    # ------------------------------------------------------------------
    # Refund operations
    # ------------------------------------------------------------------

    def list_refunds(self, **kwargs: Any) -> Any:
        return self._record("list_refunds", **kwargs)

    def iter_refunds(self, **kwargs: Any) -> Iterator[Any]:
        self._record("iter_refunds", **kwargs)
        resp = self.list_refunds_response
        if resp is not None:
            yield from resp.data
        return

    # ------------------------------------------------------------------
    # Promotion Code operations
    # ------------------------------------------------------------------

    def retrieve_promotion_code(self, promo_code_id: str) -> Any:
        return self._record("retrieve_promotion_code", promo_code_id)

    def list_promotion_codes(self, **kwargs: Any) -> Any:
        return self._record("list_promotion_codes", **kwargs)

    def iter_promotion_codes(self, **kwargs: Any) -> Iterator[Any]:
        self._record("iter_promotion_codes", **kwargs)
        resp = self.list_promotion_codes_response
        if resp is not None:
            yield from resp.data
        return

    # ------------------------------------------------------------------
    # Webhook
    # ------------------------------------------------------------------

    def construct_webhook_event(
        self,
        payload: bytes | str,
        sig_header: str,
    ) -> Any:
        """Return the pre-configured webhook event or raise.

        If ``construct_webhook_event_response`` is an :class:`Exception`,
        it will be raised instead of returned.
        """
        self._record("construct_webhook_event", payload, sig_header)
        resp = self.construct_webhook_event_response
        if isinstance(resp, Exception):
            raise resp
        if resp is None:
            raise StripeWebhookError("No fake webhook event configured")
        return resp
