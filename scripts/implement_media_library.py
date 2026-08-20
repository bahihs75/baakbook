from pathlib import Path

ROOT = Path('/home/ubuntu/baakbook-local')
ADMIN = ROOT / 'frontend' / 'admin.html'
RULES = ROOT / 'firestore.rules'

html = ADMIN.read_text(encoding='utf-8')

# 1) Add styling for the media library, image pickers, and previews.
css_anchor = "    .hero-admin-settings,.hero-slide-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.hero-slide-card"
css_insert = """    .image-input-row{display:flex;gap:8px;align-items:center}.image-input-row input{flex:1;min-width:0}.image-input-row button{white-space:nowrap;padding:8px 12px}.image-preview{display:block;width:72px;height:96px;object-fit:cover;border-radius:10px;background:#eee;margin-top:8px}.media-toolbar{display:flex;gap:10px;align-items:end;flex-wrap:wrap;margin:16px 0}.media-toolbar .form-group{flex:1;min-width:220px;margin-bottom:0}.media-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(170px,1fr));gap:14px;margin-top:18px}.media-card{border:1px solid rgba(0,0,0,.07);border-radius:var(--radius-md);background:rgba(255,255,255,.5);padding:10px;min-width:0}.media-card img{display:block;width:100%;height:150px;object-fit:cover;border-radius:10px;background:#eee}.media-meta{font-size:11px;color:var(--text-secondary);margin:8px 2px;word-break:break-word}.media-card-actions{display:flex;gap:6px;flex-wrap:wrap}.media-card-actions button{padding:7px 9px;font-size:11px}.media-empty{grid-column:1/-1;padding:28px;border:1px dashed rgba(0,0,0,.15);border-radius:var(--radius-md);color:var(--text-secondary);text-align:center}.media-status{font-size:12px;color:var(--text-secondary);min-height:22px}.media-picker-grid{max-height:60vh;overflow-y:auto}.media-picker-grid .media-card{cursor:pointer}.media-picker-grid .media-card:hover{border-color:var(--accent)}\n\n    .hero-admin-settings,.hero-slide-form{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.hero-slide-card"""
if css_anchor not in html:
    raise SystemExit('CSS anchor not found')
html = html.replace(css_anchor, css_insert, 1)

# 2) Add media tab.
tab_anchor = '        <button class="tab" data-tab="hero">🎞️ إدارة الـHero</button>\n'
if tab_anchor not in html:
    raise SystemExit('tab anchor not found')
html = html.replace(tab_anchor, tab_anchor + '        <button class="tab" data-tab="media">🖼️ مكتبة الصور</button>\n', 1)

# 3) Add media panel before orders panel.
panel_anchor = '      <!-- قسم الطلبات -->\n      <div class="panel" id="panel-orders">'
media_panel = '''      <!-- مكتبة الصور -->
      <div class="panel" id="panel-media">
        <div class="card">
          <h2 style="font-size:20px; margin-bottom:6px;">مكتبة الصور</h2>
          <p class="feature-intro">ارفع الصور مباشرة إلى ImgBB، ثم احفظ رابطها في مكتبة Baak Books لاستخدامها لاحقًا في أغلفة الكتب وشرائح الـHero. حذف الصورة من هنا يحذف سجلها من المكتبة فقط ولا يحذفها من ImgBB.</p>
          <div class="admin-note"><strong>ملاحظة أمان:</strong> مفتاح ImgBB لا يوجد في GitHub ولا في الصفحة العامة. يحفظ داخل Firestore في سجل محمي للمدير، ويُقرأ عند فتح هذه التبويبة فقط. أثناء الرفع يظهر للمسؤول المصادق عليه في المتصفح لأن ImgBB يتطلبه في طلب الرفع.</div>
          <div class="media-toolbar">
            <div class="form-group"><label for="imgbbApiKey">مفتاح ImgBB</label><input id="imgbbApiKey" type="password" autocomplete="new-password" placeholder="أدخل المفتاح أو اتركه لقراءة المفتاح المحفوظ"></div>
            <button class="btn-secondary" id="toggleImgbbKey" type="button">إظهار/إخفاء</button>
            <button class="btn-primary" id="saveImgbbKey" type="button">حفظ المفتاح</button>
          </div>
          <div class="media-toolbar">
            <div class="form-group"><label for="mediaFileInput">صور جديدة</label><input id="mediaFileInput" type="file" accept="image/*,.svg" multiple></div>
            <button class="add-btn" id="uploadMediaBtn" type="button">⬆️ رفع الصور إلى ImgBB</button>
          </div>
          <div id="mediaUploadStatus" class="media-status" aria-live="polite"></div>
          <div id="mediaGrid" class="media-grid"></div>
        </div>
      </div>

      <!-- قسم الطلبات -->
      <div class="panel" id="panel-orders">'''
