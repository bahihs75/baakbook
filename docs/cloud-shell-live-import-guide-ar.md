# دليل ترحيل Baak Books إلى Firestore عبر جهازك

هذا الدليل يستخدم مشروع Firebase الصحيح `baakbook-77c00`، ولا يحتاج إلى Service Account أو كلمة مرور أو مفتاح إداري محفوظ في GitHub. سنبدأ بخطة قراءة/تحقق فقط، ثم نتوقف قبل الكتابة الإنتاجية حتى تُراجع النتيجة.

## المرحلة 1: فتح Cloud Shell

من جهازك الشخصي افتح:

```text
https://console.firebase.google.com/project/baakbook-77c00/overview
```

تأكد من ظهور الحساب `baakbook01@gmail.com` والمشروع `baakbook-77c00`. اضغط **Activate Cloud Shell** وانتظر حتى تظهر الطرفية بحالة جاهزة.

لا تنشئ مشروعًا جديدًا.

## المرحلة 2: جلب كود الترحيل

داخل Cloud Shell نفّذ:

```bash
git clone https://github.com/bahihs75/baakbook.git
cd baakbook
mkdir -p migration/sources migration/reports
```

إذا ظهرت رسالة أن المجلد موجود، نفّذ بدلًا من ذلك:

```bash
cd baakbook
git pull --ff-only origin main
mkdir -p migration/sources migration/reports
```

## المرحلة 3: رفع ملف البيانات

من شريط Cloud Shell اختر **More / ⋮ → Upload file**، ثم ارفع نسخة `data.json` التي تريد نقلها. بعد الرفع نفّذ:

```bash
mv ~/data.json migration/sources/baakbook-live.json
wc -c migration/sources/baakbook-live.json
```

إذا رفع Cloud Shell الملف باسم مختلف، اعرض الملفات فقط ثم استخدم اسمه الصحيح:

```bash
ls -lh ~
```

لا تحذف أو تعدّل الملف الأصلي على PythonAnywhere.

## المرحلة 4: رفع محوّل المخطط القديم

من **Upload file** ارفع الملف المرفق `normalize_legacy_export.py` إلى المجلد الرئيسي في Cloud Shell، ثم نفّذ:

```bash
python3 normalize_legacy_export.py \
  migration/sources/baakbook-live.json \
  migration/sources/baakbook-live.normalized.json
```

المحوّل يضيف `id` إلى عناصر الطلب التي تحتوي على `product_id` داخل نسخة جديدة فقط؛ لا يغيّر ملف المصدر.

## المرحلة 5: إنشاء خطة فقط

نفّذ:

```bash
python3 migration/firestore_import.py \
  --source migration/sources/baakbook-live.normalized.json \
  --report-root migration/reports \
  --batch-id migration-live-preflight-20260820 \
  --target rest \
  --project baakbook-77c00
```

يجب أن تظهر رسالة شبيهة بـ:

```text
PLAN ONLY: 87 documents
```

وتوقّع الأعداد التالية:

| المجموعة | العدد المتوقع |
|---|---:|
| `products` | 22 |
| `categories` | 4 |
| `deliveryFees` | 58 |
| `orders` | 1 |
| `settings` | 1 |
| `migrationMetadata` | 1 |
| **الإجمالي** | **87** |

## المرحلة 6: التحقق المستقل من الخطة

نفّذ:

```bash
python3 migration/verify_firestore_plan.py \
  migration/sources/baakbook-live.normalized.json \
  migration/reports/migration-live-preflight-20260820/firestore-import.ndjson \
  migration/reports/cloudshell-plan-verify.json
```

يجب أن تكون النتيجة `verified`، مع عدم وجود أخطاء أو فروق.

**توقف هنا وأرسل لي ناتج الأمرين الأخيرين.** لا تنفّذ أمر `--apply` قبل أن أراجع الأعداد والبصمة.

## المرحلة 7: الكتابة الإنتاجية — بعد المراجعة فقط

بعد مراجعة الخطة، سنستخدم جلسة Google المؤقتة داخل Cloud Shell:

```bash
export FIRESTORE_ACCESS_TOKEN="$(gcloud auth print-access-token)"
test -n "$FIRESTORE_ACCESS_TOKEN"
```

ثم أمر الكتابة:

```bash
python3 migration/firestore_import.py \
  --source migration/sources/baakbook-live.normalized.json \
  --report-root migration/reports \
  --batch-id migration-live-preflight-20260820 \
  --target rest \
  --project baakbook-77c00 \
  --apply \
  --confirm-live
```

المستورد محمي بحيث يرفض أي وثيقة موجودة مسبقًا بدل استبدالها. لا تستخدم `--allow-existing` مع الهدف الإنتاجي.

## المرحلة 8: التحقق بعد الكتابة

بعد نجاح الاستيراد سنقرأ الوثائق ونختبر:

```text
https://baakbook.pages.dev/
https://baakbook.pages.dev/api/products
https://baakbook.pages.dev/api/categories
https://baakbook.pages.dev/api/delivery-fees
```

ثم نتحقق من أن لوحة الإدارة تستخدم تسجيل الدخول عبر Firebase وأن الحساب الإداري هو `baakbook01@gmail.com`.

## تحذيرات مهمة

لا ترسل كلمة مرور Google أو رمز تحقق أو Service Account JSON في المحادثة. لا ترفع `data.json` إلى GitHub. لا تنفّذ `--apply` على أي مشروع غير `baakbook-77c00`. لا نعدّل PythonAnywhere أثناء هذه العملية.
