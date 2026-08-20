# BaakBook — متجر الكتب العربي

BaakBook هو متجر كتب عربي بواجهة RTL مصممة لعرض الكتب، تصفية المنتجات حسب الفئة، إدارة سلة الشراء، وحساب رسوم التوصيل حسب الولاية وطريقة التسليم. يحتوي المشروع أيضًا على لوحة إدارة محمية لإدارة المنتجات والفئات والطلبات ورسوم التوصيل.

المشروع عبارة عن تطبيق Flask صغير بواجهة HTML/CSS/JavaScript مباشرة، ولذلك لا يحتاج إلى مرحلة بناء frontend. يمكن تشغيله محليًا، أو نشره على PythonAnywhere، أو ربطه بمنصة تدعم النشر التلقائي من GitHub.

## حالة المشروع الحالية

| العنصر | الحالة |
|---|---|
| الواجهة العامة | `store.html` وتعمل عبر المسار `/` |
| لوحة الإدارة | `admin.html` وتعمل عبر المسار `/admin` |
| الواجهة الخلفية | Flask في `app.py` |
| البيانات الحالية | ملف JSON محلي؛ الطلبات الحية لا تُرفع إلى GitHub |
| خادم الإنتاج | Gunicorn عند النشر خارج خادم التطوير |
| الاختبارات | Pytest مع تشغيل تلقائي عبر GitHub Actions |
| نقطة WSGI | `wsgi.py` لـ PythonAnywhere والمضيفين المتوافقين |

> **تنبيه مهم:** ملف `data.json` الموجود في بيئة التشغيل يحتوي على أسماء وأرقام هواتف وعناوين عملاء. لذلك تم استبعاده من GitHub، وأُضيف بدلًا منه `data.example.json` منزوع الطلبات الحية.

## هدف الترحيل الجديد

الهدف المعتمد هو نقل المتجر في **عملية انتقال واحدة** بعد تجهيز البيئة واختبارها محليًا وتجريبيًا:

| الجزء | الوجهة الجديدة |
|---|---|
| الواجهة والمتجر ولوحة الإدارة | Cloudflare Pages |
| عنوان الإنتاج | `https://baakbook.pages.dev` |
| المنتجات والطلبات والإعدادات | Cloud Firestore |
| تسجيل دخول الإدارة | Firebase Authentication مع دور إداري |
| العمليات الحساسة | Firebase Cloud Functions 2nd gen |
| الصور الحالية | الحفاظ على روابطها، ثم إدارة الصور عبر مكتبة ImgBB لاحقًا |

لن يتم رفع `data.json` إلى GitHub أو Cloudflare Pages. ستبقى PythonAnywhere والنسخة الأصلية من البيانات متاحتين للرجوع حتى انتهاء فترة المراقبة بعد الانتقال.

> **حالة الترحيل:** جرى بناء التصميم وعقد البيانات وأدوات فحص وتحويل محلية. لم يتم إنشاء أو ربط مشروع Firebase إنتاجي، ولم يتم النشر إلى Cloudflare Pages، ولم يتم تعديل PythonAnywhere.

## البنية المعمارية

```text
المتصفح
   │
   ├── /              ──> store.html
   ├── /admin         ──> admin.html
   └── /api/*         ──> Flask API في app.py
                              │
                              └── data.json في بيئة التشغيل فقط
```

يعتمد التطبيق حاليًا على تخزين JSON محلي. هذا مناسب لمتجر صغير أو مرحلة أولية على خادم واحد، لكنه ليس التصميم الأفضل عند استخدام أكثر من نسخة تشغيل أو عند الحاجة إلى نسخ احتياطية واستمرارية بيانات قوية. المرحلة التطويرية التالية الموصى بها هي نقل الطلبات والمنتجات إلى PostgreSQL أو SQLite على قرص دائم، مع إبقاء بيانات العملاء خارج المستودع.

