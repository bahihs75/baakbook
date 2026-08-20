from pathlib import Path
import re
import sys

root = Path('/home/ubuntu/baakbook-local')
admin = (root / 'frontend/admin.html').read_text(encoding='utf-8')
rules = (root / 'firestore.rules').read_text(encoding='utf-8')
errors = []
checks = []

def require(label, pattern, text=admin):
    if re.search(pattern, text, re.S):
        checks.append(label)
    else:
        errors.append(label)

require('media tab', r'data-tab="media"')
require('media panel', r'id="panel-media"')
require('ImgBB upload endpoint', r'https://api\.imgbb\.com/1/upload\?key=')
require('file input', r'id="mediaFileInput"')
require('upload button', r'id="uploadMediaBtn"')
require('media library Firestore collection', r"collection\(db, ['\"]imageLibrary['\"]\)")
require('admin secret storage', r"doc\(db, ['\"]adminSecrets['\"], ['\"]imgbb['\"]\)")
require('product picker', r'id="pickProdImage"')
require('hero picker', r'class="btn-secondary pick-hero-image"')
require('picker modal', r'id="mediaPickerModal"')
require('SVG safety validation', r"<script\|foreignObject\|javascript:")
require('file size validation', r'12 \* 1024 \* 1024')
require('image compression', r'canvas\.toBlob')
require('single modal close delegation', r"\['productModal', 'categoryModal', 'orderDetailModal', 'mediaPickerModal'\]")
require('product edit direct Firestore read', r"async function findProductSnapshot\(id\).*?getDoc\(doc\(db, 'products', id\)\).*?where\('id', '==', id\)")
require('category editing state', r'let editingCategoryName = null')

if 'match /imageLibrary/{imageId}' not in rules:
    errors.append('imageLibrary rules')
else:
    checks.append('imageLibrary rules')
if 'match /adminSecrets/{secretId}' not in rules:
    errors.append('adminSecrets rules')
else:
    checks.append('adminSecrets rules')

# ImgBB keys must never be hard-coded into source files.
# Detect a 32-character hexadecimal secret in the admin/rules source without
# storing the supplied key in this repository.
secret_like = re.compile(r"['\"]([a-f0-9]{32})['\"]", re.I)
if secret_like.search(admin) or secret_like.search(rules):
    errors.append('ImgBB-like secret leaked into source')
else:
    checks.append('ImgBB key absent from source')

# Detect duplicate assignment of window.onclick, which previously caused modal conflicts.
if re.search(r'window\.onclick\s*=', admin):
    errors.append('duplicate window.onclick remains')
else:
    checks.append('no window.onclick conflict')

print(f'CHECKS_PASSED={len(checks)}')
for check in checks:
    print(f'PASS {check}')
if errors:
    print(f'CHECKS_FAILED={len(errors)}')
    for error in errors:
        print(f'FAIL {error}')
    sys.exit(1)
print('STATUS=PASS')
