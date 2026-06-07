"""Altissimo Stripe — exception hierarchy.

Wraps the Stripe SDK's native exceptions into a consistent hierarchy
that does not leak SDK internals.
"""

from __future__ import annotations


class StripeError(Exception):
    """Base exception for all Stripe-related errors."""


class StripeImportError(StripeError, ImportError):
    """Raised when the ``stripe`` SDK package is not installed."""

    def __init__(self, msg: str | None = None) -> None:
        super().__init__(
            msg
            or (
                "The 'stripe' package is required but not installed. "
                "Install it with: pip install altissimo-stripe[stripe]"
            )
        )


class StripeApiError(StripeError):
    """Raised when a Stripe API call fails.

    Wraps ``stripe.error.StripeError`` with a stable public interface.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        original: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.original = original


class StripeWebhookError(StripeError):
    """Raised for webhook signature or payload verification failures."""

    def __init__(
        self,
        message: str,
        *,
        original: Exception | None = None,
    ) -> None:
        super().__init__(message)
        self.original = original
