# Baak Books — Firestore Data Contract

## Principles

The contract preserves the current business meaning before introducing any convenience renames. Existing field names remain available during the first migration so the frontend and importer can be compared directly. Every document carries `schemaVersion` and `legacyId` where a source identifier exists.

## Collections

### `products/{productId}`

```json
{
  "id": "bk001",
  "legacyId": "bk001",
  "title": "قواعد جارتين",
  "category": "روايات",
  "desc": "...",
  "img": "https://...",
  "price": 1200,
  "active": true,
  "stock_quantity": 10,
  "availability_type": "in_stock",
  "lead_time_min_days": 0,
  "lead_time_max_days": 0,
  "lead_time_days": 0,
  "featured": false,
  "giftable": true,
  "discoverable": true,
  "discovery_tags": [],
  "gift_tags": [],
  "editorial_note": "",
  "archived": false,
  "schemaVersion": 1,
  "createdAt": "server timestamp",
  "updatedAt": "server timestamp"
}
```

Validation:

- `id`, `title`, and `category` are non-empty strings.
- `price` is a positive integer in Algerian dinars.
- `stock_quantity` is an integer greater than or equal to zero.
- `availability_type` is `in_stock` or `on_demand`.
- `lead_time_min_days` and `lead_time_max_days` are integers in `[0, 1]`, and maximum is not less than minimum.
- `on_demand` products do not rely on stock quantity for public availability.
- `active=false` hides the product from public catalog queries but does not delete history.

### `categories/{categoryId}`

```json
{
  "name": "روايات",
  "sortOrder": 10,
  "active": true,
  "legacyValue": "روايات",
  "schemaVersion": 1
}
```

During migration, the legacy category value is the stable key. A future slug can be added without changing historical order snapshots.

### `deliveryFees/{deliveryFeeId}`

```json
{
  "num": 16,
  "name": "الجزائر",
  "stop_desk": 450,
  "domicile": 850,
  "active": true,
  "legacyNum": 16,
  "schemaVersion": 1
}
```

Negative values from the source remain visible in `legacyPayload` and are converted to an explicit unavailable state; they must not become a valid negative delivery charge.

### `settings/public`

```json
{
  "features": {
    "discovery": true,
    "gifts": true,
    "gift_from_product": true,
    "gift_from_cart": true,
    "gift_finder": true,
    "on_demand": true,
    "dark_mode": true,
    "community": false,
    "smart_search": false,
    "ideas_lab": true
  },
  "schemaVersion": 1,
  "updatedAt": "server timestamp"
}
```

Only explicitly public feature flags are readable without authentication. Administrative flags and operational settings can be split into `settings/admin` if they should not be exposed.

### `orders/{orderId}`

```json
{
  "id": "order-legacy-1",
  "legacyOrderId": 1,
  "status": "new",
  "items": [],
  "giftGroups": [],
  "customer": {},
  "delivery": {},
  "subtotal": 3250,
  "deliveryFee": 0,
  "total": 3250,
  "currency": "DZD",
  "idempotencyKey": null,
  "source": "legacy-pythonanywhere",
  "legacyPayload": {},
  "schemaVersion": 1,
  "createdAt": "source timestamp or import timestamp",
  "updatedAt": "import timestamp"
}
```

Legacy orders are immutable historical records during import. New orders receive item snapshots, authoritative totals, a generated request ID, and an idempotency key. Statuses are normalized to the current set while `legacyStatus` preserves the source value when it differs.

### `imageLibrary/{imageId}`

```json
{
  "imageUrl": "https://i.ibb.co/...",
  "deleteUrl": null,
  "source": "imgbb",
  "linkedProductIds": ["bk001"],
  "filename": "cover.jpg",
  "mimeType": "image/jpeg",
  "bytes": 0,
  "archived": false,
  "createdAt": "server timestamp",
  "updatedAt": "server timestamp",
  "schemaVersion": 1
}
```

Existing `img` URLs migrate as `source=legacy-url` records only if the image-library feature is enabled. The first data move may keep them on products without creating a library record for every old URL.

### `migrationMetadata/{batchId}`

```json
{
  "batchId": "migration-2026-...",
  "sourceFileSha256": "...",
  "sourceCounts": {},
  "targetCounts": {},
  "sourceRecordFingerprints": {},
  "targetRecordFingerprints": {},
  "status": "verified",
  "startedAt": "server timestamp",
  "completedAt": "server timestamp",
  "toolVersion": "1.0.0"
}
```

The importer refuses to reuse a completed batch ID or source hash unless explicitly run in verification-only mode.

## Migration rules

| Source | Target | Rule |
|---|---|---|
| `products[].id` | document ID and `legacyId` | Keep stable if unique |
| `products[].img` | `img` and optional image-library record | Preserve URL exactly during first move |
| `lead_time_days` | min/max fields | Convert to `0` or `1`, preserve old field |
| `settings.features` | `settings/public.features` | Preserve values and defaults |
| `orders[].id` or `order_id` | `legacyOrderId` and stable document ID | Never generate a new ID without retaining source ID |
| old status values | normalized `status` + `legacyStatus` | Preserve original status |
| unknown fields | `legacyPayload` | Never discard silently |

## Compatibility policy

The first frontend release reads the compatibility contract above. Field renaming, collection splitting, or removal of `legacyPayload` is postponed until after the one-shot migration has passed the monitoring period and a separate schema version is approved.