## فحص الترحيل محليًا

توجد أدوات القراءة والتحويل والفحص المستقل داخل `migration/`. هذه الأوامر تعمل على نسخة محلية فقط:

```bash
python3 migration/inspect_source.py data.json migration/reports/source-inventory.json
python3 migration/transform.py data.json migration/reports/target-fixture.json --batch-id local-dry-run
python3 migration/verify_bundle.py data.json migration/reports/target-fixture.json migration/reports/reconciliation.json
```

التحقق الناجح يجب أن يعرض `status: verified` و`differences: {}`. لا تشغّل هذه الأدوات على ملف حي أثناء استقبال الطلبات؛ تصدير البيانات الحية سيكون خطوة منفصلة داخل نافذة الانتقال النهائي.

## التشغيل المحلي

يتطلب المشروع Python 3.11 أو إصدارًا أحدث.

```bash
git clone https://github.com/bahihs75/baakbook.git
cd baakbook
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
cp .env.example .env
```

بعد نسخ `.env.example`، عيّن قيمة طويلة وعشوائية للمتغير `ADMIN_TOKEN`. لا تضع قيمة السر الحقيقية داخل Git أو داخل ملف HTML.

لتشغيل التطبيق في وضع التطوير:

```bash
export ADMIN_TOKEN='ضع-سرًا-طويلًا-هنا'
python app.py
```

ثم افتح:

- المتجر: `http://127.0.0.1:5000/`
- لوحة الإدارة: `http://127.0.0.1:5000/admin`

لتشغيله بخادم الإنتاج محليًا:

```bash
gunicorn app:app
```

## الاختبارات

شغّل الاختبارات بالأمر التالي:

```bash
python -m pytest -q
```

النتيجة المتوقعة في النسخة الحالية هي نجاح الاختبارات الأساسية الخاصة بعرض المتجر، وإرجاع قائمة المنتجات بصيغة JSON، ومنع الوصول إلى لوحة الإدارة عند غياب السر.

يعمل GitHub Actions تلقائيًا عند كل `push` إلى `main` وعند فتح Pull Request. لا يتم اعتبار التغيير جاهزًا قبل نجاح الاختبارات.

## متغيرات البيئة

| المتغير | الغرض | إلزامي؟ | مثال |
|---|---|---:|---|
| `ADMIN_TOKEN` | السر الذي يحمي واجهة `/api/admin/*` | نعم للإدارة | `ضع-قيمة-عشوائية-طويلة` |
| `DATA_FILE` | المسار الكامل أو النسبي لملف البيانات القابل للكتابة | اختياري | `/home/user/baakbook/data.json` |

إذا لم يتم ضبط `ADMIN_TOKEN`، فالتطبيق يفشل مغلقًا ويمنع جميع طلبات الإدارة. هذا مقصود لتجنب تشغيل لوحة تحكم محمية بسر فارغ.

## النشر على PythonAnywhere

PythonAnywhere مناسب جدًا للنسخة الحالية لأن التطبيق يعتمد على ملف JSON قابل للكتابة ويعمل على عملية واحدة. وثائق PythonAnywhere توصي باستخدام Git لسحب المشروع بدل رفع الملفات يدويًا، وتوضح أن التطبيق يحتاج إلى إعادة تحميل بعد تغيير كود Python [1].

### أول إعداد

في Bash Console داخل PythonAnywhere:

```bash
cd ~
git clone https://github.com/bahihs75/baakbook.git
cd baakbook
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp data.example.json data.json
```

بعد ذلك، اضبط `ADMIN_TOKEN` في إعدادات Web App أو في بيئة التشغيل، واجعل ملف WSGI يشير إلى:

```python
import sys
sys.path.insert(0, '/home/USERNAME/baakbook')
from app import app as application
```

