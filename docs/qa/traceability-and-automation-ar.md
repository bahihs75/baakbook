# مصفوفة التتبع وقائمة الأتمتة — Baak Books

## 1. مصفوفة المتطلبات إلى حالات الاختبار

| المتطلب | الوصف | حالات الاختبار المرتبطة | بوابة القبول |
|---|---|---|---|
| USER-HOME | عرض الصفحة العامة والـHero | PUB-001..PUB-005 | لا أخطاء JavaScript، وواجهة fallback سليمة |
| USER-SEARCH | البحث والتصفية | PUB-006..PUB-007 | نتائج صحيحة وعدم تنفيذ مدخلات ضارة |
| USER-PRODUCT | تفاصيل الكتاب وأزراره | PUB-008 | فتح/إغلاق وإضافة صحيحة |
| CART-QTY | السلة والكميات والإجمالي | PUB-009..PUB-010 | إجمالي حتمي وعدم تجاوز التوفر |
| GIFT-PRODUCT | إهداء كتاب منفرد | PUB-012..PUB-013 | بيانات المستلم منفصلة ورقم الهاتف الإلزامي |
| GIFT-GROUP | إهداء مجموعة بمستلم واحد | PUB-011 | مجموعة واحدة ومستلم واحد |
| CHECKOUT-ORDER | إنشاء الطلب | PUB-014..PUB-016 | طلب واحد وإجمالي متسق وعدم تكرار |
| ORDER-INTEGRITY | سلامة الإجمالي وبيانات الطلب | PUB-015 | لا ثقة غير مقبولة في قيم العميل |
| DELIVERY-FEES | رسوم التوصيل | PUB-017 | الحساب يتغير حسب المنطقة والطريقة |
| ON-DEMAND | الكتب التي يمكن اقتناؤها عند الطلب | PUB-018 | نوع التوفر ومدة التجهيز محفوظان |
| FEATURE-VISIBILITY | تشغيل/إيقاف الميزات | PUB-019..PUB-020 | اختفاء القسم كاملًا والرجوع إلى الأساس |
| ADMIN-AUTH | تسجيل دخول وخروج المدير | ADM-001..ADM-004 | لا وصول بلا مصادقة |
| ADMIN-PRODUCT | إدارة الكتب | ADM-005..ADM-008 | CRUD صحيح والتحقق من الحقول |
| ADMIN-CATEGORY | إدارة التصنيفات | ADM-009..ADM-010 | تحديث الكتب المرتبطة أو تقرير الفشل |
| ADMIN-HERO | إعدادات وشرائح Hero | ADM-011..ADM-013 | الحفظ والاختيار والظهور العام |
| MEDIA-SECRET | تخزين مفتاح ImgBB | ADM-014, SEC-003 | لا يظهر المفتاح في المصدر أو العامة |
| MEDIA-UPLOAD | رفع الصور إلى ImgBB | ADM-015..ADM-018 | نجاح، فشل، retry، وعدم سجل زائف |
| MEDIA-LIFECYCLE | مكتبة الصور | ADM-019..ADM-020 | نسخ/اختيار/حذف سجل واضح |
| ADMIN-ORDER | إدارة حالات الطلبات | ADM-021..ADM-022 | حالات صحيحة وحذف مؤكد |
| ADMIN-DELIVERY | رسوم التوصيل في الإدارة | ADM-023 | حفظ والتحقق من الأرقام |
| ADMIN-FEATURES | مفاتيح الميزات | ADM-024 | التطابق بين الإدارة والعامة |
| ADMIN-RBAC | صلاحيات المدير | RBAC-001..RBAC-004 | الرفض/السماح حسب الدور |
| SEC-XSS | منع حقن النصوص | PUB-007, ADM-008, SEC-001..SEC-002 | لا تنفيذ لأي payload |
| SEC-URL | سلامة روابط الصور | SEC-004 | HTTPS أو سياسة آمنة فقط |
| PERF-HOME | أداء الصفحة العامة | PERF-001 | لا تدهور حاد في LCP/CLS |
| PERF-MEDIA | أداء المكتبة | PERF-002 | تعامل مقبول مع 100 صورة |
| RECOVERY-ADMIN | استرداد الإدارة | REC-001 | رسالة واضحة وعدم حفظ جزئي صامت |
| RECOVERY-CHECKOUT | استرداد الشراء | REC-002 | لا طلبات مكررة وإمكانية إعادة المحاولة |
| A11Y | الوصولية | A11Y-001..A11Y-002 | لوحة المفاتيح والتركيز والعناوين سليمة |

