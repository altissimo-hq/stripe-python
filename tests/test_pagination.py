"""Tests for altissimo.stripe.pagination.paginate()."""

from __future__ import annotations

from typing import Any

from altissimo.stripe.pagination import paginate

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class _Item:
    """Minimal object with an ``.id`` attribute for cursor pagination."""

    def __init__(self, id: str) -> None:
        self.id = id

    def __repr__(self) -> str:
        return f"_Item({self.id!r})"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Item) and self.id == other.id


class _Page:
    """Minimal object with ``.data`` and ``.has_more`` matching Stripe SDK shape."""

    def __init__(self, data: list[Any], *, has_more: bool = False) -> None:
        self.data = data
        self.has_more = has_more


def _make_list_fn(pages: list[_Page]):
    """Return a callable that serves *pages* in sequence, respecting starting_after."""
    call_log: list[dict[str, Any]] = []

    def list_fn(**kwargs: Any) -> _Page:
        call_log.append(kwargs)
        # Determine which page to return based on call count
        idx = len(call_log) - 1
        return pages[idx]

    list_fn.call_log = call_log  # type: ignore[attr-defined]
    return list_fn


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPaginateSinglePage:
    """paginate() yields all items when the first page has has_more=False."""

    def test_yields_all_items(self) -> None:
        items = [_Item("a"), _Item("b"), _Item("c")]
        page = _Page(items, has_more=False)
        list_fn = _make_list_fn([page])

        result = list(paginate(list_fn))

        assert result == items

    def test_single_api_call(self) -> None:
        page = _Page([_Item("x")], has_more=False)
        list_fn = _make_list_fn([page])

        list(paginate(list_fn))

        assert len(list_fn.call_log) == 1


class TestPaginateMultiplePages:
    """paginate() follows starting_after cursor across pages."""

    def test_yields_all_items_across_pages(self) -> None:
        page1 = _Page([_Item("1"), _Item("2")], has_more=True)
        page2 = _Page([_Item("3"), _Item("4")], has_more=True)
        page3 = _Page([_Item("5")], has_more=False)
        list_fn = _make_list_fn([page1, page2, page3])

        result = list(paginate(list_fn))

        assert result == [_Item("1"), _Item("2"), _Item("3"), _Item("4"), _Item("5")]

    def test_starting_after_cursor_set_correctly(self) -> None:
        page1 = _Page([_Item("a"), _Item("b")], has_more=True)
        page2 = _Page([_Item("c")], has_more=False)
        list_fn = _make_list_fn([page1, page2])

        list(paginate(list_fn))

        # First call should have no starting_after
        assert "starting_after" not in list_fn.call_log[0]
        # Second call should use last item's id from first page
        assert list_fn.call_log[1]["starting_after"] == "b"


class TestPaginateEmptyPage:
    """paginate() yields nothing when the first page is empty."""

    def test_empty_first_page(self) -> None:
        page = _Page([], has_more=False)
        list_fn = _make_list_fn([page])

        result = list(paginate(list_fn))

        assert result == []


class TestPaginateLimit:
    """paginate() forwards the limit parameter to the list function."""

    def test_default_limit(self) -> None:
        page = _Page([], has_more=False)
        list_fn = _make_list_fn([page])

        list(paginate(list_fn))

        assert list_fn.call_log[0]["limit"] == 100

    def test_custom_limit(self) -> None:
        page = _Page([], has_more=False)
        list_fn = _make_list_fn([page])

        list(paginate(list_fn, limit=25))

        assert list_fn.call_log[0]["limit"] == 25

    def test_limit_preserved_across_pages(self) -> None:
        page1 = _Page([_Item("a")], has_more=True)
        page2 = _Page([_Item("b")], has_more=False)
        list_fn = _make_list_fn([page1, page2])

        list(paginate(list_fn, limit=10))

        assert list_fn.call_log[0]["limit"] == 10
        assert list_fn.call_log[1]["limit"] == 10
