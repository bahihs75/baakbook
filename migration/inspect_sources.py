import json
from pathlib import Path

paths = [Path('/home/ubuntu/upload/data.json'), Path('/home/ubuntu/baakbook-local/data.json')]
for path in paths:
    data = json.loads(path.read_text(encoding='utf-8'))
    products = data.get('products', [])
    orders = data.get('orders', [])
    item_keys = sorted({key for order in orders if isinstance(order, dict) for item in (order.get('items') or []) if isinstance(item, dict) for key in item})
    product_ids = [str(item.get('id', '')) for item in products if isinstance(item, dict)]
    order_times = [str(order.get('timestamp', '')) for order in orders if isinstance(order, dict) and order.get('timestamp')]
    print(f'FILE={path}')
    print(f'BYTES={path.stat().st_size}')
    print(f'PRODUCTS={len(products)} CATEGORIES={len(data.get("categories", []))} DELIVERY_FEES={len(data.get("delivery_fees", []))} ORDERS={len(orders)}')
    print(f'FIRST_PRODUCT_IDS={product_ids[:8]}')
    print(f'ITEM_KEYS={item_keys}')
    print(f'ORDER_TIMESTAMPS_MIN={min(order_times) if order_times else ""} ORDER_TIMESTAMPS_MAX={max(order_times) if order_times else ""}')
    print(f'ORDER_IDS={[str(order.get("order_id", "")) for order in orders if isinstance(order, dict)]}')
    print()

upload = json.loads(paths[0].read_text(encoding='utf-8'))
local = json.loads(paths[1].read_text(encoding='utf-8'))
upload_ids = {str(item.get('id', '')) for item in upload.get('products', []) if isinstance(item, dict)}
local_ids = {str(item.get('id', '')) for item in local.get('products', []) if isinstance(item, dict)}
print(f'PRODUCT_IDS_ONLY_UPLOAD={sorted(upload_ids - local_ids)}')
print(f'PRODUCT_IDS_ONLY_LOCAL={sorted(local_ids - upload_ids)}')
