type ProductRow = {
  id: string;
  title: string;
  author?: string;
  description: string | null;
  price: number;
  stock_quantity: number;
  availability_type: string;
  lead_time_min_days: number;
  lead_time_max_days: number;
  image_url: string | null;
  category_slug: string | null;
  active: number;
  giftable: number;
  discoverable: number;
  featured: number;
  archived: number;
  legacy_payload_json?: string;
};

type CategoryRow = { slug: string; name: string; active: number };
type DeliveryRow = { region_number: number; region_name: string; domicile_fee: number; stop_desk_fee: number };
type TagRow = { product_id: string; tag: string };
type FeatureRow = { key: string; enabled: number };
type OrderRow = {
  id: string;
  legacy_order_id: string;
  created_at: string;
  source_timestamp: string;
  customer_name: string;
  phone: string;
  address: string;
  wilaya: string;
  delivery_type: string;
  order_type: string;
  subtotal: number;
  delivery_fee: number;
  total: number;
  status: string;
  fulfillment_note: string;
  shipping_policy: string;
  idempotency_key: string | null;
};

type Env = {
  DB: D1Database;
  LIBRARY_BUCKET?: R2Bucket;
  ADMIN_TOKEN: string;
  ALLOWED_ORIGIN?: string;
  TURNSTILE_SECRET_KEY?: string;
};

const jsonHeaders = { 'content-type': 'application/json; charset=utf-8' };
const VALID_PURPOSES = new Set(['personal', 'gift']);
const VALID_GIFT_SOURCES = new Set(['card', 'cart', 'discover']);
const DISCOVERY_OPTIONS = {
  goal: new Set(['story', 'growth', 'knowledge', 'escape']),
  pace: new Set(['quick', 'deep']),
  mood: new Set(['mystery', 'romance', 'fantasy', 'change']),
};

function cors(request: Request, env: Env): Headers {
  const headers = new Headers(jsonHeaders);
  const origin = request.headers.get('Origin');
  const allowed = env.ALLOWED_ORIGIN || '*';
  headers.set('Access-Control-Allow-Origin', allowed === '*' ? '*' : origin === allowed ? origin : allowed);
  headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, Idempotency-Key, X-Turnstile-Token');
  headers.set('Access-Control-Allow-Methods', 'GET,POST,PUT,DELETE,OPTIONS');
  headers.set('Vary', 'Origin');
  return headers;
}

function response(data: unknown, status: number, request: Request, env: Env): Response {
  const headers = cors(request, env);
  return new Response(JSON.stringify(data), { status, headers });
}

function fail(message: string, status: number, request: Request, env: Env, extra: Record<string, unknown> = {}): Response {
  return response({ error: message, ...extra }, status, request, env);
}

async function body(request: Request): Promise<Record<string, any>> {
  try {
    const value = await request.json();
    return value && typeof value === 'object' ? value : {};
  } catch {
    return {};
  }
}

function int(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) ? parsed : fallback;
}

function digits(value: unknown): string {
  return String(value ?? '').replace(/\D/g, '');
}

function available(product: ProductRow): boolean {
  if (product.active !== 1 || product.archived === 1) return false;
  if (product.availability_type === 'on_demand') return product.lead_time_max_days <= 1;
  return product.stock_quantity > 0;
}

function productJson(product: ProductRow, category: string | null, tags: string[]): Record<string, unknown> {
  let legacy: Record<string, any> = {};
  try { legacy = product.legacy_payload_json ? JSON.parse(product.legacy_payload_json) : {}; } catch { legacy = {}; }
  return {
    id: product.id,
    title: product.title,
    author: product.author || String(legacy.author || ''),
    desc: product.description || '',
    price: product.price,
    stock_quantity: product.stock_quantity,
    availability_type: product.availability_type,
    lead_time_min_days: product.lead_time_min_days,
    lead_time_max_days: product.lead_time_max_days,
    lead_time_days: product.lead_time_max_days,
    img: product.image_url || '',
    category: category || '',
    giftable: product.giftable === 1,
    discoverable: product.discoverable === 1,
    featured: product.featured === 1,
    active: product.active === 1,
    discovery_tags: tags,
    gift_tags: tags,
  };
}

