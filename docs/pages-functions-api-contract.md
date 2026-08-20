# عقد API لنسخة Cloudflare Pages

هذا الملف يصف طبقة Pages Functions الموجودة داخل `frontend/functions/`. الهدف في مرحلة الترحيل هو الحفاظ على مسارات الواجهة الحالية (`/api/...`) مع فصل العمليات الحساسة عن القراءة العامة. لا تُعد هذه الوثيقة موافقة على النشر أو على استيراد البيانات.

## الحدود المعمارية

| الطبقة | المسؤولية | مصدر الحقيقة |
|---|---|---|
| واجهة Pages | عرض الكتب، السلة، الإهداء، الاكتشاف، ولوحة الإدارة | ملفات `frontend/*.html` |
| Pages Functions | HTTP، CORS، request ID، القراءة العامة، تفويض العمليات الحساسة | `frontend/functions/` |
| Firestore | المنتجات، التصنيفات، الطلبات، رسوم التوصيل، الإعدادات | Firebase project `baakbook-77c00` بعد الاعتماد |
| Firebase Functions | إعادة حساب السعر، التحقق من المخزون، إنشاء الطلب، وعمليات الإدارة | خدمة موثوقة خارج المتصفح |
| PythonAnywhere | النسخة الحالية وخطة الرجوع | لا تعديل أثناء التطوير |

## المسارات العامة

| المسار | الطريقة | المصادقة | الوصف |
|---|---:|---|---|
| `/api/products` | `GET` | عامة | الكتب النشطة، بحد أقصى 100 نتيجة |
| `/api/products/:id` | `GET` | عامة | كتاب واحد نشط |
| `/api/categories` | `GET` | عامة | التصنيفات النشطة |
| `/api/delivery-fees` | `GET` | عامة | رسوم التوصيل |
| `/api/settings` | `GET` | عامة | الإعدادات العامة وأعلام الميزات فقط |
| `/api/discover` | `POST` | عامة | توصيات من ثلاثة أسئلة، بحد أقصى ثلاثة كتب |
| `/api/orders` | `POST` | عامة أو حسب عقد الطلب | يفوّض الإنشاء إلى Firebase Function الموثوقة |

مسارات `/api/products` و`/api/discover` تستخدم قراءات Firestore محدودة. لا تُقبل قيمة السعر النهائي من المتصفح كمصدر موثوق. مسار `/api/orders` يمرر السلة إلى خدمة موثوقة ويضيف `Idempotency-Key` عند غيابه لتقليل خطر تكرار الطلب بسبب إعادة الإرسال.

## مسارات الإدارة

| المسار | الطرق المتوقعة | المصادقة | التنفيذ |
|---|---|---|---|
| `/api/admin/products` و`/api/admin/products/:id` | `GET`, `POST`, `PATCH`, `DELETE` حسب العقد | Firebase ID token + دور مدير | تفويض إلى Firebase Function |
| `/api/admin/categories` و`/api/admin/categories/:name` | `GET`, `POST`, `PATCH`, `DELETE` حسب العقد | Firebase ID token + دور مدير | تفويض إلى Firebase Function |
| `/api/admin/orders` و`/api/admin/orders/:id` | `GET`, `PATCH` | Firebase ID token + دور مدير | تفويض إلى Firebase Function |
| `/api/admin/settings` | `GET`, `PATCH` | Firebase ID token + دور مدير | تفويض إلى Firebase Function |
| `/api/admin/delivery-fees` | `GET`, `POST`, `PATCH`, `DELETE` حسب العقد | Firebase ID token + دور مدير | تفويض إلى Firebase Function |

Pages Functions لا تتحقق من دور المدير بنفسها في النسخة الحالية؛ فهي ترفض غياب Bearer token وتفوض التحقق النهائي إلى Firebase Function الموثوقة. قبل الإنتاج يجب أن يكون عنوان الخدمة الموثوقة مضبوطًا، ويجب اختبار رفض token صحيح لكنه غير إداري.

## شكل الأخطاء

تستخدم الاستجابات بنية موحدة:

```json
{
  "error": {
    "code": "CATALOG_UNAVAILABLE",
    "message": "تعذر تحميل الكتب حاليًا.",
    "requestId": "req_..."
  }
}
```

كل طلب يحصل على `X-Request-ID`. إذا أرسل العميل قيمة صحيحة يعاد استخدامها، وإلا يُنشأ معرّف جديد. لا تُرسل stack traces أو رموز الوصول أو تفاصيل Firestore إلى المتصفح.

## متغيرات التشغيل

| المتغير | مطلوب | الاستخدام |
|---|---|---|
| `FIREBASE_PROJECT_ID` | نعم | معرّف مشروع Firestore؛ في التطوير `baakbook-77c00` |
| `FIRESTORE_EMULATOR_HOST` | محليًا | عنوان Emulator، مثل `127.0.0.1:8080` |
| `ALLOWED_ORIGIN` | نعم | أصل الواجهة المسموح به لـ CORS |
| `TRUSTED_ORDER_FUNCTION_URL` | قبل الطلبات | عنوان Firebase Function لإنشاء الطلب |
| `TRUSTED_ADMIN_FUNCTION_URL` | قبل الإدارة | عنوان Firebase Function لعمليات الإدارة |
| `GOOGLE_OAUTH_ACCESS_TOKEN` | لاستخدام REST الحقيقي فقط | رمز مؤقت لا يُحفظ في Git؛ غير مطلوب مع Emulator |

لا يوضع Service Account JSON في الواجهة أو المستودع. كما أن Firebase Web App Config ليس بديلًا عن اعتماد خادمي، ولا يمنح Pages Functions صلاحية الكتابة الآمنة.

## قرار التوافق

أبقيت المسارات الحالية تحت `/api` لتقليل تغييرات الواجهة أثناء الترحيل. بعد استقرار النسخة الجديدة يمكن تقديم `/api/v1` كنسخة صريحة، لكن لا يتم ذلك ضمن أول انتقال حتى لا نخلط ترحيل البنية مع تغيير سلوك المنتج.
