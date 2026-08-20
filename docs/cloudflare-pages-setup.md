# إعداد Cloudflare Pages لمتجر Baak Books

هذا الدليل يخص **Baak Books فقط**. لا يتضمن تعديل Afak Carpet أو Tiddis Tapis، ولا يتضمن تنفيذ `git push` أو نشرًا من هذه الجلسة.

## القرار الحالي

البنية المحلية الجاهزة هي:

| الطبقة | المسؤولية |
|---|---|
| Cloudflare Pages | ملفات المتجر و`frontend/functions/` |
| Pages Functions | مسارات `/api/*`، CORS، معرّف الطلب، والقراءات العامة أو التفويض |
| Firebase Authentication | تسجيل دخول الإدارة والتحقق من Firebase ID token |
| Firebase Functions | إعادة حساب السعر، فحص المخزون، إنشاء الطلب، وعمليات الإدارة الموثوقة |
| Firestore | المنتجات والتصنيفات والطلبات ورسوم التوصيل والإعدادات |
| PythonAnywhere | النسخة الحالية وخطة الرجوع، ولا تُعدّل أثناء الترحيل |

> **مهم:** ملف إعداد Firebase الخاص بالواجهة يحتوي قيمًا عامة فقط. لا تضع Service Account JSON أو مفتاحًا خادميًا أو رمز OAuth دائمًا في الواجهة أو GitHub.

## ما يجب أن يفعله المستخدم في Cloudflare