async function loadProducts(env: Env, includeInactive = false): Promise<Record<string, unknown>[]> {
  const where = includeInactive ? '' : 'WHERE p.active = 1 AND p.archived = 0';
  const rows = await env.DB.prepare(`
    SELECT p.*, c.name AS category_name
    FROM products p LEFT JOIN categories c ON c.slug = p.category_slug
    ${where}
    ORDER BY p.featured DESC, p.title COLLATE NOCASE ASC
  `).all<ProductRow & { category_name: string | null }>();
  const tags = await env.DB.prepare('SELECT product_id, tag FROM product_tags ORDER BY product_id, tag').all<TagRow>();
  const byProduct = new Map<string, string[]>();
  for (const row of tags.results) {
    const current = byProduct.get(row.product_id) || [];
    current.push(row.tag);
    byProduct.set(row.product_id, current);
  }
  return rows.results.map(row => productJson(row, row.category_name, byProduct.get(row.id) || []));
}

async function featureEnabled(env: Env, key: string): Promise<boolean> {
  const row = await env.DB.prepare('SELECT enabled FROM feature_flags WHERE key = ?1').bind(key).first<FeatureRow>();
  return row ? row.enabled === 1 : true;
}

function adminAuthorized(request: Request, env: Env): boolean {
  const header = request.headers.get('Authorization') || '';
  return Boolean(env.ADMIN_TOKEN) && header === `Bearer ${env.ADMIN_TOKEN}`;
}

function cleanProductInput(input: Record<string, any>): Record<string, any> {
  const lead = Math.min(1, Math.max(0, int(input.lead_time_max_days ?? input.lead_time_days, 0)));
  return {
    title: String(input.title || '').trim(),
    author: String(input.author || '').trim(),
    description: String(input.desc ?? input.description ?? '').trim(),
    price: Math.max(0, int(input.price, 0)),
    stock_quantity: Math.max(0, int(input.stock_quantity, 0)),
    availability_type: input.availability_type === 'on_demand' ? 'on_demand' : 'in_stock',
    lead_time_min_days: lead,
    lead_time_max_days: lead,
    image_url: String(input.img ?? input.image_url ?? '').trim(),
    category_slug: input.category_slug ? String(input.category_slug) : (input.category_id ? String(input.category_id) : null),
    giftable: input.giftable === false ? 0 : 1,
    discoverable: input.discoverable === false ? 0 : 1,
    featured: input.featured ? 1 : 0,
    active: input.active === false ? 0 : 1,
    legacy_payload_json: JSON.stringify(input),
  };
}

async function verifyTurnstile(request: Request, env: Env): Promise<boolean> {
  if (!env.TURNSTILE_SECRET_KEY) return true;
  const token = request.headers.get('X-Turnstile-Token');
  if (!token) return false;
  const form = new FormData();
  form.append('secret', env.TURNSTILE_SECRET_KEY);
  form.append('response', token);
  const result = await fetch('https://challenges.cloudflare.com/turnstile/v0/siteverify', { method: 'POST', body: form });
  if (!result.ok) return false;
  const data = await result.json() as { success?: boolean };
  return data.success === true;
}

async function publicProducts(request: Request, env: Env): Promise<Response> {
  return response(await loadProducts(env), 200, request, env);
}

async function publicProduct(id: string, request: Request, env: Env): Promise<Response> {
  const row = await env.DB.prepare(`
    SELECT p.*, c.name AS category_name
    FROM products p LEFT JOIN categories c ON c.slug = p.category_slug WHERE p.id = ?1
  `).bind(id).first<ProductRow & { category_name: string | null }>();
  if (!row) return fail('Product not found', 404, request, env);
  const tags = await env.DB.prepare('SELECT tag FROM product_tags WHERE product_id = ?1 ORDER BY tag').bind(id).all<{ tag: string }>();
  return response(productJson(row, row.category_name, tags.results.map(item => item.tag)), 200, request, env);
}

