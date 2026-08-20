# Baak Books — One-Shot Cutover Runbook

## Purpose

This runbook is executed only after the new frontend, Functions, Firestore Rules, migration tooling, and staging acceptance tests are complete. It moves live data once and activates `https://baakbook.pages.dev`.

## Preconditions

All conditions below must be true:

- Local tests pass.
- Staging end-to-end tests pass.
- Firestore Rules tests pass.
- Functions have explicit timeouts and structured errors.
- The frontend has production Firebase configuration through deployment secrets/configuration.
- The Pages build is reproducible and a preview deployment has been accepted.
- The two independent verification tools have passed against staging.
- A fresh backup of the current PythonAnywhere files exists.
- The user has selected a short cutover window.
- The old PythonAnywhere URL and data remain available for rollback.

## Cutover inputs

| Input | Source | Required evidence |
|---|---|---|
| Live data export | PythonAnywhere `data.json` | File timestamp, byte size, SHA-256 |
| Source inventory | Local read-only verifier | JSON report with no fatal validation errors |
| Target Firebase project | Production Firebase | Project ID and Rules deployment status |
| Pages deployment | Cloudflare Pages | Deployment URL and successful smoke check |
| Migration batch ID | Local migration tool | Unique value not previously completed |

## Execution sequence

### 1. Announce and freeze

At the start of the agreed window, stop accepting new orders on PythonAnywhere and pause admin edits. The old site must remain readable. Record the exact UTC timestamp and the operator.

Do not begin a live import while orders or products are still being changed.

### 2. Export

Copy the live `data.json` into a protected local staging path. Do not edit the file. Compute:

- SHA-256.
- Byte size.
- Product count.
- Category count.
- Delivery-fee count.
- Order count and order-item count.
- Sum of historical order totals.
- Product and order ID sets.

If the export cannot be read or fails validation, abort before touching Firebase.

### 3. Independent source verification

Run the source verifier and save its report under a unique migration batch directory. A second process or separately implemented check must recompute the core counts and ID sets from the raw export rather than trusting the first report.

The two source reports must agree exactly before import.

### 4. Import once

Use deterministic Firestore document IDs. The importer must:

- Refuse a completed batch ID.
- Refuse a source hash already marked as completed.
- Preserve legacy IDs and payloads.
- Use bounded batches.
- Log each collection count.
- Stop on validation error instead of silently skipping records.
- Write `migrationMetadata` only after all collections are written.

The importer is not called by the public website. It runs as a one-time operator command with production credentials supplied through the environment.

### 5. Independent target verification

Read Firestore back using an independent verifier. Recompute counts, ID sets, record fingerprints, order-item counts, and financial sums from the target. Compare them with the source reports.

Required result:

```text
source_sha256: recorded
products: exact match
categories: exact match
delivery_fees: exact match
orders: exact match
order_items: exact match
historical totals: exact match or documented legacy exception
missing IDs: zero
duplicates: zero
unexplained differences: zero
```

### 6. Smoke test production functions

Before making the Pages URL public, run a controlled test with a clearly marked test payload according to the agreed policy. Confirm that:

- The server recalculates the price.
- An unavailable book is rejected.
- A non-giftable book cannot be added to a gift group.
- A gift requires recipient name and phone.
- A repeated idempotency key does not create a second order.
- The resulting test record is clearly identifiable and removable/archivable according to policy.

### 7. Activate Pages

Promote or deploy the accepted production build to the Pages project configured for `baakbook.pages.dev`. Verify:

- HTTPS certificate and URL availability.
- Public catalog loading.
- Firebase connection.
- Admin login.
- Product and order screens.
- Arabic typography and dark-mode contrast.
- No production secrets appear in browser source or logs.

### 8. Reopen

Only after the smoke checks pass, reopen order intake on the new site and display the new URL to customers. Keep PythonAnywhere frozen or clearly marked as the old system until the monitoring period ends.

### 9. Record the result

Save a final cutover record with:

- Source export hash.
- Migration batch ID.
- Source and target reports.
- Deployment identifier.
- Cutover timestamp.
- Smoke-test result.
- Operator notes.
- Any known exceptions.

## Abort conditions

Abort before activation if any of the following occurs:

- Source export is incomplete, unreadable, or changes during verification.
- Counts, IDs, fingerprints, or financial sums differ without an approved explanation.
- Rules tests fail.
- Functions cannot validate price and availability.
- Pages build or Firebase configuration is incomplete.
- Admin access is broader than intended.
- A duplicate order is possible on retry.

## Post-cutover monitoring

For the first monitoring period, track catalog read failures, order creation failures, duplicate idempotency keys, Function latency, permission denials, and manual admin edits. Do not delete PythonAnywhere or the original export during this period.