if panel_anchor not in html:
    raise SystemExit('orders panel anchor not found')
html = html.replace(panel_anchor, media_panel, 1)

# 4) Add picker buttons to product image field.
old_product_img = '        <div class="form-group"><label>رابط صورة الغلاف</label><input id="prodImg"></div>'
new_product_img = '''        <div class="form-group"><label>صورة الغلاف</label><div class="image-input-row"><input id="prodImg" type="url" placeholder="https://..."><button class="btn-secondary" id="pickProdImage" type="button">اختيار من المكتبة</button></div><img id="prodImgPreview" class="image-preview" alt="معاينة غلاف الكتاب" style="display:none"></div>'''
if old_product_img not in html:
    raise SystemExit('product image field not found')
html = html.replace(old_product_img, new_product_img, 1)

# 5) Add picker modal before order detail modal.
modal_anchor = '    <!-- مودال تفاصيل الطلب -->\n    <div class="modal" id="orderDetailModal">'
picker_modal = '''    <!-- مودال اختيار صورة من المكتبة -->
    <div class="modal" id="mediaPickerModal">
      <div class="modal-content" style="max-width: 760px;">
        <h3>اختيار صورة من مكتبة الصور</h3>
        <p class="feature-intro">اختر صورة محفوظة في المكتبة. يمكنك رفع صورة جديدة من تبويب «مكتبة الصور» ثم العودة إلى هنا.</p>
        <div id="mediaPickerGrid" class="media-grid media-picker-grid"></div>
        <div class="form-actions"><button class="btn-secondary" id="closeMediaPicker" type="button">إلغاء</button></div>
      </div>
    </div>

    <!-- مودال تفاصيل الطلب -->
    <div class="modal" id="orderDetailModal">'''
if modal_anchor not in html:
    raise SystemExit('order modal anchor not found')
html = html.replace(modal_anchor, picker_modal, 1)

