# Baak Books local redesign decisions

## Scope

This work is local-only in `/home/ubuntu/baakbook-local`. It must not push to GitHub or modify PythonAnywhere. The existing storefront identity remains warm, editorial, and book-led; the experiment lab becomes a quiet testing surface rather than the customer-facing navigation.

## Experience principles

- Use one primary action per section and explain every secondary feature in plain Arabic.
- Keep the warm Baak Books palette and typography; remove visual noise before adding decoration.
- Dark mode must use explicit high-contrast text, borders, inputs, badges, and focus states. It is a local preference only.
- Gift ordering is a real order-type prototype: the customer chooses a curated bundle or books, provides recipient and message details, and the order is stored with `order_type: gift` and a `gift` object.
- On-demand books are purchasable even when `stock_quantity` is zero when `availability_type` is `on_demand`; the customer sees a clear lead-time note and the order item preserves the availability type.
- Admin controls are grouped into feature flags, products, orders, and delivery. Every control includes a short explanation and safe default.

## Data model extensions

### Product

`availability_type` is `in_stock` or `on_demand`.

`lead_time_days` is an integer used for on-demand fulfillment messaging.

`featured` is a boolean used by the simplified homepage feature row.

### Order

`order_type` is `standard`, `gift`, or `on_demand`.

`gift` is optional and contains recipient name, occasion, message, sender name, and wrapping flag.

`fulfillment_note` is a human-readable note for on-demand orders.

### Settings

`settings.features` contains local feature flags for discovery, gifts, on-demand books, dark mode, community prototypes, and smart search.

## Validation gates

1. Python syntax and JSON validation.
2. Public catalog, gift order, on-demand order, and admin authorization tests.
3. Manual mobile and desktop review of the homepage, feature explanations, dark mode, gift flow, and on-demand labels.
4. No `git push`; no production data; no production deployment.

## Rollback

The local workspace remains the only edited workspace. Revert the local commit or restore the prior local files if a prototype is rejected. Production remains unchanged until the user explicitly approves a later promotion step.
