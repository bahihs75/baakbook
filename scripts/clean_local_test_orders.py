import json
from pathlib import Path

path = Path('/home/ubuntu/baakbook-local/data.json')
data = json.loads(path.read_text(encoding='utf-8'))
orders = data.get('orders', [])
for order in orders:
    if order.get('phone') != '0550000000' or 'اختبار' not in str(order.get('customer_name', '')):
        raise SystemExit(f"رفض التنظيف: سجل غير اختباري: {order.get('order_id')}")
data['orders'] = []
data['next_order_id'] = 1
path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('تم حذف سجلات الاختبار الأربعة فقط وإعادة عداد الطلبات المحلي إلى 1.')