# 6) Add state and helpers after findNamedDocument.
state_anchor = "    // Direct Firebase Auth + Firestore adapter. It intentionally keeps the\n"
state_block = r'''    let mediaState = { items: [], target: null, key: '' };

    function normalizeMediaItem(raw) {
      return {
        id: raw.id || '',
        url: raw.url || raw.display_url || '',
        display_url: raw.display_url || raw.url || '',
        delete_url: raw.delete_url || '',
        name: raw.name || raw.title || 'صورة بدون اسم',
        width: Number(raw.width || 0),
        height: Number(raw.height || 0),
        size: Number(raw.size || 0),
        createdAt: raw.createdAt || ''
      };
    }

    function formatMediaDate(value) {
      if (!value) return '—';
      const date = new Date(value);
      return Number.isNaN(date.getTime()) ? '—' : date.toLocaleDateString('ar-DZ');
    }

    function validateMediaFile(file) {
      if (!file) throw new Error('اختر صورة أولًا');
      if (!(file.type || '').startsWith('image/') && file.type !== 'image/svg+xml') throw new Error('الملف يجب أن يكون صورة');
      if (file.size > 12 * 1024 * 1024) throw new Error('حجم الصورة يجب ألا يتجاوز 12 ميغابايت');
      if (file.type === 'image/svg+xml') {
        return file.text().then(text => {
          if (!/<svg[\\s>]/i.test(text) || /<script|foreignObject|javascript:|on[a-z]+\\s*=/i.test(text)) throw new Error('ملف SVG غير مسموح به لأسباب أمنية');
          return file;
        });
      }
      return Promise.resolve(file);
    }

    async function compressMediaFile(file) {
      if (file.type === 'image/svg+xml' || file.size <= 2 * 1024 * 1024) return file;
      const objectUrl = URL.createObjectURL(file);
      try {
        const image = await new Promise((resolve, reject) => { const img = new Image(); img.onload = () => resolve(img); img.onerror = reject; img.src = objectUrl; });
        const maxSide = 2400;
        const scale = Math.min(1, maxSide / Math.max(image.naturalWidth || image.width, image.naturalHeight || image.height));
        const canvas = document.createElement('canvas');
        canvas.width = Math.max(1, Math.round((image.naturalWidth || image.width) * scale));
        canvas.height = Math.max(1, Math.round((image.naturalHeight || image.height) * scale));
        canvas.getContext('2d').drawImage(image, 0, 0, canvas.width, canvas.height);
        const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.86));
        return blob && blob.size < file.size ? new File([blob], file.name.replace(/\\.[^.]+$/, '.jpg'), { type: 'image/jpeg' }) : file;
      } finally { URL.revokeObjectURL(objectUrl); }
    }

    async function loadImgbbKey() {
      const snapshot = await getDoc(doc(db, 'adminSecrets', 'imgbb'));
      mediaState.key = snapshot.exists() ? String(snapshot.data()?.apiKey || '') : '';
      if ($('imgbbApiKey')) $('imgbbApiKey').value = mediaState.key;
      return mediaState.key;
    }

    async function saveImgbbKey() {
      const key = $('imgbbApiKey').value.trim();
      if (!key) return toast('أدخل مفتاح ImgBB أولًا', 'error');
      await setDoc(doc(db, 'adminSecrets', 'imgbb'), { apiKey: key, updatedAt: serverTimestamp(), updatedBy: auth.currentUser?.email || '' }, { merge: true });
      mediaState.key = key;
      toast('تم حفظ مفتاح ImgBB في سجل المدير', 'success');
    }

    async function uploadMediaToImgBB(file, apiKey) {
      const prepared = await compressMediaFile(await validateMediaFile(file));
      const form = new FormData();
      form.append('image', prepared);
      const response = await fetch(`https://api.imgbb.com/1/upload?key=${encodeURIComponent(apiKey)}`, { method: 'POST', body: form });
      let payload = null;
      try { payload = await response.json(); } catch (_) { payload = null; }
      if (!response.ok || !payload?.success || !payload?.data?.url) throw new Error(payload?.error?.message || 'فشل رفع الصورة إلى ImgBB');
      return { ...payload.data, name: file.name };
    }

    async function loadMediaLibrary() {
      try {
        const snapshots = await getDocs(collection(db, 'imageLibrary'));
        mediaState.items = snapshots.docs.map(rawData).map(normalizeMediaItem).filter(item => item.url).sort((a, b) => String(b.createdAt).localeCompare(String(a.createdAt)));
        renderMediaGrid();
        await loadImgbbKey();
      } catch (error) { toast('تعذر تحميل مكتبة الصور', 'error'); }
    }

    function mediaCard(item, picker = false) {
      const safeUrl = adminEsc(item.display_url || item.url);
      const safeName = adminEsc(item.name);
      return `<div class="media-card" data-media-id="${adminEsc(item.id)}">
        <img src="${safeUrl}" alt="${safeName}" loading="lazy" onerror="this.style.opacity=.35">
        <div class="media-meta"><strong>${safeName}</strong><br>${item.width && item.height ? `${item.width}×${item.height} · ` : ''}${formatMediaDate(item.createdAt)}</div>
        <div class="media-card-actions">${picker ? `<button type="button" class="btn-primary choose-media" data-id="${adminEsc(item.id)}">اختيار</button>` : `<button type="button" class="btn-secondary copy-media-url" data-id="${adminEsc(item.id)}">نسخ الرابط</button><button type="button" class="btn-secondary delete-media" data-id="${adminEsc(item.id)}">حذف من المكتبة</button>`}</div>
      </div>`;
    }

    function renderMediaGrid() {
      const html = mediaState.items.length ? mediaState.items.map(item => mediaCard(item)).join('') : '<div class="media-empty">لا توجد صور محفوظة بعد. ارفع أول صورة لتظهر هنا.</div>';
      const grid = $('mediaGrid');
      if (grid) grid.innerHTML = html;
      document.querySelectorAll('.copy-media-url').forEach(button => button.onclick = async () => { const item = mediaState.items.find(entry => entry.id === button.dataset.id); if (!item) return; try { await navigator.clipboard.writeText(item.url); toast('تم نسخ رابط الصورة', 'success'); } catch (_) { toast(item.url); } });
      document.querySelectorAll('.delete-media').forEach(button => button.onclick = async () => { const item = mediaState.items.find(entry => entry.id === button.dataset.id); if (!item || !confirm('حذف سجل الصورة من مكتبة Baak Books؟ لن تُحذف الصورة من ImgBB.')) return; try { await deleteDoc(doc(db, 'imageLibrary', item.id)); mediaState.items = mediaState.items.filter(entry => entry.id !== item.id); renderMediaGrid(); toast('تم حذف الصورة من المكتبة', 'success'); } catch (error) { toast('تعذر حذف الصورة من المكتبة', 'error'); } });
    }

    function openMediaPicker(target) {
      mediaState.target = target;
      const grid = $('mediaPickerGrid');
      grid.innerHTML = mediaState.items.length ? mediaState.items.map(item => mediaCard(item, true)).join('') : '<div class="media-empty">المكتبة فارغة. ارفع صورة من تبويب «مكتبة الصور» أولًا.</div>';
      $('mediaPickerModal').classList.add('open');
      document.querySelectorAll('.choose-media').forEach(button => button.onclick = () => { const item = mediaState.items.find(entry => entry.id === button.dataset.id); if (item && mediaState.target?.input) { mediaState.target.input.value = item.url; mediaState.target.input.dispatchEvent(new Event('input', { bubbles: true })); } $('mediaPickerModal').classList.remove('open'); mediaState.target = null; });
    }

    async function uploadSelectedMedia() {
      const files = [...($('mediaFileInput').files || [])];
      if (!files.length) return toast('اختر صورة واحدة على الأقل', 'error');
      const apiKey = $('imgbbApiKey').value.trim() || mediaState.key || await loadImgbbKey();
      if (!apiKey) return toast('احفظ مفتاح ImgBB أولًا', 'error');
      const status = $('mediaUploadStatus');
      let completed = 0;
      try {
        for (const file of files) {
          status.textContent = `جارٍ رفع ${file.name}…`;
          const result = await uploadMediaToImgBB(file, apiKey);
          const id = (crypto.randomUUID ? crypto.randomUUID() : `media-${Date.now()}-${completed}`);
          await setDoc(doc(db, 'imageLibrary', id), { id, url: result.url, display_url: result.display_url || result.url, delete_url: result.delete_url || '', name: result.name || file.name, width: Number(result.width || 0), height: Number(result.height || 0), size: Number(result.size || file.size || 0), type: result.type || file.type, createdAt: new Date().toISOString(), createdBy: auth.currentUser?.email || '' });
          completed += 1;
        }
        $('mediaFileInput').value = '';
        status.textContent = `اكتمل رفع ${completed} صورة.`;
        await loadMediaLibrary();
        toast(`تم رفع ${completed} صورة`, 'success');
      } catch (error) { status.textContent = ''; toast(error.message || 'فشل رفع الصور', 'error'); }
    }

'''
if state_anchor not in html:
    raise SystemExit('state anchor not found')