لا تنفّذ هذه الخطوات قبل مراجعة التغييرات المحلية والحصول على موافقة مستقلة على `git push`. عند صدور تلك الموافقة، افتح لوحة [Cloudflare Dashboard](https://dash.cloudflare.com/) ثم اتبع الترتيب الآتي:

1. افتح **Workers & Pages**.
2. اختر **Create application** ثم **Pages** ثم **Connect to Git**.
3. اختر GitHub، ثم اختر المستودع `bahihs75/baakbook` فقط.
4. سمِّ المشروع `baakbook`، بحيث يكون العنوان المتوقع `baakbook.pages.dev` إذا كان الاسم متاحًا.
5. اختر فرع الإنتاج `main`.
6. افتح الإعدادات المتقدمة، واجعل **Root directory** هو `frontend`.
7. اجعل **Framework preset** هو `None` أو `Custom`.
8. اجعل **Build command** هو `npm run build`.
9. اجعل **Build output directory** هو `.`.
10. لا تضف أمر نشر Wrangler مستقلًا؛ Pages سيكتشف مجلد `frontend/functions/` تلقائيًا لأنه موجود في جذر مشروع Pages.
11. لا تضغط **Save and Deploy** قبل التأكد من أن المتغيرات أدناه مكتملة وأن Firebase Functions الموثوقة جاهزة.

هذه القيم مبنية على وثائق Cloudflare الرسمية الخاصة بـ [Git integration](https://developers.cloudflare.com/pages/get-started/git-integration/)، و[Build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/)، و[Pages Functions](https://developers.cloudflare.com/pages/functions/get-started/).

## متغيرات بيئة الإنتاج

أضفها في **Settings > Environment variables > Production**. متغيرات Firebase Web التالية ستظهر في ملف JavaScript العام عند البناء؛ وجودها في الواجهة طبيعي، لكنها لا تمنح صلاحية كتابة آمنة إلى Firestore.

| الاسم | القيمة | ملاحظات |
|---|---|---|
| `FIREBASE_API_KEY` | قيمة Web App Config للمشروع `baakbook-77c00` | قيمة عامة للواجهة |
| `FIREBASE_AUTH_DOMAIN` | `baakbook-77c00.firebaseapp.com` | قيمة عامة |
| `FIREBASE_PROJECT_ID` | `baakbook-77c00` | مطلوب للواجهة وPages |
| `FIREBASE_STORAGE_BUCKET` | `baakbook-77c00.firebasestorage.app` | قيمة عامة |
| `FIREBASE_MESSAGING_SENDER_ID` | `446668891522` | قيمة عامة |
| `FIREBASE_APP_ID` | `1:446668891522:web:d381a6bfa453eb94abdb9b` | قيمة عامة |
| `PUBLIC_API_BASE` | `/api` | اتركه نسبيًا داخل Pages |
| `ALLOWED_ORIGIN` | `https://baakbook.pages.dev` | أصل CORS الإنتاجي |

## متغيرات لا تُضاف قبل جاهزية Firebase Functions

هذه المتغيرات ضرورية للعمليات التي لا يجوز تنفيذها داخل المتصفح، لكنها لا ينبغي أن تكون عناوين وهمية:

| الاسم | متى يضاف؟ | الغرض |
|---|---|---|
| `TRUSTED_ORDER_FUNCTION_URL` | بعد نشر واختبار Firebase Function الخاصة بالطلبات | إنشاء الطلب بعد إعادة حساب السعر وفحص المخزون |
| `TRUSTED_ADMIN_FUNCTION_URL` | بعد نشر واختبار Firebase Function الإدارية | المنتجات والطلبات والإعدادات ورسوم التوصيل |

لا تضف `FIRESTORE_EMULATOR_HOST` إلى Production؛ هذا المتغير محلي فقط وقيمته `127.0.0.1:8080`. لا تضف `GOOGLE_OAUTH_ACCESS_TOKEN` أو `GOOGLE_SERVICE_ACCOUNT_PRIVATE_KEY` إلى متغيرات عامة أو إلى المستودع. إذا احتاجت Pages إلى قراءة Firestore مباشرة في الإنتاج، يجب أولًا اعتماد قناة خادمية دائمة ومراجعة صلاحياتها؛ رمز OAuth المؤقت ليس حلًا إنتاجيًا.

## إعداد Preview

يمكن إنشاء متغيرات منفصلة لبيئة Preview. لا تستخدم فيها أصل الإنتاج إذا كان الهدف اختبار معاينات فرعية؛ استخدم أصل المعاينة المتوقع أو اجعل CORS مقيدًا مؤقتًا. لا تستورد بيانات العملاء إلى Preview، واستخدم Emulator أو مجموعة بيانات اصطناعية.

## فحص ما بعد إنشاء المشروع

بعد تجهيز المشروع وبمجرد السماح بالنشر، افحص بالترتيب:

1. نجاح البناء وعدم ظهور `Missing runtime configuration`.
2. وجود `runtime-config.js` في أصل الموقع.
3. نجاح `GET /api/products` عندما تكون قناة Firestore العامة الموثوقة جاهزة.
4. عودة `401` من مسارات `/api/admin/*` عند غياب Firebase ID token.
5. رفض token صحيح لكنه لا يحمل دور المدير.
6. نجاح `OPTIONS /api/products` بحالة `204` ورؤوس CORS.
7. عدم قبول السعر النهائي المرسل من المتصفح كمصدر للحساب.
8. نجاح `POST /api/orders` مرة واحدة مع إعادة المحاولة باستخدام نفس `Idempotency-Key` دون إنشاء طلب مكرر.

## مصادر مرجعية

1. Cloudflare, [Git integration for Pages](https://developers.cloudflare.com/pages/get-started/git-integration/).
2. Cloudflare, [Build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/).
3. Cloudflare, [Pages Functions — Get started](https://developers.cloudflare.com/pages/functions/get-started/).
4. Cloudflare, [Environment variables and secrets](https://developers.cloudflare.com/workers/local-development/environment-variables/).
5. عقد Baak Books المحلي: `docs/pages-functions-api-contract.md`.
6. نتائج Emulator المحلي: `docs/local-emulator-validation.md`.

هذا الملف يقدّم تعليمات الإعداد فقط. لا يعني أن المشروع نُشر أو أن البيانات نُقلت إلى Firebase الحقيقي.
