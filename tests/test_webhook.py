"""Tests for altissimo.stripe.webhook.StripeWebhookHandler."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import pytest

from altissimo.stripe.exceptions import StripeWebhookError
from altissimo.stripe.models import WebhookResult
from altissimo.stripe.webhook import StripeWebhookHandler

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@dataclass
class _FakeEvent:
    """Minimal event object with ``.type`` and ``.id``."""

    type: str
    id: str


class _FakeClient:
    """Minimal client with a construct_webhook_event method."""

    def __init__(self, event: Any = None, *, error: Exception | None = None) -> None:
        self._event = event
        self._error = error

    def construct_webhook_event(
        self, payload: bytes | str, sig_header: str
    ) -> Any:
        if self._error is not None:
            raise self._error
        return self._event


# Common fixtures
_PAYLOAD = b'{"type": "test"}'
_SIG = "t=123,v1=abc"


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDecoratorRegistration:
    """@handler.on('event_type') registers the handler function."""

    def test_decorator_registration(self) -> None:
        event = _FakeEvent(type="invoice.paid", id="evt_1")
        client = _FakeClient(event=event)
        handler = StripeWebhookHandler(client)

        @handler.on("invoice.paid")
        def on_invoice_paid(evt: Any) -> None:
            pass

        assert handler._handlers["invoice.paid"] is on_invoice_paid

    def test_decorator_returns_original_function(self) -> None:
        client = _FakeClient()
        handler = StripeWebhookHandler(client)

        @handler.on("some.event")
        def my_func(evt: Any) -> None:
            pass

        assert my_func.__name__ == "my_func"


class TestProgrammaticRegistration:
    """handler.register('event_type', fn) registers the handler."""

    def test_programmatic_registration(self) -> None:
        client = _FakeClient()
        handler = StripeWebhookHandler(client)

        def my_handler(evt: Any) -> None:
            pass

        handler.register("checkout.session.completed", my_handler)

        assert handler._handlers["checkout.session.completed"] is my_handler


class TestHandleSyncHandler:
    """Sync handler is called and returns WebhookResult(status='ok')."""

    @pytest.mark.asyncio
    async def test_handle_sync_handler(self) -> None:
        event = _FakeEvent(type="customer.created", id="evt_sync")
        client = _FakeClient(event=event)
        handler = StripeWebhookHandler(client)
        received_events: list[Any] = []

        def on_customer_created(evt: Any) -> None:
            received_events.append(evt)

        handler.register("customer.created", on_customer_created)

        result = await handler.handle(_PAYLOAD, _SIG)

        assert result == WebhookResult(
            status="ok", event_type="customer.created", event_id="evt_sync"
        )
        assert received_events == [event]


class TestHandleAsyncHandler:
    """Async handler is called and returns WebhookResult(status='ok')."""

    @pytest.mark.asyncio
    async def test_handle_async_handler(self) -> None:
        event = _FakeEvent(type="payment_intent.succeeded", id="evt_async")
        client = _FakeClient(event=event)
        handler = StripeWebhookHandler(client)
        received_events: list[Any] = []

        async def on_payment_succeeded(evt: Any) -> None:
            received_events.append(evt)

        handler.register("payment_intent.succeeded", on_payment_succeeded)

        result = await handler.handle(_PAYLOAD, _SIG)

        assert result == WebhookResult(
            status="ok",
            event_type="payment_intent.succeeded",
            event_id="evt_async",
        )
        assert received_events == [event]


class TestHandleUnhandledEvent:
    """Unhandled event type returns WebhookResult(status='ignored') and logs INFO."""

    @pytest.mark.asyncio
    async def test_handle_unhandled_event(self, caplog: pytest.LogCaptureFixture) -> None:
        event = _FakeEvent(type="unknown.event", id="evt_unk")
        client = _FakeClient(event=event)
        handler = StripeWebhookHandler(client)

        with caplog.at_level(logging.INFO, logger="altissimo.stripe.webhook"):
            result = await handler.handle(_PAYLOAD, _SIG)

        assert result == WebhookResult(
            status="ignored",
            event_type="unknown.event",
            event_id="evt_unk",
        )
        assert any("unknown.event" in record.message for record in caplog.records)


class TestHandleHandlerException:
    """Handler exception returns WebhookResult(status='error') with error message."""

    @pytest.mark.asyncio
    async def test_handle_handler_exception(self) -> None:
        event = _FakeEvent(type="charge.failed", id="evt_err")
        client = _FakeClient(event=event)
        handler = StripeWebhookHandler(client)

        def exploding_handler(evt: Any) -> None:
            raise ValueError("something went wrong")

        handler.register("charge.failed", exploding_handler)

        result = await handler.handle(_PAYLOAD, _SIG)

        assert result == WebhookResult(
            status="error",
            event_type="charge.failed",
            event_id="evt_err",
            error="something went wrong",
        )


class TestHandleWebhookErrorPropagates:
    """StripeWebhookError from construct_webhook_event propagates."""

    @pytest.mark.asyncio
    async def test_handle_webhook_error_propagates(self) -> None:
        error = StripeWebhookError("bad signature")
        client = _FakeClient(error=error)
        handler = StripeWebhookHandler(client)

        with pytest.raises(StripeWebhookError, match="bad signature"):
            await handler.handle(_PAYLOAD, _SIG)