html = html.replace(state_anchor, state_block + state_anchor, 1)

# 7) Extend tab switching to load the media panel.
old_tab = "        else if (target === 'hero') loadHeroEditor();"
new_tab = "        else if (target === 'hero') loadHeroEditor();\n        else if (target === 'media') loadMediaLibrary();"
if old_tab not in html:
    raise SystemExit('tab switch anchor not found')
html = html.replace(old_tab, new_tab, 1)

# 8) Fix editProduct by reading the product directly instead of unsupported GET /:id.
start = html.index('    async function editProduct(id) {')
end = html.index('\n    $(\'cancelModal\').onclick', start)
new_edit = '''    async function editProduct(id) {
      try {
        const snapshot = await getDoc(doc(db, 'products', id));
        if (!snapshot.exists()) throw new Error('الكتاب غير موجود');
        const p = rawData(snapshot);
        $('prodId').value = p.id;
        $('prodId').disabled = true;
        $('prodTitle').value = p.title || '';
        $('prodCategory').value = p.category || 'روايات';
        $('prodDesc').value = p.desc || '';
        $('prodImg').value = p.img || '';
        updateProductImagePreview();
        $('prodPrice').value = p.price || 0;
        $('prodStock').value = p.stock_quantity || 0;
        $('prodAvailability').value = p.availability_type || 'in_stock';
        $('prodLeadDuration').value = String(Math.min(1, Math.max(0, Number(p.lead_time_max_days ?? p.lead_time_days ?? 0))));
        $('prodDiscoveryTags').value = (p.discovery_tags || []).join(', ');
        $('prodGiftTags').value = (p.gift_tags || []).join(', ');
        $('prodGiftable').checked = p.giftable !== false;
        $('prodDiscoverable').checked = p.discoverable !== false;
        $('prodFeatured').checked = Boolean(p.featured);
        $('prodActive').checked = p.active !== false;
        $('modalTitle').textContent = 'تعديل بيانات الكتاب';
        $('productModal').classList.add('open');
      } catch (err) { toast(err.message || 'تعذر تحميل بيانات الكتاب', 'error'); }
    }
'''
html = html[:start] + new_edit + html[end:]