## 2. قائمة الأتمتة المرتبة

| ID | الأتمتة | الأولوية | الأداة | الجهد | معيار الإنجاز |
|---|---|---:|---|---:|---|
| AUTO-01 | فحص عدم تسريب المفتاح و`git diff --check` | P0 | Python/CI | 0.25 يوم | يفشل البناء عند قيمة ImgBB صريحة |
| AUTO-02 | فحص build وTypeScript | P0 | npm | 0.25 يوم | `npm run build` ناجح |
| AUTO-03 | Firestore rules matrix | P0 | Firebase Emulator | 1 يوم | كل RBAC-001..004 آلي |
| AUTO-04 | Login/logout/expired token | P0 | Playwright | 0.5 يوم | لا وصول بعد الخروج |
| AUTO-05 | Smoke الصفحة والـHero | P1 | Playwright | 0.5 يوم | PUB-001..004 آلية |
| AUTO-06 | البحث والبطاقات والسلة | P1 | Playwright | 0.75 يوم | PUB-006..010 آلية |
| AUTO-07 | رحلة الهدية الفردية والمجموعة | P1 | Playwright | 0.75 يوم | PUB-011..013 آلية |
| AUTO-08 | Checkout مع mock Firestore/endpoint | P0 | Playwright + mock | 1 يوم | PUB-014..017 وREC-002 |
| AUTO-09 | CRUD الكتب والتصنيفات | P1 | Playwright + Emulator | 0.75 يوم | ADM-005..010 آلية |
| AUTO-10 | Hero settings/slides/picker | P1 | Playwright + Emulator | 0.75 يوم | ADM-011..013 آلية |
| AUTO-11 | ImgBB contract mock | P0 | MSW/route mocking | 0.75 يوم | 2xx/4xx/429/5xx/timeout |
| AUTO-12 | Media library lifecycle | P1 | Playwright + Emulator | 0.75 يوم | ADM-014..020 آلية |
| AUTO-13 | XSS/URL security suite | P0 | Playwright + sanitizer assertions | 0.5 يوم | SEC-001..004 آلية |
| AUTO-14 | Accessibility scan | P1 | axe-core | 0.5 يوم | لا critical/serious في الشاشات الأساسية |
| AUTO-15 | Lighthouse budget | P2 | Lighthouse CI | 0.5 يوم | حدود LCP/CLS/JS error محددة |
| AUTO-16 | Load/concurrency checkout | P1 | k6 | 1 يوم | لا duplicate وp95 موثق |
| AUTO-17 | Visual regression RTL | P2 | Playwright screenshots | 0.75 يوم | baseline معتمد للصفحة والإدارة |
| AUTO-18 | Post-deploy health checks | P0 | curl/Playwright CI | 0.25 يوم | الموقع والإدارة يعيدان استجابة سليمة |

## 3. استراتيجية mocks/stubs

يُحاكى ImgBB افتراضيًا في CI عبر endpoint محلي يعيد الحالات التالية: نجاح مع `data.url`، فشل مصادقة 403، حد معدل 429، خطأ خادم 500، مهلة، واستجابة JSON ناقصة. ويُستخدم Firebase Emulator لاختبار القواعد والكتابة بدلاً من قاعدة الإنتاج. أما اختبار الرفع الحقيقي فيُجرى يدويًا أو في pipeline محمي بمفتاح بيئة مخصص، مع عدم طباعة المفتاح.

## 4. معايير إخراج تقرير آلي

كل تشغيل يجب أن ينتج `junit.xml`، ولقطات فشل، وPlaywright trace، وسجل console، وملخصًا يتضمن commit SHA والبيئة ونسخة Node. ويجب فصل فشل الشبكة الخارجية عن فشل التطبيق: إذا فشل mock المحلي فهذا عطل في الاختبار، وإذا فشل ImgBB الحقيقي في اختبار محدود يُسجل كفشل تكامل خارجي مع رابط مرجع دون كشف المفتاح.
