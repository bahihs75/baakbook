import json
import sys
from pathlib import Path

source = Path(sys.argv[1])
target = Path(sys.argv[2])
data = json.loads(source.read_text(encoding='utf-8'))
if not isinstance(data, dict):
    raise SystemExit('source root must be an object')

changed = 0
orders = data.get('orders', [])
if not isinstance(orders, list):
    raise SystemExit('orders must be a list')

for order_index, order in enumerate(orders):
    if not isinstance(order, dict):
        raise SystemExit(f'order {order_index} must be an object')
    items = order.get('items', [])
    if not isinstance(items, list):
        raise SystemExit(f'order {order_index} items must be a list')
    for item_index, item in enumerate(items):
        if not isinstance(item, dict):
            raise SystemExit(f'order {order_index} item {item_index} must be an object')
        if not str(item.get('id', '')).strip() and str(item.get('product_id', '')).strip():
            item['id'] = str(item['product_id']).strip()
            changed += 1
        if not str(item.get('id', '')).strip():
            raise SystemExit(f'order {order_index} item {item_index} has no id or product_id')

target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'NORMALIZED_ITEMS={changed}')
print(f'SOURCE_BYTES={source.stat().st_size}')
print(f'TARGET_BYTES={target.stat().st_size}')