# 9) Remove competing window.onclick assignments; one delegated handler is installed below.
html = html.replace("    window.onclick = (e) => { if (e.target === $('productModal')) $('productModal').classList.remove('open'); };\n", '', 1)
html = html.replace("    window.onclick = (e) => {\n      if (e.target === $('orderDetailModal')) $('orderDetailModal').classList.remove('open');\n    };\n", '', 1)

# 10) Fix category add/edit handler collision.
cat_start = html.index('    function editCategory(name) {')
cat_end = html.index('\n    async function deleteCategory(name) {', cat_start)
new_cat = '''    let editingCategoryName = null;
    function editCategory(name) {
      editingCategoryName = name;
      $('catName').value = name;
      $('catModalTitle').textContent = 'تعديل التصنيف';
      $('categoryModal').classList.add('open');
    }

    $('saveCategory').onclick = async () => {
      const name = $('catName').value.trim();
      if (!name) return toast('الاسم مطلوب', 'error');
      try {
        const isEditing = Boolean(editingCategoryName);
        const path = isEditing ? `${API_BASE}/admin/categories/${encodeURIComponent(editingCategoryName)}` : `${API_BASE}/admin/categories`;
        const res = await adminFetch(path, { method: isEditing ? 'PUT' : 'POST', headers: apiHeaders(), body: JSON.stringify({ name }) });
        if (!res.ok) { const payload = await res.json(); throw new Error(payload.error || 'تعذر حفظ التصنيف'); }
        $('categoryModal').classList.remove('open');
        editingCategoryName = null;
        toast(isEditing ? 'تم تعديل التصنيف' : 'تمت إضافة التصنيف', 'success');
        await loadCategories();
        await loadProducts();
      } catch (e) { toast(e.message || String(e), 'error'); }
    };
'''
html = html[:cat_start] + new_cat + html[cat_end:]
html = html.replace("      $('catName').value = '';\n      $('catModalTitle').textContent = 'إضافة تصنيف';", "      editingCategoryName = null;\n      $('catName').value = '';\n      $('catModalTitle').textContent = 'إضافة تصنيف';", 1)