استبدل `USERNAME` باسم حسابك الفعلي. يجب الاحتفاظ بملف `data.json` الحالي في مسار التشغيل، وعدم استبداله بـ `data.example.json` إذا كان يحتوي على الطلبات الحقيقية.

### أسهل تحديث يدوي وآمن

بعد دفع التغييرات إلى GitHub:

```bash
cd ~/baakbook
git fetch origin
git checkout main
git pull --ff-only origin main
source .venv/bin/activate
pip install -r requirements.txt
```

ثم اذهب إلى تبويب **Web** واضغط **Reload**. هذه الخطوة ضرورية عادةً بعد تغيير كود Python؛ أما تعديلات HTML فقد تُرى تلقائيًا، لكن إعادة التحميل أوضح وأكثر أمانًا [2].

### تحديث شبه تلقائي

يمكن جعل PythonAnywhere يعيد تحميل التطبيق بعد عملية Git عبر hook أو عبر تنفيذ أمر لمس ملف WSGI. وثائق PythonAnywhere تذكر صراحةً إمكانية إعادة التحميل من خلال Git actions عبر لمس ملف WSGI [2]. هذا يتطلب ضبط المسار والصلاحيات داخل حسابك، ولذلك يُفضّل البدء بالتحديث اليدوي أعلاه ثم إضافة hook بعد التأكد من النسخ الاحتياطية.

## هل ننقل الموقع إلى منصة أخرى؟

التوصية العملية هي **عدم نقل الموقع فورًا قبل معالجة تخزين البيانات**. يمكن ربط PythonAnywhere بـ GitHub الآن والحصول على سير عمل منظم وآمن. أما Render فيوفر نشرًا تلقائيًا عند كل push إلى الفرع المرتبط [3]، لكنه يستخدم نظام ملفات مؤقتًا افتراضيًا، وتضيع التغييرات على الملفات عند إعادة التشغيل أو إعادة النشر، كما أن الخدمة المجانية لا توفر قرصًا دائمًا [4]. وبما أن التطبيق يحفظ الطلبات في `data.json`، فإن نقل النسخة الحالية كما هي إلى Render المجاني قد يؤدي إلى فقدان الطلبات.

| الخيار | المزايا | المخاطر أو القيود | التقييم الحالي |
|---|---|---|---|
| PythonAnywhere + GitHub | أقل تغيير، مناسب لـ JSON القابل للكتابة، تحديث واضح عبر `git pull` وReload | التحديث التلقائي يحتاج إعداد hook أو API، ونظام التخزين ما زال ملفيًا | **الأفضل الآن** |
| Render مع GitHub | نشر تلقائي بعد كل push، إعداد سهل لتطبيق Flask، ويدعم Gunicorn [3] | النظام المجاني مؤقت؛ لا يصلح لـ `data.json` الحي دون قاعدة بيانات أو قرص دائم [4] | مناسب بعد نقل البيانات |
| Railway مع GitHub | نشر Flask من GitHub، واكتشاف تطبيق Python تلقائيًا، وإعداد سريع [5] | التكلفة والاستمرارية تعتمد على الخطة؛ يجب نقل البيانات إلى تخزين دائم | خيار جيد بعد ترقية التخزين |
| VPS أو خادم مُدار | تحكم كامل وقرص دائم وخيارات نسخ احتياطي واسعة | يحتاج تحديثات أمنية وتهيئة Nginx/Gunicorn ونسخ احتياطية وإدارة خادم | غير ضروري للمرحلة الحالية |

## خطة التحديث المقترحة

المرحلة الأولى هي اعتماد GitHub كمصدر وحيد للكود، مع إبقاء `data.json` الحي على PythonAnywhere فقط. عند كل تغيير، يُنشأ commit ويُدفع إلى `main`، ثم يُسحب على PythonAnywhere ويُعاد تحميل التطبيق. بهذه الطريقة يمكن الرجوع إلى أي نسخة سابقة من الكود دون لمس طلبات العملاء.

