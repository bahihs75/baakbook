-- Baak Books D1 schema v1
-- SQLite-compatible for local verification and Cloudflare D1.
-- No secrets or source data are stored in this schema file.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS categories (
    slug TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);

CREATE TABLE IF NOT EXISTS delivery_fees (
    region_number INTEGER PRIMARY KEY,
    region_name TEXT NOT NULL,
    domicile_fee INTEGER NOT NULL CHECK (domicile_fee >= 0),
    stop_desk_fee INTEGER NOT NULL CHECK (stop_desk_fee >= 0)
);

CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY,
    legacy_id TEXT NOT NULL UNIQUE,
    category_slug TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    image_url TEXT NOT NULL DEFAULT '',
    price INTEGER NOT NULL CHECK (price >= 0),
    stock_quantity INTEGER NOT NULL DEFAULT 0 CHECK (stock_quantity >= 0),
    availability_type TEXT NOT NULL CHECK (availability_type IN ('in_stock', 'on_demand')),
    lead_time_min_days INTEGER NOT NULL DEFAULT 0 CHECK (lead_time_min_days BETWEEN 0 AND 1),
    lead_time_max_days INTEGER NOT NULL DEFAULT 0 CHECK (lead_time_max_days BETWEEN 0 AND 1),
    lead_time_days INTEGER NOT NULL DEFAULT 0 CHECK (lead_time_days BETWEEN 0 AND 1),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    featured INTEGER NOT NULL DEFAULT 0 CHECK (featured IN (0, 1)),
    giftable INTEGER NOT NULL DEFAULT 0 CHECK (giftable IN (0, 1)),
    discoverable INTEGER NOT NULL DEFAULT 1 CHECK (discoverable IN (0, 1)),
    archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1)),
    legacy_payload_json TEXT NOT NULL DEFAULT '{}',
    schema_version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_slug) REFERENCES categories(slug),
    CHECK (lead_time_min_days <= lead_time_max_days),
    CHECK (availability_type = 'in_stock' OR lead_time_max_days <= 1)
);

CREATE TABLE IF NOT EXISTS product_tags (
    product_id TEXT NOT NULL,
    tag_type TEXT NOT NULL CHECK (tag_type IN ('discovery', 'gift')),
    tag TEXT NOT NULL,
    PRIMARY KEY (product_id, tag_type, tag),
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    legacy_order_id TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK (status IN ('new', 'confirmed', 'awaiting_supply', 'processing', 'ready_to_ship', 'shipped', 'delivered', 'cancelled', 'returned')),
    customer_name TEXT NOT NULL DEFAULT '',
    phone TEXT NOT NULL DEFAULT '',
    address TEXT NOT NULL DEFAULT '',
    wilaya TEXT NOT NULL DEFAULT '',
    delivery_type TEXT NOT NULL DEFAULT '',
    delivery_fee INTEGER NOT NULL DEFAULT 0 CHECK (delivery_fee >= 0),
    order_type TEXT NOT NULL DEFAULT '',
    shipping_policy TEXT NOT NULL DEFAULT '',
    fulfillment_note TEXT NOT NULL DEFAULT '',
    subtotal INTEGER NOT NULL DEFAULT 0 CHECK (subtotal >= 0),
    total INTEGER NOT NULL DEFAULT 0 CHECK (total >= 0),
    source_timestamp TEXT NOT NULL DEFAULT '',
    idempotency_key TEXT UNIQUE,
    legacy_status TEXT,
    legacy_payload_json TEXT NOT NULL DEFAULT '{}',
    schema_version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    product_id TEXT NOT NULL,
    item_role TEXT NOT NULL CHECK (item_role IN ('personal', 'gift')),
    title_snapshot TEXT NOT NULL DEFAULT '',
    image_snapshot TEXT NOT NULL DEFAULT '',
    price_snapshot INTEGER NOT NULL DEFAULT 0 CHECK (price_snapshot >= 0),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    purchase_purpose TEXT NOT NULL DEFAULT '',
    availability_type TEXT NOT NULL DEFAULT '',
    lead_time_min_days INTEGER NOT NULL DEFAULT 0 CHECK (lead_time_min_days BETWEEN 0 AND 1),
    lead_time_max_days INTEGER NOT NULL DEFAULT 0 CHECK (lead_time_max_days BETWEEN 0 AND 1),
    legacy_payload_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id),
    UNIQUE (order_id, line_number)
);

CREATE TABLE IF NOT EXISTS order_gifts (
    order_id TEXT PRIMARY KEY,
    source TEXT NOT NULL DEFAULT '',
    sender_name TEXT NOT NULL DEFAULT '',
    recipient_name TEXT NOT NULL DEFAULT '',
    recipient_phone TEXT NOT NULL DEFAULT '',
    recipient_type TEXT NOT NULL DEFAULT '',
    message TEXT NOT NULL DEFAULT '',
    occasion TEXT NOT NULL DEFAULT '',
    mood TEXT NOT NULL DEFAULT '',
    budget INTEGER CHECK (budget IS NULL OR budget >= 0),
    anonymous INTEGER NOT NULL DEFAULT 0 CHECK (anonymous IN (0, 1)),
    gift_item_ids_json TEXT NOT NULL DEFAULT '[]',
    legacy_payload_json TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS feature_flags (
    key TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL CHECK (enabled IN (0, 1)),
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS store_settings (
    key TEXT PRIMARY KEY,
    value_json TEXT NOT NULL,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS image_assets (
    id TEXT PRIMARY KEY,
    product_id TEXT,
    storage_provider TEXT NOT NULL CHECK (storage_provider IN ('external', 'r2')),
    object_key TEXT,
    public_url TEXT NOT NULL,
    original_filename TEXT,
    mime_type TEXT,
    byte_size INTEGER CHECK (byte_size IS NULL OR byte_size >= 0),
    archived INTEGER NOT NULL DEFAULT 0 CHECK (archived IN (0, 1)),
    legacy_payload_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS migration_batches (
    batch_id TEXT PRIMARY KEY,
    source_sha256 TEXT NOT NULL,
    row_counts_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('prepared', 'imported', 'verified', 'rolled_back')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verified_at TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_products_category_title ON products(category_slug, title);
CREATE INDEX IF NOT EXISTS idx_products_active_featured ON products(active, archived, featured);
CREATE INDEX IF NOT EXISTS idx_products_availability ON products(availability_type, active, archived);
CREATE INDEX IF NOT EXISTS idx_product_tags_lookup ON product_tags(tag_type, tag);
CREATE INDEX IF NOT EXISTS idx_orders_status_created ON orders(status, created_at);
CREATE INDEX IF NOT EXISTS idx_orders_phone ON orders(phone);
CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id, line_number);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_images_product_active ON image_assets(product_id, archived);
