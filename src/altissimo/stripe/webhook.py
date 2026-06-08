"""Altissimo Stripe — webhook handler framework.

Provides a reusable webhook dispatch system with signature verification,
decorator-based handler registration, and support for both sync and async
handler functions.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from typing import Any

from altissimo.stripe.exceptions import StripeWebhookError
from altissimo.stripe.models import WebhookResult

logger = logging.getLogger(__name__)


class StripeWebhookHandler:
    """Reusable webhook dispatch with signature verification.

    Usage::

        from altissimo.stripe import StripeClient, StripeWebhookHandler

        client = StripeClient.from_env()
        handler = StripeWebhookHandler(client)

        @handler.on("payment_intent.succeeded")
        async def on_payment_succeeded(event):
            ...

        # In your web framework endpoint:
        result = await handler.handle(payload, sig_header)

    Args:
        client: A configured :class:`StripeClient` instance.
    """

    def __init__(self, client: Any) -> None:
        # Import here to avoid circular imports; accept any client-like object
        self._client = client
        self._handlers: dict[str, Callable[..., Any]] = {}

    def on(self, event_type: str) -> Callable[..., Any]:
        """Decorator to register a handler for a Stripe event type.

        Args:
            event_type: The Stripe event type (e.g. ``"payment_intent.succeeded"``).

        Returns:
            A decorator that registers the handler function.

        Example::

            @handler.on("payment_intent.succeeded")
            async def handle_success(event):
                ...
        """

        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            self._handlers[event_type] = fn
            return fn

        return decorator

    def register(self, event_type: str, handler: Callable[..., Any]) -> None:
        """Programmatically register a handler for an event type.

        Args:
            event_type: The Stripe event type.
            handler: A sync or async callable accepting the event object.
        """
        self._handlers[event_type] = handler

    async def handle(
        self,
        payload: bytes | str,
        sig_header: str,
    ) -> WebhookResult:
        """Verify the webhook signature, parse the event, and dispatch.

        This method:

        1. Verifies the signature and parses the event via the client.
        2. Looks up a registered handler for the event type.
        3. Invokes the handler (supporting both sync and async callables).
        4. Returns a :class:`WebhookResult`.

        Unhandled event types are logged at ``INFO`` level and return a
        result with ``status="ignored"``.

        Args:
            payload: Raw request body bytes (or string).
            sig_header: Value of the ``Stripe-Signature`` header.

        Returns:
            A :class:`WebhookResult` describing the outcome.

        Raises:
            StripeWebhookError: If signature verification or payload
                parsing fails.
        """
        # 1. Verify + parse — StripeWebhookError propagates on failure
        event = self._client.construct_webhook_event(payload, sig_header)
        event_type: str = event.type  # type: ignore[union-attr]
        event_id: str | None = getattr(event, "id", None)

        # 2. Look up handler
        handler_fn = self._handlers.get(event_type)
        if handler_fn is None:
            logger.info("Unhandled Stripe webhook event type: %s", event_type)
            return WebhookResult(
                status="ignored",
                event_type=event_type,
                event_id=event_id,
            )

        # 3. Dispatch — support both sync and async handlers
        try:
            if asyncio.iscoroutinefunction(handler_fn):
                await handler_fn(event)
            else:
                handler_fn(event)
        except StripeWebhookError:
            raise
        except Exception as exc:
            logger.exception("Handler for %s raised an exception", event_type)
            return WebhookResult(
                status="error",
                event_type=event_type,
                event_id=event_id,
                error=str(exc),
            )

        return WebhookResult(
            status="ok",
            event_type=event_type,
            event_id=event_id,
        )
