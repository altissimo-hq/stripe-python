"""Altissimo Stripe — generic cursor-based pagination for Stripe list endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator


def paginate(
    list_fn: Callable[..., Any],
    *,
    limit: int = 100,
    **params: Any,
) -> Iterator[Any]:
    """Generic cursor-based pagination for Stripe list endpoints.

    Yields individual Stripe objects from paginated list responses,
    automatically following ``starting_after`` cursors until all
    pages have been consumed.

    Args:
        list_fn: A Stripe SDK list function (e.g. ``stripe.Customer.list``).
        limit: Number of items per page (max 100).
        **params: Additional parameters forwarded to ``list_fn``.

    Yields:
        Individual Stripe objects from successive pages.
    """
    while True:
        response = list_fn(limit=limit, **params)
        yield from response.data
        if not response.has_more:
            break
        params["starting_after"] = response.data[-1].id
