"""Altissimo Stripe — typed models and enums."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel


class PaymentIntentStatus(StrEnum):
    """Status values for a Stripe PaymentIntent."""

    REQUIRES_PAYMENT_METHOD = "requires_payment_method"
    REQUIRES_CONFIRMATION = "requires_confirmation"
    REQUIRES_ACTION = "requires_action"
    PROCESSING = "processing"
    REQUIRES_CAPTURE = "requires_capture"
    CANCELED = "canceled"
    SUCCEEDED = "succeeded"


class StripeAddress(BaseModel):
    """Pydantic model for a Stripe address structure."""

    line1: str | None = None
    line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    country: str | None = None


class StripeShipping(BaseModel):
    """Pydantic model for Stripe shipping information."""

    name: str
    address: StripeAddress


@dataclass(frozen=True, slots=True)
class WebhookResult:
    """Typed result object returned by webhook dispatch.

    Attributes:
        status: One of ``"ok"``, ``"ignored"``, or ``"error"``.
        event_type: The Stripe event type string (e.g. ``"payment_intent.succeeded"``).
        event_id: The Stripe event ID, if available.
        error: An error message, if the handler raised.
    """

    status: str
    event_type: str
    event_id: str | None = None
    error: str | None = None
