# خطوات Firestore الإنتاجية لمشروع Baak Books

هذا الدليل يخص مشروع Firebase الصحيح فقط: `baakbook-77c00` في منطقة Frankfurt (`europe-west3`). لا تستخدم المشروعين القديمين `baak-books-production` أو `baak-books-production-ab2ed`.

## الحالة الحالية

قواعد Firestore موجودة في `firestore.rules`، والفهارس في `firestore.indexes.json`. تم اختبار القواعد محليًا على Firestore Emulator باستخدام مشروع تجريبي `demo-baakbook`. لم تُنشر القواعد إلى Firebase الحقيقي، ولم تُستورد بيانات العملاء أو `data.json` الحي.

> **لا تنشر القواعد الآن إلا بعد مراجعة هذا الدليل وإعطاء موافقة منفصلة.** موافقتك السابقة كانت على `git push` فقط.

## ماذا تفعل القواعد الحالية؟

| المسار | القراءة العامة | الكتابة | الملاحظة |
|---|---:|---:|---|
| `products/{id}` | نعم للكتاب النشط غير المؤرشف | المدير فقط | يتحقق من السعر والتوفر ومدة الاقتناء |
| `categories/{id}` | نعم للتصنيف النشط | المدير فقط | الحذف ممنوع |
| `deliveryFees/{id}` | نعم للرسم النشط | المدير فقط | الحذف ممنوع |
| `settings/public` | نعم | المدير فقط | لا يحتوي إعدادات سرية |
| `orders/{id}` | المدير فقط | ممنوعة من العميل | الإنشاء يتم عبر وظيفة موثوقة تعيد حساب السعر والمخزون |
| `imageLibrary/{id}` | المدير فقط | المدير فقط | لا يوجد رفع عام |
| `auditLogs/{id}` | المدير فقط | ممنوعة من العميل | تكتبها الخدمة الموثوقة لاحقًا |
| `migrationMetadata/{id}` | المدير فقط | ممنوعة من العميل | تستخدم للتدقيق في الترحيل |

تعتمد صلاحية المدير على وجود custom claim باسم `admin` وقيمته `true` داخل Firebase ID token. وجود حساب `baakbook01@gmail.com` في Authentication لا يعني تلقائيًا أنه مدير.

## الخطوة الأولى: تأكيد المشروع