async function discover(request: Request, env: Env): Promise<Response> {
  const input = await body(request);
  const missing = Object.entries(DISCOVERY_OPTIONS)
    .filter(([key, values]) => !values.has(String(input[key] || '')))
    .map(([key]) => key);
  if (missing.length) return fail('يرجى إكمال الاختيارات الثلاثة', 400, request, env, { fields: missing });

  const products = await loadProducts(env);
  const goal = String(input.goal);
  const mood = String(input.mood);
  const pace = String(input.pace);
  const keywords: Record<string, string[]> = {
    story: ['رواية', 'خيال', 'عالم', 'مغامرة', 'قصص'],
    growth: ['تطوير', 'نجاح', 'عادات', 'عمل', 'تحسين'],
    knowledge: ['تعلم', 'معرفة', 'تاريخ', 'فكر', 'علم'],
    escape: ['رواية', 'خيال', 'عالم', 'مغامرة', 'قصص'],
    mystery: ['غموض', 'جريمة', 'سر', 'تحقيق'],
    romance: ['حب', 'رومانسية', 'مشاعر', 'علاقة'],
    fantasy: ['خيال', 'مملكة', 'عالم', 'مخلوقات'],
    change: ['تغيير', 'تطوير', 'تحسين', 'تقدم'],
  };
  const ranked = products.map(product => {
    const text = `${product.title} ${product.desc} ${product.category} ${(product.discovery_tags as string[]).join(' ')}`;
    const goalHits = keywords[goal].filter(word => text.includes(word));
    const moodHits = keywords[mood].filter(word => text.includes(word));
    const score = goalHits.length * 1.2 + moodHits.length * 1.6 + (pace === 'quick' ? Math.max(0, 2.5 - String(product.desc).length / 500) : Math.min(2.5, String(product.desc).length / 500));
    const reasons = [] as string[];
    if (goalHits.length) reasons.push('يلتقي مع رغبتك في هذا النوع من القراءة');
    if (moodHits.length) reasons.push('يحمل نبرة قريبة من مزاجك');
    reasons.push(pace === 'quick' ? 'مناسب لبداية خفيفة وسريعة' : 'يمنحك مساحة أكبر للتفاصيل والاندماج');
    return { score, product, reason: reasons.join('، ') };
  }).sort((a, b) => b.score - a.score || String(a.product.title).localeCompare(String(b.product.title), 'ar'));
  return response({ recommendations: ranked.slice(0, 3).map(item => ({ ...item.product, reason: item.reason })) }, 200, request, env);
}

