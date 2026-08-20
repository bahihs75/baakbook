# Baak Books — Cloudflare Pages + Firebase Architecture

## Scope

This document defines the target production architecture for `https://baakbook.pages.dev`. It is intentionally independent from the current Flask runtime so the migration can be prepared locally without modifying PythonAnywhere or publishing code.

## Target components

| Component | Target | Responsibility | Trust level |
|---|---|---|---|
| Public storefront | Cloudflare Pages | Static HTML/CSS/JS or compiled frontend assets | Untrusted client |
| Admin UI | Same Pages project under `/admin` | Product, order, settings, and image-library screens | Untrusted client, authenticated |
| Public data | Cloud Firestore | Published products, categories, delivery fees, public feature flags | Read-only for public fields |
| Sensitive mutations | Firebase Cloud Functions 2nd gen | Order creation, price validation, stock checks, admin writes, ImgBB upload | Trusted server boundary |
| Authentication | Firebase Authentication | Admin identity and session token | Managed identity provider |
| Image storage | Existing ImgBB URLs in migration 1 | Preserve current covers without moving binaries | External dependency |
| Audit trail | Firestore `auditLogs` | Admin mutation trace and migration events | Admin/service only |

Cloudflare Pages serves files; it does not become the authority for prices, inventory, orders, or admin authorization. Firebase Functions are the trusted boundary for mutations. Firestore Rules remain active even when a Function is used, and Admin SDK access must be limited to server code.

## Runtime environments

| Environment | Pages address | Firebase project | Data policy |
|---|---|---|---|
| Local | `http://localhost:5173` or equivalent | Firebase Emulator Suite or no remote project | Synthetic data only |
| Staging | Cloudflare preview URL | `baak-books-staging` | Synthetic or explicitly sanitized export only |
| Production | `https://baakbook.pages.dev` | Production Firebase project | Live catalog and orders after one-shot cutover |

No production Firebase project is needed to design the local adapters. Production secrets and credentials are never committed to Git.

## Data-flow rules

### Public catalog read

1. The storefront requests only active catalog documents.
2. The client applies presentation filters such as category and discovery tags.
3. Any public query is bounded and indexed; no unbounded collection read is allowed.
4. Missing or unavailable data produces a readable fallback state rather than a false empty inventory.

### Order creation

1. The client sends a validated checkout payload and a random `idempotencyKey`.
2. A callable Function authenticates the request context where required, validates the payload, and creates a request ID.
3. The Function reads authoritative product and delivery-fee documents.
4. It validates availability, price, giftability, recipient phone, one gift group, and lead-time constraints.
5. It calculates the subtotal, delivery fee, and total from authoritative values.
6. It creates one order transactionally or returns the previously created order for the same idempotency key.
7. It returns a public order reference and safe status information; internal details remain in logs.

### Admin mutation

1. Firebase Authentication provides the identity token.
2. A custom claim or server-checked role identifies the administrator.
3. The Function validates the mutation and writes the target document plus an audit record.
4. The client refreshes its data after a successful mutation.
5. Deletes are not exposed in the first migration; use `active=false` or `archived=true`.

## Security model

### Public reads

Public access is limited to fields required for the storefront. Orders, audit logs, migration metadata, and image-library management are not public.

### Admin access

The browser is never trusted merely because it displays the admin page. Every admin Function verifies the Firebase ID token and role. Firestore Rules also reject direct writes from non-admin users.

### Secrets

The following values must exist only in local secret files, Cloudflare/Firebase secret configuration, or an appropriate secret manager:

- Firebase Admin credentials or service-account material.
- ImgBB API key.
- Any migration credential.
- Any webhook or notification secret.

The Firebase Web SDK configuration may be exposed to the browser, but it is not a security boundary; Rules and server authorization remain mandatory.

## Error contract

Functions return a stable envelope:

```json
{
  "ok": false,
  "error": {
    "code": "PRODUCT_UNAVAILABLE",
    "message": "تعذر تأكيد أحد الكتب لأن توفره تغيّر.",
    "requestId": "req_..."
  }
}
```

Public messages are Arabic and safe to display. Logs carry the structured error code, request ID, function name, latency, and relevant entity IDs without exposing recipient phone numbers or full addresses.

## External-call policy

ImgBB calls use explicit connect and read timeouts, bounded retries with jitter for retryable failures, and no retry for validation failures. A failed image upload must not corrupt the product document. The Function either stores a complete image record or returns a recoverable error.

## Indexes and query shapes

The initial Firestore index plan is deliberately small:

| Query | Collection | Required shape |
|---|---|---|
| Active catalog by category | `products` | `active == true`, optional `category`, ordered by `title` |
| Featured active products | `products` | `active == true`, `featured == true`, ordered by `title` |
| Admin orders by status | `orders` | `status`, `createdAt desc`, cursor pagination |
| Admin orders by date | `orders` | `createdAt desc`, cursor pagination |
| Image library by archive state | `imageLibrary` | `archived == false`, `createdAt desc` |

The storefront will not fetch all orders, all images, or the entire product collection without a limit.

## Observability

Every Function request receives a request ID. Structured logs include request ID, operation, entity ID, status, latency, and error code. Sensitive personal data is excluded or redacted. The cutover also records source hash, target verification result, migration batch ID, and timestamp in `migrationMetadata`.

## Architecture decisions

### ADR-001 — Firestore over Realtime Database

**Problem:** The store has separate product, order, settings, and admin resources with different access policies and query shapes.

**Alternatives:** Realtime Database, Firestore, or retaining JSON behind a Flask API.

**Decision:** Use Cloud Firestore for the new system. It provides document-shaped data, rules suited to resource access, query indexes, and a natural separation between public catalog and protected orders.

**Consequence:** Indexes and usage limits must be monitored, and the migration must preserve document IDs and historical snapshots.

### ADR-002 — Functions for trusted mutations

**Problem:** The browser cannot be trusted to submit the final price, stock state, or gift eligibility.

**Decision:** Use callable HTTPS Functions for order creation and sensitive admin actions. The client may calculate a preview, but the server calculation is authoritative.

**Consequence:** The Functions code must be versioned, tested, and deployed alongside Rules. It also introduces a server-side deployment step and possible Firebase billing prerequisites.

### ADR-003 — Pages URL as the first production address

**Problem:** The migration needs a known target without a DNS cutover.

**Decision:** Use `https://baakbook.pages.dev` as the production address.

**Consequence:** The PythonAnywhere subdomain remains available for rollback, but it is not the same hostname. A custom domain can be added later as a separate DNS change.