افتح [Firebase Console](https://console.firebase.google.com/) وتأكد من ظهور اسم المشروع `baakbook-77c00` في محدد المشروع. افتح **Build > Firestore Database** وتأكد من أن قاعدة البيانات الموجودة هي قاعدة المشروع الصحيح وفي المنطقة `europe-west3`. لا تنشئ قاعدة جديدة ولا تغيّر الخطة إلى Blaze.

## الخطوة الثانية: مراجعة القواعد في Rules Simulator

من Firestore Database افتح تبويب **Rules** ثم استخدم Rules Simulator قبل النشر. القواعد التي يجب اختبارها هي الموجودة في مستودع Baak Books، لا قواعد مشروع قديم. نفّذ على الأقل الاختبارات الآتية:

| الحالة | المسار والعملية | النتيجة المتوقعة |
|---|---|---:|
| زائر غير مسجل | قراءة منتج نشط غير مؤرشف | Allow |
| زائر غير مسجل | قراءة منتج مؤرشف | Deny |
| زائر غير مسجل | إنشاء `/orders/test-order` | Deny |
| مستخدم مسجل بلا claim مدير | تعديل منتج | Deny |
| مدير يحمل `admin: true` | تعديل منتج بقيم صحيحة | Allow |
| مدير يحمل `admin: true` | قراءة طلب | Allow |
| مستخدم عادي | قراءة طلب | Deny |
| أي مستخدم | كتابة `auditLogs` أو `migrationMetadata` مباشرة | Deny |

لا تستخدم أبدًا قاعدة عامة مثل `allow read, write: if true` في الإنتاج؛ هذا يفتح قاعدة البيانات بالكامل.[1]

## الخطوة الثالثة: إعداد صلاحية المدير

يجب إسناد custom claim من بيئة موثوقة باستخدام Firebase Admin SDK، وليس من الواجهة أو من متصفح المستخدم. أنشئ وظيفة إدارية مؤقتة أو استخدم بيئة موثوقة تملك صلاحية Admin SDK، ثم طبّق المنطق التالي على UID الخاص بالحساب `baakbook01@gmail.com`:

```js
await getAuth().setCustomUserClaims(uid, { admin: true });
```

لا ترسل Service Account JSON داخل المحادثة ولا تحفظه في GitHub. بعد تغيير claim، سجّل الخروج ثم الدخول مجددًا، أو اطلب تجديد Firebase ID token؛ فالـ claim الجديد يظهر عند إصدار token جديد أو تجديده بالقوة.[2]

لا تنشر قواعد الكتابة قبل التأكد من أن حساب المدير يحمل claim فعلًا، وإلا ستتمكن من تسجيل الدخول لكن ستُرفض عمليات لوحة الإدارة.

## الخطوة الرابعة: نشر القواعد من Firebase Console

بعد نجاح Rules Simulator، انسخ محتوى `firestore.rules` من مستودع Baak Books إلى محرر Rules في المشروع `baakbook-77c00`، ثم اضغط **Publish**. راجع اسم المشروع مرة ثانية في نافذة التأكيد قبل النشر. نشر القواعد لا يعني استيراد البيانات ولا يغيّر `data.json` على PythonAnywhere.

بديل CLI من نسخة المشروع المحلية، ولا تشغله إلا بعد موافقة منفصلة:

```bash
cd /path/to/baakbook-local
cp .firebaserc.example .firebaserc
firebase login
firebase use baakbook-77c00
firebase projects:list
firebase deploy --only firestore:rules --project baakbook-77c00
```

يمكن نشر الفهارس بعد مراجعتها:

```bash
firebase deploy --only firestore:indexes --project baakbook-77c00
```

يُبقي Firebase CLI إعداد المشروع في `firebase.json`، ويتيح حفظ القواعد تحت version control بدل تعديلها دون سجل.[3]

## الخطوة الخامسة: لا تستورد البيانات بعد نشر القواعد مباشرة

نشر القواعد خطوة مستقلة عن الترحيل. بعد نشرها، افحص القواعد أولًا، ثم نُنشئ لقطة نهائية من `data.json` الحي في PythonAnywhere في نافذة التجميد المتفق عليها، ثم نطبّق خطة الاستيراد ونقرأ كل الوثائق للتحقق منها. حتى ذلك الحين، لا تشغّل `migration/firestore_import.py` على المشروع الحقيقي.

## ملاحظة مهمة حول Spark وFirebase Functions

قواعد Firestore نفسها لا تحتاج إلى إدخال بيانات دفع. أما نشر Firebase Functions أو بعض خدمات Google Cloud فقد يعرض متطلبات خطة مختلفة. إذا ظهرت مطالبة بالترقية إلى Blaze أو إضافة بطاقة، **توقف ولا توافق**؛ سنعيد تقييم طبقة العمليات الموثوقة قبل أي ترقية. لا توجد حاجة لترقية الخطة من أجل نشر القواعد وحدها.

## بعد النشر

قد يستغرق انتشار تغييرات القواعد وقتًا قصيرًا للطلبات الجديدة، وقد يستغرق الانتشار الكامل وقتًا أطول للجلسات أو المستمعين النشطين.[1] بعد ذلك أعد تشغيل Rules Simulator، وسجّل نتيجة كل اختبار في `docs/migration-readiness-log.md`، ولا تبدأ استيراد البيانات قبل اعتماد فحص مستقل ثانٍ.

## References

[1]: https://firebase.google.com/docs/firestore/security/get-started "Firebase: Get started with Cloud Firestore Security Rules"
[2]: https://firebase.google.com/docs/auth/admin/custom-claims "Firebase: Manage users with custom claims"
[3]: https://firebase.google.com/docs/cli "Firebase CLI documentation"
