# Migration Readiness Log

## 2026-08-19 — Local dry-run baseline

The local `data.json` was inspected without modification or external access.

| Metric | Value |
|---|---:|
| Products | 22 |
| Categories | 4 |
| Delivery fees | 58 |
| Orders | 6 |
| Order items | 12 |
| Product availability types | 21 `in_stock`, 1 `on_demand` |
| Duplicate product IDs | 0 |
| Duplicate order IDs | 0 |
| Missing product IDs | 0 |
| Missing order IDs | 0 |
| Historical order total sum | 19,500 DZD |

Source JSON SHA-256:

```text
a258d304f1e318dd3e86df0de1b2b5546c27a48f378fdaf6a6672ebea5833d36
```

The deterministic offline transformer produced a Firestore-shaped target fixture. An independent verifier recomputed the source and target metrics without importing the transformer and returned:

```text
status: verified
errors: []
differences: {}
```

This is a **local readiness baseline**, not a live-data export and not evidence that Firebase production has been configured. No GitHub push, PythonAnywhere change, Cloudflare deployment, or Firebase write was performed.
