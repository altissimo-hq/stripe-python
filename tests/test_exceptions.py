"""Tests for altissimo.stripe.exceptions."""

from altissimo.stripe.exceptions import (
    StripeApiError,
    StripeError,
    StripeImportError,
    StripeWebhookError,
)


class TestStripeError:
    def test_is_exception(self) -> None:
        assert issubclass(StripeError, Exception)

    def test_custom_message(self) -> None:
        err = StripeError("something went wrong")
        assert str(err) == "something went wrong"


class TestStripeImportError:
    def test_inherits_stripe_error_and_import_error(self) -> None:
        assert issubclass(StripeImportError, StripeError)
        assert issubclass(StripeImportError, ImportError)

    def test_default_message(self) -> None:
        err = StripeImportError()
        assert "stripe" in str(err).lower()
        assert "altissimo-stripe[stripe]" in str(err)

    def test_custom_message(self) -> None:
        err = StripeImportError("custom msg")
        assert str(err) == "custom msg"

    def test_catchable_as_stripe_error(self) -> None:
        try:
            raise StripeImportError
        except StripeError:
            pass  # expected

    def test_catchable_as_import_error(self) -> None:
        try:
            raise StripeImportError
        except ImportError:
            pass  # expected


class TestStripeApiError:
    def test_inherits_stripe_error(self) -> None:
        assert issubclass(StripeApiError, StripeError)

    def test_attributes(self) -> None:
        original = ValueError("underlying")
        err = StripeApiError(
            "API failed",
            status_code=402,
            code="card_declined",
            original=original,
        )
        assert str(err) == "API failed"
        assert err.status_code == 402
        assert err.code == "card_declined"
        assert err.original is original

    def test_defaults(self) -> None:
        err = StripeApiError("fail")
        assert err.status_code is None
        assert err.code is None
        assert err.original is None


class TestStripeWebhookError:
    def test_inherits_stripe_error(self) -> None:
        assert issubclass(StripeWebhookError, StripeError)

    def test_attributes(self) -> None:
        original = RuntimeError("sig fail")
        err = StripeWebhookError("bad sig", original=original)
        assert str(err) == "bad sig"
        assert err.original is original

    def test_defaults(self) -> None:
        err = StripeWebhookError("fail")
        assert err.original is None