async function createOrder(request: Request, env: Env): Promise<Response> {
  if (!(await verifyTurnstile(request, env))) return fail('تعذر التحقق الأمني من الطلب', 403, request, env);
  const input = await body(request);
  const customer = input.customer && typeof input.customer === 'object' ? input.customer : {};
  const rawCart = Array.isArray(input.cart) ? input.cart : [];
  if (!rawCart.length || rawCart.length > 100) return fail('Cart is empty or too large', 400, request, env);

  const idempotencyKey = String(request.headers.get('Idempotency-Key') || input.idempotency_key || '').trim();
  if (idempotencyKey.length < 16 || idempotencyKey.length > 128) return fail('A valid Idempotency-Key is required', 400, request, env);
  const existing = await env.DB.prepare('SELECT id FROM orders WHERE idempotency_key = ?1').bind(idempotencyKey).first<{ id: string }>();
  if (existing) return response({ order_id: existing.id, reused: true }, 200, request, env);

  const itemIds = rawCart.map(item => String(item?.id || '')).filter(Boolean);
  if (new Set(itemIds).size !== itemIds.length) return fail('Duplicate product lines are not allowed', 400, request, env);
  const placeholders = itemIds.map(() => '?').join(',');
  const productResult = await env.DB.prepare(`SELECT p.*, c.name AS category_name FROM products p LEFT JOIN categories c ON c.slug = p.category_slug WHERE p.id IN (${placeholders})`).bind(...itemIds).all<ProductRow & { category_name: string | null }>();
  const productMap = new Map(productResult.results.map(item => [item.id, item]));

  const cart: Record<string, any>[] = [];
  for (const raw of rawCart) {
    const product = productMap.get(String(raw?.id || ''));
    const quantity = int(raw?.qty, 0);
    if (!product || !available(product)) return fail(`Product unavailable: ${String(raw?.id || '')}`, 400, request, env);
    if (quantity < 1 || quantity > 20) return fail('Invalid quantity', 400, request, env);
    if (product.availability_type === 'in_stock' && quantity > product.stock_quantity) return fail(`Insufficient stock: ${String(raw?.id || '')}`, 409, request, env);
    const purpose = String(raw?.purchase_purpose || (input.order_type === 'gift' ? 'gift' : 'personal'));
    if (!VALID_PURPOSES.has(purpose)) return fail('Invalid purchase purpose', 400, request, env);
    if (purpose === 'gift' && (!(await featureEnabled(env, 'gifts')) || product.giftable !== 1)) return fail('Gift order is unavailable for this product', 400, request, env);
    cart.push({ id: product.id, title: product.title, price: product.price, qty: quantity, img: product.image_url || '', availability_type: product.availability_type, lead_time_min_days: product.lead_time_min_days, lead_time_max_days: product.lead_time_max_days, lead_time_days: product.lead_time_max_days, purchase_purpose: purpose });
  }

  const giftItems = cart.filter(item => item.purchase_purpose === 'gift');
  const personalItems = cart.filter(item => item.purchase_purpose === 'personal');
  let gift: Record<string, any> | null = null;
  if (giftItems.length) {
    const rawGift = input.gift && typeof input.gift === 'object' ? input.gift : {};
    const recipientName = String(rawGift.recipient_name || '').trim();
    const recipientPhone = String(rawGift.recipient_phone || '').trim();
    if (!recipientName) return fail('Gift recipient name is required', 400, request, env);
    if (digits(recipientPhone).length < 8) return fail('Gift recipient phone is required', 400, request, env);
    const source = String(rawGift.source || 'cart');
    if (!VALID_GIFT_SOURCES.has(source)) return fail('Invalid gift source', 400, request, env);
    gift = { source, recipient_name: recipientName, recipient_phone: recipientPhone, recipient_type: String(rawGift.recipient_type || 'friend'), occasion: String(rawGift.occasion || 'general'), message: String(rawGift.message || '').trim(), budget: Math.max(0, int(rawGift.budget, 0)), mood: String(rawGift.mood || 'warm'), sender_name: String(rawGift.sender_name || customer.name || '').trim(), anonymous: Boolean(rawGift.anonymous), gift_item_ids: giftItems.map(item => item.id) };
  } else if (input.gift) return fail('Gift details require at least one gift item', 400, request, env);

  const wilayaNum = int(input.wilaya, 0);
  const deliveryType = String(input.delivery_type || 'stop_desk');
  if (!['stop_desk', 'domicile'].includes(deliveryType)) return fail('Invalid delivery type', 400, request, env);
  if (deliveryType === 'domicile' && !String(customer.address || '').trim()) return fail('Delivery address is required', 400, request, env);
  const delivery = await env.DB.prepare('SELECT * FROM delivery_fees WHERE region_number = ?1').bind(wilayaNum).first<DeliveryRow>();
  const deliveryColumn = deliveryType === 'domicile' ? 'domicile_fee' : 'stop_desk_fee';
  if (!delivery || int(delivery[deliveryColumn], -1) < 0) return fail('Delivery unavailable', 400, request, env);
  const subtotal = cart.reduce((sum, item) => sum + Number(item.price) * Number(item.qty), 0);
  const fee = int(delivery[deliveryColumn], 0);
  const total = subtotal + fee;
  const hasOnDemand = cart.some(item => item.availability_type === 'on_demand');
  const orderType = giftItems.length && personalItems.length ? 'mixed' : giftItems.length ? 'gift' : hasOnDemand ? 'on_demand' : 'standard';
  const onDemandItems = cart.filter(item => item.availability_type === 'on_demand');
  const minLead = onDemandItems.length ? Math.max(...onDemandItems.map(item => item.lead_time_min_days)) : 0;
  const maxLead = onDemandItems.length ? Math.max(...onDemandItems.map(item => item.lead_time_max_days)) : 0;
  const fulfillmentNote = onDemandItems.length ? `يشحن الطلب كاملًا بعد توفير الكتب المطلوبة؛ المدة المتوقعة ${minLead}–${maxLead} يومًا.` : 'جميع الكتب متوفرة من المخزون.';
  const orderId = `ORD-${crypto.randomUUID().slice(0, 8).toUpperCase()}`;
  const now = new Date().toISOString();
  const orderJson = { order_id: orderId, timestamp: now, customer_name: String(customer.name || ''), phone: String(customer.phone || ''), address: String(customer.address || '—'), wilaya: delivery.region_name, delivery_type: deliveryType, items: cart, personal_items: personalItems, gift_items: giftItems, order_type: orderType, gift, subtotal, delivery_fee: fee, total, status: 'new', fulfillment_note: fulfillmentNote, shipping_policy: 'ship_together' };

  const statements: D1PreparedStatement[] = [
    env.DB.prepare(`INSERT INTO orders (id, legacy_order_id, status, customer_name, phone, address, wilaya, delivery_type, delivery_fee, order_type, shipping_policy, fulfillment_note, subtotal, total, source_timestamp, idempotency_key, legacy_payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(orderId, orderId, 'new', String(customer.name || ''), String(customer.phone || ''), String(customer.address || '—'), delivery.region_name, deliveryType, fee, orderType, 'ship_together', fulfillmentNote, subtotal, total, now, idempotencyKey, JSON.stringify(orderJson)),
  ];
  for (const item of cart) {
    const product = productMap.get(item.id)!;
    if (product.availability_type === 'in_stock') {
      statements.push(env.DB.prepare('UPDATE products SET stock_quantity = stock_quantity - ? WHERE id = ? AND stock_quantity >= ?').bind(item.qty, item.id, item.qty));
    }
    statements.push(env.DB.prepare('INSERT INTO order_items (order_id, line_number, product_id, item_role, title_snapshot, image_snapshot, price_snapshot, quantity, purchase_purpose, availability_type, lead_time_min_days, lead_time_max_days, legacy_payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)').bind(orderId, cart.indexOf(item) + 1, item.id, item.purchase_purpose, item.title, item.img, item.price, item.qty, item.purchase_purpose, item.availability_type, item.lead_time_min_days, item.lead_time_max_days, JSON.stringify(item)));
  }
  if (gift) statements.push(env.DB.prepare('INSERT INTO order_gifts (order_id, source, sender_name, recipient_name, recipient_phone, recipient_type, message, occasion, mood, budget, anonymous, gift_item_ids_json, legacy_payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)').bind(orderId, gift.source, gift.sender_name, gift.recipient_name, gift.recipient_phone, gift.recipient_type, gift.message, gift.occasion, gift.mood, gift.budget, gift.anonymous ? 1 : 0, JSON.stringify(gift.gift_item_ids), JSON.stringify(gift)));
  try {
    await env.DB.batch(statements);
  } catch {
    return fail('تعذر إنشاء الطلب، لم يتم حفظه', 500, request, env);
  }
  return response({ order_id: orderId }, 201, request, env);
}

async function adminRoute(request: Request, env: Env, path: string): Promise<Response> {
  if (!adminAuthorized(request, env)) return fail('Unauthorized', 401, request, env);
  const method = request.method;
  if (path === '/api/admin/products' && method === 'GET') return response(await loadProducts(env, true), 200, request, env);
  if (path === '/api/admin/categories' && method === 'GET') {
    const rows = await env.DB.prepare('SELECT * FROM categories ORDER BY name COLLATE NOCASE').all<CategoryRow>();
    return response(rows.results.map(row => row.name), 200, request, env);
  }
  if (path === '/api/admin/delivery-fees' && method === 'GET') {
    const rows = await env.DB.prepare('SELECT * FROM delivery_fees ORDER BY region_number').all<DeliveryRow>();
    return response(rows.results.map(row => ({ num: row.region_number, name: row.region_name, stop_desk: row.stop_desk_fee, domicile: row.domicile_fee })), 200, request, env);
  }
  if (path === '/api/admin/orders' && method === 'GET') {
    const rows = await env.DB.prepare('SELECT * FROM orders ORDER BY created_at DESC').all<OrderRow>();
    const items = await env.DB.prepare('SELECT * FROM order_items ORDER BY order_id, line_number').all<Record<string, any>>();
    const gifts = await env.DB.prepare('SELECT * FROM order_gifts').all<Record<string, any>>();
    const itemMap = new Map<string, any[]>();
    for (const item of items.results) itemMap.set(item.order_id, [...(itemMap.get(item.order_id) || []), { id: item.product_id, title: item.title_snapshot, img: item.image_snapshot, price: item.price_snapshot, qty: item.quantity, purchase_purpose: item.purchase_purpose, availability_type: item.availability_type }]);
    const giftMap = new Map(gifts.results.map(gift => [gift.order_id, gift]));
    return response(rows.results.map(order => ({ order_id: order.id, timestamp: order.source_timestamp || order.created_at, customer_name: order.customer_name, phone: order.phone, address: order.address, wilaya: order.wilaya, delivery_type: order.delivery_type, order_type: order.order_type, items: itemMap.get(order.id) || [], gift: giftMap.get(order.id) || null, subtotal: order.subtotal, delivery_fee: order.delivery_fee, total: order.total, status: order.status, fulfillment_note: order.fulfillment_note, shipping_policy: order.shipping_policy })), 200, request, env);
  }
  if (path === '/api/settings' && method === 'GET') return response(await settings(env), 200, request, env);
  if (path === '/api/admin/settings' && method === 'GET') return response(await settings(env), 200, request, env);
  if (path === '/api/admin/settings' && method === 'PUT') {
    const input = await body(request);
    const features = input.features && typeof input.features === 'object' ? input.features : {};
    const statements = Object.entries(features).map(([key, value]) => env.DB.prepare('INSERT INTO feature_flags (key, enabled) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET enabled = excluded.enabled').bind(key, value ? 1 : 0));
    if (statements.length) await env.DB.batch(statements);
    return response(await settings(env), 200, request, env);
  }
  if (path === '/api/admin/upload-image' && method === 'POST') return uploadImage(request, env);
  if (path.startsWith('/api/admin/products/') && method === 'PUT') return saveProduct(request, env, path.split('/').pop() || '');
  if (path.startsWith('/api/admin/products/') && method === 'DELETE') return archiveProduct(request, env, path.split('/').pop() || '');
  if (path === '/api/admin/products' && method === 'POST') return saveProduct(request, env, '');
  if (path.startsWith('/api/admin/orders/') && method === 'PUT') {
    const id = path.split('/').pop() || '';
    const input = await body(request);
    const status = String(input.status || '');
    if (!['new', 'confirmed', 'processing', 'delivered', 'cancelled'].includes(status)) return fail('Invalid order status', 400, request, env);
    const result = await env.DB.prepare('UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? OR legacy_order_id = ?').bind(status, id, id).run();
    return response({ updated: result.meta.changes }, 200, request, env);
  }
  return fail('Admin route not found', 404, request, env);
}

async function settings(env: Env): Promise<Record<string, unknown>> {
  const rows = await env.DB.prepare('SELECT key, enabled FROM feature_flags ORDER BY key').all<FeatureRow>();
  return { features: Object.fromEntries(rows.results.map(row => [row.key, row.enabled === 1])) };
}

async function saveProduct(request: Request, env: Env, id: string): Promise<Response> {
  const input = cleanProductInput(await body(request));
  if (!input.title || !input.author || input.price < 0) return fail('Invalid product data', 400, request, env);
  const productId = id || String((await body(request)).id || crypto.randomUUID());
  await env.DB.prepare(`INSERT INTO products (id, legacy_id, category_slug, title, description, image_url, price, stock_quantity, availability_type, lead_time_min_days, lead_time_max_days, lead_time_days, active, featured, giftable, discoverable, archived, legacy_payload_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?) ON CONFLICT(id) DO UPDATE SET category_slug=excluded.category_slug, title=excluded.title, description=excluded.description, image_url=excluded.image_url, price=excluded.price, stock_quantity=excluded.stock_quantity, availability_type=excluded.availability_type, lead_time_min_days=excluded.lead_time_min_days, lead_time_max_days=excluded.lead_time_max_days, lead_time_days=excluded.lead_time_days, active=excluded.active, featured=excluded.featured, giftable=excluded.giftable, discoverable=excluded.discoverable, legacy_payload_json=excluded.legacy_payload_json, updated_at=CURRENT_TIMESTAMP`).bind(productId, productId, input.category_slug || 'غير-مصنف', input.title, input.description, input.image_url, input.price, input.stock_quantity, input.availability_type, input.lead_time_min_days, input.lead_time_max_days, input.lead_time_max_days, input.active, input.featured, input.giftable, input.discoverable, input.legacy_payload_json).run();
  return response({ id: productId }, 200, request, env);
}

async function archiveProduct(request: Request, env: Env, id: string): Promise<Response> {
  const result = await env.DB.prepare('UPDATE products SET archived = 1, active = 0 WHERE id = ?').bind(id).run();
  return response({ deleted: result.meta.changes }, 200, request, env);
}

async function uploadImage(request: Request, env: Env): Promise<Response> {
  if (!env.LIBRARY_BUCKET) return fail('Image library is not configured', 503, request, env);
  const form = await request.formData();
  const file = form.get('file');
  if (!(file instanceof File)) return fail('Image file is required', 400, request, env);
  if (!file.type.startsWith('image/') || file.size > 10 * 1024 * 1024) return fail('Unsupported image or size exceeds 10MB', 400, request, env);
  const ext = file.type.split('/')[1] || 'bin';
  const key = `library/${new Date().toISOString().slice(0, 10)}/${crypto.randomUUID()}.${ext}`;
  await env.LIBRARY_BUCKET.put(key, file.stream(), { httpMetadata: { contentType: file.type } });
    await env.DB.prepare('INSERT INTO image_assets (id, storage_key, original_name, mime_type, size_bytes, archived) VALUES (?, ?, ?, ?, ?, 0)').bind(crypto.randomUUID(), key, file.name, file.type, file.size).run();
  return response({ key }, 201, request, env);
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(request, env) });
    const url = new URL(request.url);
    try {
      if (url.pathname === '/api/products' && request.method === 'GET') return publicProducts(request, env);
      if (url.pathname.startsWith('/api/products/') && request.method === 'GET') return publicProduct(url.pathname.split('/').pop() || '', request, env);
      if (url.pathname === '/api/categories' && request.method === 'GET') {
        const rows = await env.DB.prepare('SELECT * FROM categories WHERE active = 1 ORDER BY name COLLATE NOCASE').all<CategoryRow>();
        return response(rows.results, 200, request, env);
      }
      if (url.pathname === '/api/delivery-fees' && request.method === 'GET') {
        const rows = await env.DB.prepare('SELECT * FROM delivery_fees ORDER BY region_number').all<DeliveryRow>();
        return response(rows.results, 200, request, env);
      }
      if (url.pathname === '/api/settings' && request.method === 'GET') return response(await settings(env), 200, request, env);
      if (url.pathname === '/api/discover' && request.method === 'POST') return discover(request, env);
      if (url.pathname === '/api/orders' && request.method === 'POST') return createOrder(request, env);
      if (url.pathname.startsWith('/api/admin/')) return adminRoute(request, env, url.pathname);
      return fail('Not found', 404, request, env);
    } catch (error) {
      console.error(error);
      return fail('Internal server error', 500, request, env);
    }
  },
};
