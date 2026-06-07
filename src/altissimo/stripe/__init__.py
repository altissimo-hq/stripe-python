"""Altissimo Stripe — typed client, webhook handler, and helpers.

Public API surface::

    from altissimo.stripe import (
        # Client
        StripeClient,
        # Webhook handler
        StripeWebhookHandler,
        # Pagination
        paginate,
        # Models
        PaymentIntentStatus,
        StripeAddress,
        StripeShipping,
        WebhookResult,
        # Exceptions
        StripeError,
        StripeImportError,
        StripeApiError,
        StripeWebhookError,
    )
"""

from altissimo.stripe.client import StripeClient
from altissimo.stripe.exceptions import (
    StripeApiError,
    StripeError,
    StripeImportError,
    StripeWebhookError,
)
from altissimo.stripe.models import (
    PaymentIntentStatus,
    StripeAddress,
    StripeShipping,
    WebhookResult,
)
from altissimo.stripe.pagination import paginate
from altissimo.stripe.webhook import StripeWebhookHandler

__all__ = [
    "PaymentIntentStatus",
    "StripeAddress",
    "StripeApiError",
    "StripeClient",
    "StripeError",
    "StripeImportError",
    "StripeShipping",
    "StripeWebhookError",
    "StripeWebhookHandler",
    "WebhookResult",
    "paginate",
]
