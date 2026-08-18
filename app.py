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
                data.get('next_order_id', 1)
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
        1
    )

def save_data():
    """حفظ جميع البيانات الحالية إلى الملف"""
    data = {
        'products': mock_products,
        'categories': categories,
        'delivery_fees': delivery_fees,
        'orders': orders,
        'next_order_id': next_order_id
    }
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# تحميل البيانات عند بدء التشغيل
mock_products, categories, delivery_fees, orders, next_order_id = load_data()

# Set ADMIN_TOKEN in PythonAnywhere/Render/Railway environment variables.
# An empty value intentionally disables all admin requests until configured.
ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', '')

def format_price(val):
    if val is None or val <= 0:
        return None
    return f"{val:,}".replace(',', ' ') + ' د.ج'

# ------------------------- Public APIs -------------------------
@app.route('/api/products')
def get_products():
    active = [p for p in mock_products if p.get('active') and p.get('stock_quantity', 0) > 0]
    return jsonify(active)

@app.route('/api/products/<product_id>')
def get_product(product_id):
    p = next((p for p in mock_products if p['id'] == product_id), None)
    if not p:
        abort(404)
    return jsonify(p)

@app.route('/api/categories')
def get_categories():
    return jsonify(categories)

@app.route('/api/delivery-fees')
def get_delivery_fees():
    return jsonify(delivery_fees)

@app.route('/api/orders', methods=['POST'])
def place_order():
    global next_order_id
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data'}), 400

    customer = data.get('customer', {})
    cart = data.get('cart', [])
    wilaya_num = int(data.get('wilaya', 0))
    delivery_type = data.get('delivery_type', 'stop_desk')

    wilaya = next((w for w in delivery_fees if w['num'] == wilaya_num), None)
    if not wilaya or wilaya.get(delivery_type, -1) == -1:
        return jsonify({'error': 'Delivery unavailable'}), 400

    subtotal = sum(item['price'] * item['qty'] for item in cart)
    fee = wilaya[delivery_type]
    total = subtotal + fee

    order = {
        'order_id': f"ORD-{next_order_id:04d}",
        'timestamp': datetime.datetime.now().isoformat(),
        'customer_name': customer.get('name', ''),
        'phone': customer.get('phone', ''),
        'address': customer.get('address', '—'),
        'wilaya': wilaya['name'],
        'delivery_type': delivery_type.replace('_', ' ').title(),
        'items': cart,
        'subtotal': subtotal,
        'delivery_fee': fee,
        'total': total,
        'status': 'New'
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
    new_prod = {
        'id': data['id'],
        'title': data['title'],
        'category': data.get('category', 'روايات'),
        'desc': data.get('desc', ''),
        'img': data.get('img', ''),
        'price': data['price'],
        'stock_quantity': data.get('stock_quantity', 10),
        'active': data.get('active', True)
    }
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
    for field in ['title', 'category', 'desc', 'img', 'price', 'stock_quantity', 'active']:
        if field in data:
            p[field] = data[field]
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