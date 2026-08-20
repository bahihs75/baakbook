# Baseline review — local BaakBook

Local review URL: https://8000-idyy867z2ydfd4k4mve75-53f9d2fe.us5.manus.computer/

The isolated local app is served from `/home/ubuntu/baakbook-local` with sanitized `data.json`; production and GitHub data are not modified. The local workspace has its Git push URL intentionally set to `DISABLED_NO_PUSH_UNTIL_APPROVED`.

## Observed storefront baseline

- Page title: `Baak Books — متجر الكتب`.
- RTL storefront with a top brand label, search input (`بحث عن كتاب...`), cart toggle showing zero items, category filters (`الكل`, `روايات`, `تنمية بشرية`), product grid, and footer contact links.
- Hero heading: `حيث الكلمات تأخذك لعوالم أخرى` with supporting Arabic copy.
- Product cards show cover image, category, title, truncated description, price in Algerian dinar, and `شراء الآن` action.
- Local sanitized dataset displays a substantial catalog of books, including fiction and human-development categories.
- Cart panel is initially empty (`سلتك فارغة`).
- Product images are remote URLs, including i.ibb.co and Google thumbnail URLs.
- Browser baseline screenshot was saved by the browser at `/home/ubuntu/screenshots/8000-idyy867z2ydfd4k_2026-08-18_19-36-06_3867.webp`.

## Initial UX/design notes

- Existing visual direction is warm editorial/luxury: off-white background, gold accent, Cairo font, rounded product cards, and book-cover-led content.
- The current layout is a four-column desktop product grid with category filtering and search; mobile behavior and cart interactions require focused validation before changes.
- Good candidate improvements should be tested as small, reversible experiments: mobile navigation and spacing, product-card hierarchy, search/filter states, cart/checkout clarity, loading/empty/error states, and admin usability.

## Important guardrail

Do not run `git push` from the local workspace unless the user explicitly validates the feature and says to publish it. Do not copy local test data to PythonAnywhere.