# 11) Add media handlers and product image helpers immediately before PRODUCTS section.
products_anchor = "    // ========== PRODUCTS ==========\n"
product_helpers = '''    function updateProductImagePreview() {
      const url = $('prodImg')?.value.trim();
      const preview = $('prodImgPreview');
      if (!preview) return;
      preview.src = url || '';
      preview.style.display = url ? 'block' : 'none';
    }

    $('prodImg')?.addEventListener('input', updateProductImagePreview);
    $('pickProdImage')?.addEventListener('click', async () => { if (!mediaState.items.length) await loadMediaLibrary(); openMediaPicker({ type: 'product', input: $('prodImg') }); });
    $('toggleImgbbKey')?.addEventListener('click', () => { const input = $('imgbbApiKey'); input.type = input.type === 'password' ? 'text' : 'password'; });
    $('saveImgbbKey')?.addEventListener('click', async () => { try { await saveImgbbKey(); } catch (error) { toast(error.message || 'تعذر حفظ مفتاح ImgBB', 'error'); } });
    $('uploadMediaBtn')?.addEventListener('click', uploadSelectedMedia);
    $('closeMediaPicker')?.addEventListener('click', () => { $('mediaPickerModal').classList.remove('open'); mediaState.target = null; });

'''
if products_anchor not in html:
    raise SystemExit('products anchor not found')
html = html.replace(products_anchor, product_helpers + products_anchor, 1)

# 12) Update clearModal to refresh image preview.
html = html.replace("      $('prodImg').value = '';\n", "      $('prodImg').value = '';\n      updateProductImagePreview();\n", 1)

# 13) Add hero image library button and event binding.
old_hero_image = '<div class="form-group wide"><label>صورة الخلفية (URL)</label><input class="s-image" type="url" maxlength="700" value="${adminEsc(slide.image)}" placeholder="https://..."><img class="hero-slide-preview" src="${adminEsc(slide.image)}" alt="معاينة الصورة" onerror="this.style.display=\'none\'" onload="this.style.display=\'block\'"></div>'
new_hero_image = '<div class="form-group wide"><label>صورة الخلفية</label><div class="image-input-row"><input class="s-image" type="url" maxlength="700" value="${adminEsc(slide.image)}" placeholder="https://..."><button type="button" class="btn-secondary pick-hero-image">اختيار من المكتبة</button></div><img class="hero-slide-preview" src="${adminEsc(slide.image)}" alt="معاينة الصورة" onerror="this.style.display=\'none\'" onload="this.style.display=\'block\'"></div>'
if old_hero_image not in html:
    raise SystemExit('hero image field not found')
html = html.replace(old_hero_image, new_hero_image, 1)
hero_bind_anchor = "        card.querySelector('.s-image')?.addEventListener('input', event => { const preview = card.querySelector('.hero-slide-preview'); preview.src = event.target.value.trim(); preview.style.display = event.target.value.trim() ? 'block' : 'none'; });\n"
hero_bind_new = hero_bind_anchor + "        card.querySelector('.pick-hero-image')?.addEventListener('click', async () => { if (!mediaState.items.length) await loadMediaLibrary(); openMediaPicker({ type: 'hero', input: card.querySelector('.s-image') }); });\n"
if hero_bind_anchor not in html:
    raise SystemExit('hero bind anchor not found')
html = html.replace(hero_bind_anchor, hero_bind_new, 1)

# 14) Add one delegated modal closer after logout handler.
logout_anchor = "    $('logoutBtn').onclick = async () => { await signOut(auth); $('passwordInput').value = ''; showLogin(); };\n"
modal_handler = logout_anchor + "    document.addEventListener('click', event => { ['productModal', 'categoryModal', 'orderDetailModal', 'mediaPickerModal'].forEach(id => { const modal = $(id); if (modal && event.target === modal) modal.classList.remove('open'); }); });\n"
if logout_anchor not in html:
    raise SystemExit('logout anchor not found')
html = html.replace(logout_anchor, modal_handler, 1)

ADMIN.write_text(html, encoding='utf-8')

rules = RULES.read_text(encoding='utf-8')
secret_anchor = "    match /imageLibrary/{imageId} {\n      allow read, write: if isAdmin();\n    }\n"
secret_block = secret_anchor + "\n    match /adminSecrets/{secretId} {\n      allow read, write: if isAdmin();\n    }\n"
if 'match /adminSecrets/{secretId}' not in rules:
    if secret_anchor not in rules:
        raise SystemExit('rules imageLibrary anchor not found')
    rules = rules.replace(secret_anchor, secret_block, 1)
    RULES.write_text(rules, encoding='utf-8')

print('UPDATED', ADMIN)
print('UPDATED', RULES)
