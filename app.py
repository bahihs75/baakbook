# -*- coding: utf-8 -*-
import datetime
import json
import os
from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=BASE_DIR, static_url_path='')
CORS(app)

# Runtime configuration comes from the hosting environment rather than source control.
DATA_FILE = os.environ.get('DATA_FILE', os.path.join(BASE_DIR, 'data.json'))

DEFAULT_SETTINGS = {
    'features': {
        'discovery': True,
        'gifts': True,
        'gift_from_product': True,
        'gift_from_cart': True,
        'gift_finder': True,
        'on_demand': True,
        'dark_mode': True,
        'community': False,
        'smart_search': False,
        'ideas_lab': True,
    }
}

ORDER_STATUSES = {
    'new', 'confirmed', 'awaiting_supply', 'processing', 'ready_to_ship',
    'shipped', 'delivered', 'cancelled', 'returned',
    # قيم قديمة محفوظة في data.json قبل توسيع دورة الحالات.
    'New', 'Processing', 'Delivered'
}

VALID_AVAILABILITY_TYPES = {'in_stock', 'on_demand'}
VALID_PURPOSES = {'personal', 'gift'}
VALID_GIFT_SOURCES = {'product_card', 'cart', 'gift_finder'}


def _int_value(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _tags_value(value):
    if isinstance(value, str):
        return [tag.strip() for tag in value.split(',') if tag.strip()]
    if isinstance(value, list):
        return [str(tag).strip() for tag in value if str(tag).strip()]
    return []


def normalize_product(product):
    """Migrate old catalog records to the explicit product contract."""
    product.setdefault('active', True)
    product.setdefault('stock_quantity', 0)
    product.setdefault('availability_type', 'in_stock')
    product.setdefault('featured', False)
    product.setdefault('giftable', True)
    product.setdefault('discoverable', True)
    product['discovery_tags'] = _tags_value(product.get('discovery_tags', []))
    product['gift_tags'] = _tags_value(product.get('gift_tags', []))
    old_lead = _int_value(product.get('lead_time_days', 0), 0)
    product.setdefault('lead_time_min_days', old_lead)
    product.setdefault('lead_time_max_days', old_lead)
    product['lead_time_min_days'] = min(1, max(0, _int_value(product.get('lead_time_min_days'), old_lead)))
    product['lead_time_max_days'] = min(1, max(product['lead_time_min_days'], _int_value(product.get('lead_time_max_days'), old_lead)))
    # Keep the legacy field for old clients and old data exports.
    product['lead_time_days'] = product['lead_time_max_days']
    return product


def lead_window(payload):
    """Read the explicit min/max window, accepting the old single-day field."""
    legacy = _int_value(payload.get('lead_time_days', 0), 0)
    minimum = _int_value(payload.get('lead_time_min_days', legacy), legacy)
    maximum = _int_value(payload.get('lead_time_max_days', legacy), legacy)
    minimum = min(1, max(0, minimum))
    maximum = min(1, max(minimum, maximum))
    return minimum, maximum

# ------------------------- دوال التحميل والحفظ -------------------------
def load_data():
    """تحميل البيانات من الملف، أو إرجاع القيم الافتراضية إذا لم يوجد"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return (
                data.get('products', []),
                data.get('categories', ['روايات']),
                data.get('delivery_fees', []),
                data.get('orders', []),
                data.get('next_order_id', 1),
                data.get('settings', DEFAULT_SETTINGS)
            )
    # قيم افتراضية لأول تشغيل – الأسعار صحيحة الآن
    return (
        [
            {'id': 'bk001', 'title': 'قواعد جارتين', 'category': 'روايات', 'desc': 'ماذا لو وجدت نفسك بأرضٍ أقصى ما يمكنك بلوغه بها هو خمسون عامًا ..', 'img': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQXtuCUwbjOMSvrUSoJ46PnB1f2Lg5uR0N1bxZtQ1_MnQ&s=10', 'price': 1200, 'stock_quantity': 10, 'active': True},
            {'id': 'bk002', 'title': 'دقات الشامو', 'category': 'روايات', 'desc': 'صارت الفوضى تعم كل شيء من حولنا...', 'img': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTi8pkJEcs_yob-O8p2lGzVJi1DFDSEGqeOe-VZOQIJRw&s=10', 'price': 1300, 'stock_quantity': 5, 'active': True},
            {'id': 'bk003', 'title': 'أمواج أكما', 'category': 'روايات', 'desc': 'كنت أظن أن تغيير القواعد يحتاج إلى القوة وحسب...', 'img': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQV2LKC-0hByQ4sngJFhFOZXjxGYJhHMiuE2XgUvUVPEA&s=10', 'price': 1400, 'stock_quantity': 7, 'active': True},
            {'id': 'bk004', 'title': 'متلازمة فريجولي', 'category': 'روايات', 'desc': 'نادر اخصائي نفسي تجبره ظروف الحياة...', 'img': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRGw5uVSSGRQow8Sxb5MTeIneed3ONpDHBOacdnIkwseQ&s=10', 'price': 1150, 'stock_quantity': 3, 'active': True},
            {'id': 'bk005', 'title': 'شمس منتصف الليل', 'category': 'روايات', 'desc': 'تحكي الرواية عن فتاة شقراء تدعى تالين...', 'img': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSI_7xZjznLC9j4zEGlBCk8gZliFOxlFwSAVCwGgLeYaw&s=10', 'price': 1250, 'stock_quantity': 4, 'active': True}
        ],
        ['روايات', 'تنمية بشرية', 'علوم', 'تاريخ'],
        [
            {'num': 1, 'name': 'أدرار', 'stop_desk': 1100, 'domicile': 1400},
            {'num': 2, 'name': 'الشلف', 'stop_desk': 500, 'domicile': 850},
            {'num': 3, 'name': 'الأغواط', 'stop_desk': 450, 'domicile': 850},
            {'num': 4, 'name': 'أم البواقي', 'stop_desk': 500, 'domicile': 850},
            {'num': 5, 'name': 'باتنة', 'stop_desk': 500, 'domicile': 850},
            {'num': 6, 'name': 'بجاية', 'stop_desk': 500, 'domicile': 850},
            {'num': 7, 'name': 'بسكرة', 'stop_desk': 600, 'domicile': 950},
            {'num': 8, 'name': 'بشار', 'stop_desk': 1100, 'domicile': 1400},
            {'num': 9, 'name': 'البليدة', 'stop_desk': 500, 'domicile': 850},
            {'num': 10, 'name': 'البويرة', 'stop_desk': 500, 'domicile': 850},
            {'num': 11, 'name': 'تمنراست', 'stop_desk': 1400, 'domicile': 1800},
            {'num': 12, 'name': 'تبسة', 'stop_desk': 600, 'domicile': 950},
            {'num': 13, 'name': 'تلمسان', 'stop_desk': 500, 'domicile': 850},
            {'num': 14, 'name': 'تيارت', 'stop_desk': 500, 'domicile': 850},
            {'num': 15, 'name': 'تيزي وزو', 'stop_desk': 500, 'domicile': 850},
            {'num': 16, 'name': 'الجزائر', 'stop_desk': 450, 'domicile': 850},
            {'num': 17, 'name': 'الجلفة', 'stop_desk': 500, 'domicile': 850},
            {'num': 18, 'name': 'جيجل', 'stop_desk': 500, 'domicile': 850},
            {'num': 19, 'name': 'سطيف', 'stop_desk': 500, 'domicile': 850},
            {'num': 20, 'name': 'سعيدة', 'stop_desk': 600, 'domicile': 900},
            {'num': 21, 'name': 'سكيكدة', 'stop_desk': 500, 'domicile': 850},
            {'num': 22, 'name': 'سيدي بلعباس', 'stop_desk': 500, 'domicile': 850},
            {'num': 23, 'name': 'عنابة', 'stop_desk': 500, 'domicile': 850},
            {'num': 24, 'name': 'قالمة', 'stop_desk': 600, 'domicile': 850},
            {'num': 25, 'name': 'قسنطينة', 'stop_desk': 500, 'domicile': 850},
            {'num': 26, 'name': 'المدية', 'stop_desk': 500, 'domicile': 850},
            {'num': 27, 'name': 'مستغانم', 'stop_desk': 500, 'domicile': 850},
            {'num': 28, 'name': 'المسيلة', 'stop_desk': 500, 'domicile': 850},
            {'num': 29, 'name': 'معسكر', 'stop_desk': 600, 'domicile': 900},
            {'num': 30, 'name': 'ورقلة', 'stop_desk': 800, 'domicile': 1100},
            {'num': 31, 'name': 'وهران', 'stop_desk': 500, 'domicile': 850},
            {'num': 32, 'name': 'البيض', 'stop_desk': 800, 'domicile': 1100},
            {'num': 33, 'name': 'إيليزي', 'stop_desk': 1700, 'domicile': 2200},
            {'num': 34, 'name': 'برج بوعريريج', 'stop_desk': 500, 'domicile': 850},
            {'num': 35, 'name': 'بومرداس', 'stop_desk': 500, 'domicile': 850},
            {'num': 36, 'name': 'الطارف', 'stop_desk': 600, 'domicile': 950},
            {'num': 37, 'name': 'تندوف', 'stop_desk': 1400, 'domicile': 1800},
            {'num': 38, 'name': 'تيسمسيلت', 'stop_desk': 500, 'domicile': 850},
            {'num': 39, 'name': 'الوادي', 'stop_desk': 800, 'domicile': 1100},
            {'num': 40, 'name': 'خنشلة', 'stop_desk': 600, 'domicile': 900},
            {'num': 41, 'name': 'سوق أهراس', 'stop_desk': 600, 'domicile': 900},
            {'num': 42, 'name': 'تيبازة', 'stop_desk': 500, 'domicile': 850},
            {'num': 43, 'name': 'ميلة', 'stop_desk': 500, 'domicile': 850},
            {'num': 44, 'name': 'عين الدفلى', 'stop_desk': 500, 'domicile': 850},
            {'num': 45, 'name': 'النعامة', 'stop_desk': 800, 'domicile': 1100},
            {'num': 46, 'name': 'عين تموشنت', 'stop_desk': 600, 'domicile': 900},
            {'num': 47, 'name': 'غرداية', 'stop_desk': 400, 'domicile': 500},
            {'num': 48, 'name': 'غليزان', 'stop_desk': 500, 'domicile': 850},
            {'num': 49, 'name': 'تيميمون', 'stop_desk': 1100, 'domicile': 1400},
            {'num': 50, 'name': 'برج باجي مختار', 'stop_desk': -1, 'domicile': -1},
            {'num': 51, 'name': 'أولاد جلال', 'stop_desk': 700, 'domicile': 1000},
            {'num': 52, 'name': 'بني عباس', 'stop_desk': 1100, 'domicile': 1400},
            {'num': 53, 'name': 'عين صالح', 'stop_desk': 1100, 'domicile': 1400},
            {'num': 54, 'name': 'عين قزام', 'stop_desk': 1700, 'domicile': 2000},
            {'num': 55, 'name': 'تقرت', 'stop_desk': 800, 'domicile': 1100},
            {'num': 56, 'name': 'جانت', 'stop_desk': 1700, 'domicile': 2000},
            {'num': 57, 'name': 'المغير', 'stop_desk': 800, 'domicile': 1100},
            {'num': 58, 'name': 'المنيعة', 'stop_desk': 1000, 'domicile': 1300}
        ],
        [],
        1,
        DEFAULT_SETTINGS
    )

def save_data():
    """حفظ جميع البيانات الحالية إلى الملف"""
    data = {
        'products': mock_products,
        'categories': categories,
        'delivery_fees': delivery_fees,
        'orders': orders,
        'next_order_id': next_order_id,
        'settings': settings
    }
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# تحميل البيانات عند بدء التشغيل
mock_products, categories, delivery_fees, orders, next_order_id, settings = load_data()
for _product in mock_products:
    normalize_product(_product)
settings = {**DEFAULT_SETTINGS, **(settings or {})}
settings['features'] = {**DEFAULT_SETTINGS['features'], **settings.get('features', {})}

# Set ADMIN_TOKEN in PythonAnywhere/Render/Railway environment variables.
# An empty value intentionally disables all admin requests until configured.
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '')

def product_is_available(product):
    """A product is sellable from stock or as a clearly labelled on-demand title."""
    if not product.get('active') or product.get('price', 0) <= 0:
        return False
    if product.get('availability_type', 'in_stock') == 'on_demand':
        return settings['features'].get('on_demand', True)
    return product.get('stock_quantity', 0) > 0


def format_price(val):
    if val is None or val <= 0:
        return None
    return f"{val:,}".replace(',', ' ') + ' د.ج'

# ------------------------- Public APIs -------------------------
@app.route('/api/products')
def get_products():
    active = [p for p in mock_products if product_is_available(p)]
    return jsonify(active)

@app.route('/api/products/<product_id>')
def get_product(product_id):
    p = next((p for p in mock_products if p['id'] == product_id), None)
    if not p or not product_is_available(p):
        abort(404)
    return jsonify(p)

@app.route('/api/categories')
def get_categories():
    return jsonify(categories)

@app.route('/api/delivery-fees')
def get_delivery_fees():
    return jsonify(delivery_fees)

# ------------------------- Discover Your Book -------------------------
DISCOVERY_OPTIONS = {
    'goal': {'story', 'growth', 'knowledge', 'escape'},
    'pace': {'quick', 'deep'},
    'mood': {'mystery', 'romance', 'fantasy', 'change'},
}

DISCOVERY_PROFILES = {
    'goal': {
        'story': {
            'label': 'حكاية تأخذك بعيدًا',
            'categories': {'روايات'},
            'keywords': {'رواية', 'قصة', 'شخصيات', 'أحداث'},
        },
        'growth': {
            'label': 'خطوة عملية إلى الأمام',
            'categories': {'تنمية بشرية'},
            'keywords': {'عادات', 'نجاح', 'تطوير', 'تحسين', 'صلاة'},
        },
        'knowledge': {
            'label': 'فكرة جديدة تتعلمها',
            'categories': {'علوم', 'تاريخ'},
            'keywords': {'علم', 'تاريخ', 'معرفة', 'مجتمع', 'اكتشاف'},
        },
        'escape': {
            'label': 'عالم مختلف تعيشه',
            'categories': {'روايات'},
            'keywords': {'خيال', 'مملكة', 'عالم', 'مخلوقات', 'مغامرة', 'ضباب'},
        },
    },
    'mood': {
        'mystery': {
            'label': 'الغموض والتشويق',
            'keywords': {'غموض', 'جريمة', 'قاتل', 'أسرار', 'سر', 'خطر', 'نفسي', 'اضطراب'},
        },
        'romance': {
            'label': 'الرومانسية والمشاعر',
            'keywords': {'حب', 'رومانسية', 'عاطفية', 'علاقة', 'حبيب', 'مشاعر'},
        },
        'fantasy': {
            'label': 'الخيال والعوالم غير المألوفة',
            'keywords': {'خيال', 'مملكة', 'مخلوقات', 'مصاص', 'ضباب', 'سحر', 'عالم'},
        },
        'change': {
            'label': 'التغيير والتحسن',
            'keywords': {'عادات', 'نجاح', 'تحسين', 'تطوير', 'حياة', 'عملية'},
        },
    },
}


def recommend_books(preferences):
    """Return up to three explainable recommendations from the active catalog."""
    goal = preferences['goal']
    pace = preferences['pace']
    mood = preferences['mood']
    goal_profile = DISCOVERY_PROFILES['goal'][goal]
    mood_profile = DISCOVERY_PROFILES['mood'][mood]
    candidates = [product for product in mock_products if product_is_available(product) and product.get('discoverable', True)]

    scored = []
    for product in candidates:
        title = str(product.get('title', ''))
        description = str(product.get('desc', ''))
        category = str(product.get('category', ''))
        tags = ' '.join(product.get('discovery_tags', []))
        searchable_text = f'{title} {description} {category} {tags}'
        score = 0.0
        matched_goal = []
        matched_mood = []

        if category in goal_profile['categories']:
            score += 6
            matched_goal.append(goal_profile['label'])
        for keyword in goal_profile['keywords']:
            if keyword in searchable_text:
                score += 1.2
                matched_goal.append(keyword)

        for keyword in mood_profile['keywords']:
            if keyword in searchable_text:
                score += 1.6
                matched_mood.append(keyword)

        description_size = len(description)
        if pace == 'quick':
            score += max(0, 2.5 - description_size / 500)
            pace_reason = 'مناسب لبداية خفيفة وسريعة'
        else:
            score += min(2.5, description_size / 500)
            pace_reason = 'يمنحك مساحة أكبر للتفاصيل والاندماج'

        reasons = []
        if matched_goal:
            reasons.append(f"يلتقي مع رغبتك في {goal_profile['label']}")
        if matched_mood:
            reasons.append(f"يحمل نبرة من {mood_profile['label']}")
        reasons.append(pace_reason)
        scored.append((score, product, '، '.join(dict.fromkeys(reasons))))

    scored.sort(key=lambda item: (-item[0], item[1].get('title', '')))
    return [
        {**product, 'reason': reason}
        for _, product, reason in scored[:3]
    ]


@app.route('/api/discover', methods=['POST'])
def discover_books():
    """Validate quiz answers and return explainable catalog recommendations."""
    data = request.get_json(silent=True) or {}
    missing = [key for key in DISCOVERY_OPTIONS if data.get(key) not in DISCOVERY_OPTIONS[key]]
    if missing:
        return jsonify({'error': 'يرجى إكمال الاختيارات الثلاثة', 'fields': missing}), 400
    return jsonify({'recommendations': recommend_books(data)})

@app.route('/api/orders', methods=['POST'])
def place_order():
    global next_order_id
    data = request.get_json(silent=True) or {}
    customer = data.get('customer', {}) or {}
    raw_cart = data.get('cart', [])
    if not raw_cart:
        return jsonify({'error': 'Cart is empty'}), 400

    cart = []
    legacy_gift_order = data.get('order_type') == 'gift' and bool(data.get('gift'))
    for raw_item in raw_cart:
        product_id = str(raw_item.get('id', ''))
        product = next((item for item in mock_products if item.get('id') == product_id), None)
        if not product or not product_is_available(product):
            return jsonify({'error': f'Product unavailable: {product_id}'}), 400
        quantity = _int_value(raw_item.get('qty', 1), 0)
        if quantity < 1 or quantity > 20:
            return jsonify({'error': 'Invalid quantity'}), 400
        purpose = raw_item.get('purchase_purpose', 'gift' if legacy_gift_order else 'personal')
        if purpose not in VALID_PURPOSES:
            return jsonify({'error': 'Invalid purchase purpose'}), 400
        if purpose == 'gift' and not settings['features'].get('gifts', True):
            return jsonify({'error': 'Gift orders are currently unavailable'}), 400
        if purpose == 'gift' and not product.get('giftable', True):
            return jsonify({'error': f'Product is not giftable: {product_id}'}), 400
        minimum, maximum = lead_window(product)
        cart.append({
            'id': product['id'], 'title': product.get('title', ''),
            'price': product.get('price', 0), 'qty': quantity,
            'img': product.get('img', ''),
            'availability_type': product.get('availability_type', 'in_stock'),
            'lead_time_min_days': minimum, 'lead_time_max_days': maximum,
            'lead_time_days': maximum, 'purchase_purpose': purpose,
        })

    gift_items = [item for item in cart if item['purchase_purpose'] == 'gift']
    personal_items = [item for item in cart if item['purchase_purpose'] == 'personal']
    gift = data.get('gift') if gift_items else None
    if gift_items:
        if not settings['features'].get('gifts', True):
            return jsonify({'error': 'Gift orders are currently unavailable'}), 400
        gift = gift or {}
        recipient_name = str(gift.get('recipient_name', '')).strip()
        recipient_phone = str(gift.get('recipient_phone', '')).strip()
        if not recipient_name:
            return jsonify({'error': 'Gift recipient name is required'}), 400
        if len(''.join(ch for ch in recipient_phone if ch.isdigit())) < 8:
            return jsonify({'error': 'Gift recipient phone is required'}), 400
        source = gift.get('source', 'cart')
        if source not in VALID_GIFT_SOURCES:
            return jsonify({'error': 'Invalid gift source'}), 400
        gift = {
            'source': source,
            'recipient_name': recipient_name,
            'recipient_phone': recipient_phone,
            'recipient_type': gift.get('recipient_type', 'friend'),
            'occasion': gift.get('occasion', 'general'),
            'message': str(gift.get('message', '')).strip(),
            'budget': _int_value(gift.get('budget', 0), 0),
            'mood': gift.get('mood', 'warm'),
            'sender_name': str(gift.get('sender_name', customer.get('name', ''))).strip(),
            'anonymous': bool(gift.get('anonymous', False)),
            'gift_item_ids': [item['id'] for item in gift_items],
        }
    elif data.get('gift'):
        return jsonify({'error': 'Gift details require at least one gift item'}), 400

    wilaya_num = _int_value(data.get('wilaya', 0), 0)
    delivery_type = data.get('delivery_type', 'stop_desk')
    if delivery_type not in {'stop_desk', 'domicile'}:
        return jsonify({'error': 'Invalid delivery type'}), 400
    if delivery_type == 'domicile' and not str(customer.get('address', '')).strip():
        return jsonify({'error': 'Delivery address is required'}), 400
    wilaya = next((w for w in delivery_fees if w['num'] == wilaya_num), None)
    if not wilaya or wilaya.get(delivery_type, -1) == -1:
        return jsonify({'error': 'Delivery unavailable'}), 400

    subtotal = sum(item['price'] * item['qty'] for item in cart)
    fee = wilaya[delivery_type]
    total = subtotal + fee
    has_on_demand = any(item.get('availability_type') == 'on_demand' for item in cart)
    if gift_items and personal_items:
        order_type = 'mixed'
    elif gift_items:
        order_type = 'gift'
    elif has_on_demand:
        order_type = 'on_demand'
    else:
        order_type = 'standard'
    on_demand_items = [item for item in cart if item.get('availability_type') == 'on_demand']
    if on_demand_items:
        minimum = max(item['lead_time_min_days'] for item in on_demand_items)
        maximum = max(item['lead_time_max_days'] for item in on_demand_items)
        fulfillment_note = f'يشحن الطلب كاملًا بعد توفير الكتب المطلوبة عند الطلب؛ المدة المتوقعة {minimum}–{maximum} يومًا.'
    else:
        fulfillment_note = 'جميع الكتب متوفرة من المخزون.'

    order = {
        'order_id': f"ORD-{next_order_id:04d}",
        'timestamp': datetime.datetime.now().isoformat(),
        'customer_name': customer.get('name', ''), 'phone': customer.get('phone', ''),
        'address': customer.get('address', '—'), 'wilaya': wilaya['name'],
        'delivery_type': delivery_type.replace('_', ' ').title(), 'items': cart,
        'personal_items': personal_items, 'gift_items': gift_items,
        'order_type': order_type, 'gift': gift,
        'fulfillment_note': fulfillment_note, 'shipping_policy': 'ship_together',
        'subtotal': subtotal, 'delivery_fee': fee, 'total': total,
        'status': 'new'
    }
    next_order_id += 1
    orders.append(order)
    save_data()
    return jsonify({'order_id': order['order_id']})

# ------------------------- Admin API (Protected) -------------------------
def check_admin(req):
    """Validate the bearer token used by the private administration API."""
    if not ADMIN_TOKEN:
        return False
    token = req.headers.get('Authorization', '').replace('Bearer ', '', 1).strip()
    return token == ADMIN_TOKEN

# Products CRUD
@app.route('/api/admin/products')
def admin_get_products():
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(mock_products)

@app.route('/api/admin/products', methods=['POST'])
def admin_add_product():
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    if not all(k in data for k in ['id', 'title', 'price']):
        return jsonify({'error': 'Missing required fields'}), 400
    if any(p['id'] == data['id'] for p in mock_products):
        return jsonify({'error': 'Product ID exists'}), 409
    availability_type = data.get('availability_type', 'in_stock')
    if availability_type not in VALID_AVAILABILITY_TYPES:
        return jsonify({'error': 'Invalid availability type'}), 400
    minimum, maximum = lead_window(data)
    if availability_type == 'on_demand' and maximum < minimum:
        return jsonify({'error': 'On-demand books require a valid lead-time window'}), 400
    new_prod = normalize_product({
        'id': data['id'], 'title': data['title'],
        'category': data.get('category', 'روايات'), 'desc': data.get('desc', ''),
        'img': data.get('img', ''), 'price': data['price'],
        'stock_quantity': _int_value(data.get('stock_quantity', 10), 10),
        'active': bool(data.get('active', True)), 'availability_type': availability_type,
        'lead_time_min_days': minimum, 'lead_time_max_days': maximum,
        'featured': bool(data.get('featured', False)),
        'giftable': bool(data.get('giftable', True)),
        'discoverable': bool(data.get('discoverable', True)),
        'discovery_tags': _tags_value(data.get('discovery_tags', [])),
        'gift_tags': _tags_value(data.get('gift_tags', [])),
    })
    mock_products.append(new_prod)
    save_data()
    return jsonify(new_prod), 201

@app.route('/api/admin/products/<product_id>', methods=['PUT'])
def admin_update_product(product_id):
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    p = next((p for p in mock_products if p['id'] == product_id), None)
    if not p:
        abort(404)
    data = request.get_json()
    if 'availability_type' in data and data['availability_type'] not in VALID_AVAILABILITY_TYPES:
        return jsonify({'error': 'Invalid availability type'}), 400
    if any(field in data for field in ['availability_type', 'lead_time_days', 'lead_time_min_days', 'lead_time_max_days']):
        candidate_type = data.get('availability_type', p.get('availability_type', 'in_stock'))
        minimum, maximum = lead_window({**p, **data})
        if candidate_type == 'on_demand' and maximum < minimum:
            return jsonify({'error': 'On-demand books require a valid lead-time window'}), 400
        p['lead_time_min_days'], p['lead_time_max_days'] = minimum, maximum
        p['lead_time_days'] = maximum
        p['availability_type'] = candidate_type
    for field in ['title', 'category', 'desc', 'img', 'price', 'stock_quantity', 'active', 'featured', 'giftable', 'discoverable']:
        if field in data:
            p[field] = data[field]
    if 'discovery_tags' in data:
        p['discovery_tags'] = _tags_value(data['discovery_tags'])
    if 'gift_tags' in data:
        p['gift_tags'] = _tags_value(data['gift_tags'])
    normalize_product(p)
    save_data()
    return jsonify(p)

@app.route('/api/admin/products/<product_id>', methods=['DELETE'])
def admin_delete_product(product_id):
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    global mock_products
    mock_products = [p for p in mock_products if p['id'] != product_id]
    save_data()
    return jsonify({'message': 'Deleted'}), 200

# Categories CRUD
@app.route('/api/admin/categories', methods=['GET'])
def admin_get_categories():
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(categories)

@app.route('/api/admin/categories', methods=['POST'])
def admin_add_category():
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    cat = data.get('name', '').strip()
    if not cat:
        return jsonify({'error': 'Category name required'}), 400
    if cat in categories:
        return jsonify({'error': 'Category exists'}), 409
    categories.append(cat)
    save_data()
    return jsonify({'name': cat}), 201

@app.route('/api/admin/categories/<name>', methods=['PUT'])
def admin_update_category(name):
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    if name not in categories:
        abort(404)
    data = request.get_json()
    new_name = data.get('name', '').strip()
    if not new_name:
        return jsonify({'error': 'New name required'}), 400
    if new_name in categories:
        return jsonify({'error': 'New name exists'}), 409
    idx = categories.index(name)
    categories[idx] = new_name
    for p in mock_products:
        if p['category'] == name:
            p['category'] = new_name
    save_data()
    return jsonify({'old': name, 'new': new_name})

@app.route('/api/admin/categories/<name>', methods=['DELETE'])
def admin_delete_category(name):
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    if name not in categories:
        abort(404)
    categories.remove(name)
    save_data()
    return jsonify({'message': f'Category {name} deleted'})

# Delivery Fees management
@app.route('/api/admin/delivery-fees', methods=['GET'])
def admin_get_delivery_fees():
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(delivery_fees)

@app.route('/api/admin/delivery-fees/<int:wilaya_num>', methods=['PUT'])
def admin_update_delivery_fee(wilaya_num):
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    w = next((w for w in delivery_fees if w['num'] == wilaya_num), None)
    if not w:
        abort(404)
    data = request.get_json()
    if 'stop_desk' in data:
        w['stop_desk'] = int(data['stop_desk'])
    if 'domicile' in data:
        w['domicile'] = int(data['domicile'])
    save_data()
    return jsonify(w)

# Feature controls
@app.route('/api/settings')
def get_settings():
    return jsonify(settings)

@app.route('/api/admin/settings', methods=['GET'])
def admin_get_settings():
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(settings)

@app.route('/api/admin/settings', methods=['PUT'])
def admin_update_settings():
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json(silent=True) or {}
    features = data.get('features', {})
    for key in DEFAULT_SETTINGS['features']:
        if key in features:
            settings['features'][key] = bool(features[key])
    save_data()
    return jsonify(settings)

# Orders management
@app.route('/api/admin/orders')
def admin_get_orders():
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(orders)

@app.route('/api/admin/orders/<order_id>', methods=['PUT'])
def admin_update_order(order_id):
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    order = next((o for o in orders if o['order_id'] == order_id), None)
    if not order:
        abort(404)
    data = request.get_json()
    if 'status' in data:
        if data['status'] not in ORDER_STATUSES:
            return jsonify({'error': 'Invalid order status'}), 400
        order['status'] = data['status']
        save_data()
        return jsonify(order)
    return jsonify({'error': 'Status field required'}), 400

@app.route('/api/admin/orders/<order_id>', methods=['DELETE'])
def admin_delete_order(order_id):
    if not check_admin(request):
        return jsonify({'error': 'Unauthorized'}), 401
    global orders
    orders = [o for o in orders if o['order_id'] != order_id]
    save_data()
    return jsonify({'message': 'Order deleted'}), 200

# ------------------------- Static Files -------------------------
@app.route('/')
def serve_store():
    return send_from_directory(BASE_DIR, 'store.html')

@app.route('/admin')
def serve_admin():
    return send_from_directory(BASE_DIR, 'admin.html')

if __name__ == '__main__':
    app.run()