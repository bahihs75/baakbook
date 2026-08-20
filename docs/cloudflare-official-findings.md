# مصادر Cloudflare الرسمية المستخدمة في إعداد Baak Books

## Git integration

المصدر الرسمي: [Git integration guide](https://developers.cloudflare.com/pages/get-started/git-integration/)

توضح Cloudflare أن إعداد Pages عبر Git يتم من Workers & Pages ثم Create application > Pages > Connect to Git. يدعم التكامل GitHub وGitLab، ويمكن اختيار المستودعات العامة أو الخاصة بعد تثبيت صلاحية الوصول. يحدد المستخدم اسم المشروع، وفرع الإنتاج، وRoot directory، وأمر البناء، ومجلد الناتج، ومتغيرات البيئة، ثم يختار Save and Deploy. الفرع `main` هو الاختيار المعتاد للإنتاج، بينما تُستخدم الفروع الأخرى عادةً لمعاينات Preview.

تبدأ عملية البناء من جذر المستودع افتراضيًا، ويمكن تغيير ذلك من Root directory (advanced) > Path، وهو مهم في Baak Books لأن مشروع Pages موجود داخل `frontend/`.

## Build configuration

المصدر الرسمي: [Build configuration](https://developers.cloudflare.com/pages/configuration/build-configuration/)

إذا لم يستخدم المشروع إطارًا معروفًا، يمكن ترك Framework preset دون اختيار، ويجب أن يعيد أمر البناء حالة خروج ناجحة. في Baak Books يملك مجلد `frontend/` أمر بناء فعليًا هو `npm run build`، ويقوم بتوليد `runtime-config.js` ثم فحص TypeScript. خرج Pages مضبوط محليًا على نفس الجذر عبر `pages_build_output_dir = "."` في `frontend/wrangler.toml`.

تؤكد Cloudflare أن المتغيرات تُضاف من Workers & Pages > المشروع > Settings > Environment variables، ويمكن ضبطها بعد إنشاء المشروع أو أثناء الإعداد الأول.

## Pages Functions

المصدر الرسمي: [Pages Functions — Get started](https://developers.cloudflare.com/pages/functions/get-started/)

يجب أن يوجد مجلد `functions/` في جذر مشروع Pages، وليس داخل مجلد static output مثل `dist/`. تُحوّل أسماء الملفات داخل هذا المجلد تلقائيًا إلى مسارات HTTP، وتعيد الدوال كائن `Response` أو Promise منه. لذلك يعتمد Baak Books على `frontend/functions/`، وليس على Worker مستقل.

## Local environment variables

المصدر الرسمي: [Environment variables and secrets](https://developers.cloudflare.com/workers/local-development/environment-variables/)

تقرأ Wrangler ملفات `.dev.vars` أو `.env` الموجودة بجانب ملف إعداد Wrangler في التطوير المحلي، ويجب استبعاد ملفات الأسرار من Git. أما متغيرات الإنتاج فتُضبط من لوحة Cloudflare. لا يوضع Service Account JSON أو أي اعتماد خادمي داخل الواجهة أو المستودع.

## تطبيق المصادر على Baak Books

| القرار | قيمة Baak Books المحلية |
|---|---|
| Git repository | `bahihs75/baakbook` |
| Pages project name | `baakbook` |
| Production branch | `main` |
| Root directory | `frontend` |
| Framework preset | None / Custom |
| Build command | `npm run build` |
| Build output directory | `.` |
| Pages Functions directory | `frontend/functions/` |
| Production Firebase project | `baakbook-77c00` |
| Production origin | `https://baakbook.pages.dev` |

هذه الملاحظات لا تعني تنفيذ الربط أو النشر. إعداد المشروع في Cloudflare يبقى خطوة يدوية ينفذها المستخدم، ولا يتم `git push` من هذه الجلسة.
