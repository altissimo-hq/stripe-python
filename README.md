# altissimo-stripe

Typed Stripe client, webhook handler, and helpers for the Altissimo platform.

## Installation

```bash
pip install altissimo-stripe[stripe]
```

The `stripe` SDK is an **optional dependency**. Install the `[stripe]` extra to
include it. The package can be imported without `stripe` installed (e.g. for
type-checking or using the test helpers), but API calls will raise
`StripeImportError` at runtime.

## Quick Start

### Client

```python
from altissimo.stripe import StripeClient

# From environment variables
client = StripeClient.from_env()

# Or explicit
client = StripeClient(
    api_key="sk_test_...",
    webhook_signing_secret="whsec_...",
)

# Operations
customer = client.create_customer(email="user@example.com", name="Jane Doe")
pi = client.create_payment_intent(2000, "usd", description="Order #123")
intent = client.retrieve_payment_intent("pi_xxx")
```

### Paginated Iteration

```python
# Automatic cursor-based pagination
for customer in client.iter_customers():
    print(customer.email)

for charge in client.iter_charges(limit=50):
    print(charge.amount)

# Or use the generic helper directly
from altissimo.stripe import paginate

for item in paginate(some_list_fn, limit=100, active=True):
    ...
```

### Webhook Handler

```python
from altissimo.stripe import StripeClient, StripeWebhookHandler

client = StripeClient.from_env()
handler = StripeWebhookHandler(client)

@handler.on("payment_intent.succeeded")
async def on_payment_succeeded(event):
    payment_intent = event.data.object
    print(f"Payment {payment_intent.id} succeeded!")

@handler.on("customer.created")
def on_customer_created(event):  # sync handlers work too
    customer = event.data.object
    print(f"New customer: {customer.email}")

# In your web framework endpoint:
result = await handler.handle(request_body, stripe_signature_header)
# result.status is "ok", "ignored", or "error"
```

### Typed Models

```python
from altissimo.stripe import PaymentIntentStatus, StripeAddress, StripeShipping

status = PaymentIntentStatus.SUCCEEDED
assert status.value == "succeeded"

address = StripeAddress(
    line1="123 Main St",
    city="Springfield",
    state="IL",
    postal_code="62704",
    country="US",
)

shipping = StripeShipping(name="Jane Doe", address=address)
```

### Exceptions

```python
from altissimo.stripe import StripeApiError, StripeImportError, StripeWebhookError

try:
    client.retrieve_customer("cus_nonexistent")
except StripeApiError as e:
    print(e.status_code)  # e.g. 404
    print(e.code)         # e.g. "resource_missing"
```

### Test Helpers

```python
from altissimo.stripe.testing import FakeStripeClient, FakePage

fake = FakeStripeClient(
    list_customers_response=FakePage([mock_customer_1, mock_customer_2]),
    retrieve_customer_response=mock_customer_1,
)

# Use the fake in place of a real client
result = fake.list_customers(limit=10)
assert result.data == [mock_customer_1, mock_customer_2]

# All calls are recorded
assert fake.calls[0].method == "list_customers"
assert fake.calls[0].kwargs == {"limit": 10}
```

## Architecture

- **Instance-based client** — supports DI, multiple instances, clean testing
- **Lazy SDK import** — zero import-time side effects; `stripe` imported only inside methods
- **Implicit namespace** — `altissimo` is a namespace package, coexisting with other `altissimo-*` packages
- **Keyword-only args** — all public methods use keyword-only arguments (except positional ID params)

## License

See [LICENSE](LICENSE).