المرحلة الثانية هي إضافة نسخة احتياطية دورية من `data.json` خارج GitHub، مع تقييد صلاحيات الملف. لا ينبغي رفع هذا الملف إلى مستودع عام أو خاص ما لم يتم تنظيفه من بيانات العملاء، لأن المستودع الخاص ليس بديلًا عن نظام نسخ احتياطي أو سياسة وصول مناسبة.

المرحلة الثالثة، قبل الانتقال إلى Render أو Railway، هي نقل البيانات إلى قاعدة بيانات دائمة مثل PostgreSQL أو إلى قرص دائم مدعوم من الخطة المختارة. بعد ذلك يمكن تفعيل النشر التلقائي من GitHub بأمان أكبر، وإضافة migrations واختبارات تكامل.

## الأمن والخصوصية

تمت إزالة السر الصريح من `app.py` وتحويله إلى المتغير `ADMIN_TOKEN`. كما تم جعل رابط المنتج في لوحة الإدارة يعتمد على النطاق الحالي بدل نطاق PythonAnywhere الثابت، ولذلك سيعمل الرابط بعد الانتقال إلى نطاق جديد.

ينبغي أيضًا لاحقًا تحسين حماية لوحة الإدارة باستخدام جلسات أو مزود هوية، وإضافة تحديد لمعدل الطلبات، والتحقق الصريح من محتوى السلة والأسعار من الخادم بدل الثقة الكاملة في القيم القادمة من المتصفح. هذه تحسينات مهمة قبل زيادة عدد الطلبات، لكنها ليست شرطًا لتشغيل النسخة الحالية بعد ضبط السر وعدم نشر بيانات العملاء.

## المساهمة

للمساهمة، أنشئ فرعًا جديدًا، نفّذ الاختبارات، ثم افتح Pull Request:

```bash
git checkout -b feature/short-description
python -m pytest -q
git add .
git commit -m "Describe the change"
git push -u origin feature/short-description
```

لا تُضمّن ملفات `.env` أو `data.json` أو أي نسخة تحتوي على أسماء العملاء أو أرقام هواتفهم أو عناوينهم.

## الملفات المهمة

| الملف | الوظيفة |
|---|---|
| `app.py` | تطبيق Flask وواجهات API |
| `store.html` | واجهة المتجر العامة |
| `admin.html` | لوحة الإدارة |
| `data.example.json` | نموذج بيانات نظيف بلا طلبات عملاء |
| `wsgi.py` | نقطة تشغيل WSGI |
| `Procfile` | أمر تشغيل Gunicorn |
| `render.yaml` | إعداد قديم للنشر على Render؛ لا يمثل الهدف الجديد |
| `firebase.json` | إعداد Firestore وFunctions Emulator محليًا |
| `firestore.rules` | قواعد Firestore المبدئية غير المنشورة |
| `firestore.indexes.json` | الفهارس الأولية للاستعلامات المحددة |
| `functions/` | Functions TypeScript موثوقة، حاليًا مع Function إنشاء الطلب |
| `frontend/` | نسخة واجهة مستقلة تمهيدًا لتكييفها مع Pages |
| `migration/` | أدوات الجرد والتحويل والفحص المحلي |
| `.env.example` | قالب متغيرات البيئة للنسخة Flask الحالية |
| `.github/workflows/tests.yml` | الاختبارات التلقائية |

## المراجع

[1]: https://help.pythonanywhere.com/pages/UploadingAndDownloadingFiles/ "PythonAnywhere — How to get your code in and out"

[2]: https://help.pythonanywhere.com/pages/ReloadWebApp/ "PythonAnywhere — Reload web app"

[3]: https://render.com/docs/deploy-flask "Render — Deploy a Flask App"

[4]: https://render.com/docs/free "Render — Free instance limitations and local files"

[5]: https://docs.railway.com/guides/flask "Railway — Deploy a Flask App"
