from pathlib import Path

path = Path('/home/ubuntu/baakbook-local/frontend/admin.html')
text = path.read_text()

old = """    function rawData(snapshot) {
      const data = snapshot.data() || {};
      const result = { ...data, id: snapshot.id };
      for (const [key, value] of Object.entries(result)) {
        if (value && typeof value === 'object' && typeof value.toDate === 'function') result[key] = value.toDate().toISOString();
      }
      return result;
    }
"""
new = """    function rawData(snapshot) {
      const data = snapshot.data() || {};
      const result = { ...data, id: snapshot.id };
      for (const [key, value] of Object.entries(result)) {
        if (value && typeof value === 'object' && typeof value.toDate === 'function') result[key] = value.toDate().toISOString();
      }
      return result;
    }

    // Products may have a historical mismatch between the Firestore document id
    // and the business id stored in the document. Keep both values explicit.
    function adminProductData(snapshot) {
      const data = snapshot.data() || {};
      const result = { ...data, id: data.id || snapshot.id, docId: snapshot.id };
      for (const [key, value] of Object.entries(result)) {
        if (value && typeof value === 'object' && typeof value.toDate === 'function') result[key] = value.toDate().toISOString();
      }
      return result;
    }

    async function findProductSnapshot(id) {
      const direct = await getDoc(doc(db, 'products', id));
      if (direct.exists()) return direct;
      const matches = await getDocs(query(collection(db, 'products'), where('id', '==', id)));
      return matches.empty ? null : matches.docs[0];
    }
"""
if old not in text:
    raise SystemExit('rawData block not found')
text = text.replace(old, new, 1)

old = """            const snapshots = await getDocs(collection(db, 'products'));
            return directResponse(snapshots.docs.map(rawData));
"""
new = """            const snapshots = await getDocs(collection(db, 'products'));
            return directResponse(snapshots.docs.map(adminProductData));
"""
if old not in text:
    raise SystemExit('products GET block not found')
text = text.replace(old, new, 1)

old = """    function renderProductsTable(products) {
"""
new = """    let editingProductDocId = '';

    function renderProductsTable(products) {
"""
if old not in text:
    raise SystemExit('renderProductsTable marker not found')
text = text.replace(old, new, 1)

old = """            <button class="copy-link" data-id="${p.id}" title="نسخ رابط الكتاب">🔗</button>
            <button class="edit" data-id="${p.id}">✏️</button>
            <button class="delete" data-id="${p.id}">🗑️</button>
"""
new = """            <button class="copy-link" data-id="${p.id}" title="نسخ رابط الكتاب">🔗</button>
            <button class="edit" data-doc-id="${p.docId || p.id}" data-id="${p.id}">✏️</button>
            <button class="delete" data-doc-id="${p.docId || p.id}" data-id="${p.id}">🗑️</button>
"""
if old not in text:
    raise SystemExit('product action buttons block not found')
text = text.replace(old, new, 1)

old = """      $('prodId').value = '';
      $('prodId').disabled = false;
"""
new = """      editingProductDocId = '';
      $('prodId').value = '';
      $('prodId').disabled = false;
"""
if old not in text:
    raise SystemExit('clear modal marker not found')
text = text.replace(old, new, 1)

old = """      document.querySelectorAll('#productsTable .edit').forEach(btn => {
        btn.onclick = () => editProduct(btn.dataset.id);
      });
      document.querySelectorAll('#productsTable .delete').forEach(btn => {
        btn.onclick = () => deleteProduct(btn.dataset.id);
      });
"""
new = """      document.querySelectorAll('#productsTable .edit').forEach(btn => {
        btn.onclick = () => editProduct(btn.dataset.docId || btn.dataset.id);
      });
      document.querySelectorAll('#productsTable .delete').forEach(btn => {
        btn.onclick = () => deleteProduct(btn.dataset.docId || btn.dataset.id);
      });
"""
if old not in text:
    raise SystemExit('product event block not found')
text = text.replace(old, new, 1)

old = """    async function editProduct(id) {
      try {
        const snapshot = await getDoc(doc(db, 'products', id));
        if (!snapshot.exists()) throw new Error('الكتاب غير موجود');
        const p = rawData(snapshot);
"""
new = """    async function editProduct(id) {
      try {
        const snapshot = await findProductSnapshot(id);
        if (!snapshot) throw new Error('الكتاب غير موجود');
        const p = adminProductData(snapshot);
        editingProductDocId = snapshot.id;
"""
if old not in text:
    raise SystemExit('editProduct start block not found')
text = text.replace(old, new, 1)

old = """        } else {
          res = await adminFetch(`${API_BASE}/admin/products/${id}`, {
            method: 'PUT', headers: apiHeaders(), body: JSON.stringify(data)
          });
"""
new = """        } else {
          const documentId = editingProductDocId || id;
          res = await adminFetch(`${API_BASE}/admin/products/${encodeURIComponent(documentId)}`, {
            method: 'PUT', headers: apiHeaders(), body: JSON.stringify(data)
          });
"""
if old not in text:
    raise SystemExit('save update block not found')
text = text.replace(old, new, 1)

path.write_text(text)
print('UPDATED', path)
print('CHANGES', 7)
