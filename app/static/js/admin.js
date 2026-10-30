/**
 * PRIME APPS — Admin Backoffice JS
 * Handles Product Images Upload, Reorder, Order Status Flow, License Override, and Analytics Charts
 */

// Native SVG Chart Generator (Dependency-Free, Ultra-Crisp)
function renderSalesChart(containerId, dataPoints) {
  const container = document.getElementById(containerId);
  if (!container || !dataPoints || dataPoints.length === 0) return;

  const width = container.clientWidth || 600;
  const height = 240;
  const padding = { top: 20, right: 20, bottom: 40, left: 60 };

  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  const maxVal = Math.max(...dataPoints.map(d => d.value), 100000);
  const stepX = innerWidth / (dataPoints.length - 1 || 1);

  let pathD = '';
  let areaD = `M ${padding.left} ${height - padding.bottom} `;
  let pointsHtml = '';

  dataPoints.forEach((d, i) => {
    const x = padding.left + i * stepX;
    const y = padding.top + innerHeight - (d.value / maxVal) * innerHeight;

    if (i === 0) {
      pathD += `M ${x} ${y} `;
      areaD += `L ${x} ${y} `;
    } else {
      pathD += `L ${x} ${y} `;
      areaD += `L ${x} ${y} `;
    }

    pointsHtml += `
      <circle cx="${x}" cy="${y}" r="4" fill="#0071e3" stroke="#ffffff" stroke-width="2">
        <title>${d.label}: Rp ${d.value.toLocaleString('id-ID')}</title>
      </circle>
      <text x="${x}" y="${height - 15}" font-size="11" fill="#86868b" text-anchor="middle">${d.label}</text>
    `;
  });

  areaD += `L ${padding.left + (dataPoints.length - 1) * stepX} ${height - padding.bottom} Z`;

  const svg = `
    <svg width="100%" height="${height}" viewBox="0 0 ${width} ${height}" style="overflow: visible;">
      <defs>
        <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#0071e3" stop-opacity="0.25"/>
          <stop offset="100%" stop-color="#0071e3" stop-opacity="0.0"/>
        </linearGradient>
      </defs>
      <!-- Grid lines -->
      <line x1="${padding.left}" y1="${padding.top}" x2="${width - padding.right}" y2="${padding.top}" stroke="rgba(0,0,0,0.06)" stroke-dasharray="3"/>
      <line x1="${padding.left}" y1="${padding.top + innerHeight / 2}" x2="${width - padding.right}" y2="${padding.top + innerHeight / 2}" stroke="rgba(0,0,0,0.06)" stroke-dasharray="3"/>
      <line x1="${padding.left}" y1="${height - padding.bottom}" x2="${width - padding.right}" y2="${height - padding.bottom}" stroke="rgba(0,0,0,0.1)"/>
      <!-- Y-Axis labels -->
      <text x="${padding.left - 10}" y="${padding.top + 4}" font-size="10" fill="#86868b" text-anchor="end">Rp ${(maxVal/1000).toFixed(0)}k</text>
      <text x="${padding.left - 10}" y="${padding.top + innerHeight/2 + 4}" font-size="10" fill="#86868b" text-anchor="end">Rp ${(maxVal/2000).toFixed(0)}k</text>
      <text x="${padding.left - 10}" y="${height - padding.bottom + 4}" font-size="10" fill="#86868b" text-anchor="end">Rp 0</text>
      <!-- Area & Line -->
      <path d="${areaD}" fill="url(#areaGrad)"/>
      <path d="${pathD}" fill="none" stroke="#0071e3" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
      <!-- Points -->
      ${pointsHtml}
    </svg>
  `;

  container.innerHTML = svg;
}

// Multi-Image Upload & Management for Product Form
const AdminImageManager = {
  productId: null,
  
  init(productId) {
    this.productId = productId;
    const dropzone = document.getElementById('image-dropzone');
    const fileInput = document.getElementById('product-images-input');

    if (!dropzone || !fileInput) return;

    dropzone.addEventListener('click', () => fileInput.click());
    
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'var(--accent)';
      dropzone.style.background = 'var(--accent-subtle)';
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.style.borderColor = 'var(--border-default)';
      dropzone.style.background = 'var(--bg-surface)';
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.style.borderColor = 'var(--border-default)';
      dropzone.style.background = 'var(--bg-surface)';
      if (e.dataTransfer.files.length > 0) {
        this.uploadFiles(e.dataTransfer.files);
      }
    });

    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        this.uploadFiles(fileInput.files);
      }
    });
  },

  async uploadFiles(fileList) {
    if (!this.productId) {
      alert('Simpan informasi produk terlebih dahulu sebelum mengunggah gambar.');
      return;
    }

    showToast(`Mengunggah ${fileList.length} gambar...`, 'info');

    for (let i = 0; i < fileList.length; i++) {
      const file = fileList[i];
      const formData = new FormData();
      formData.append('file', file);
      formData.append('alt_text', file.name);

      try {
        const res = await fetch(`/api/admin/products/${this.productId}/images`, {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Upload gagal');
        
        showToast(`Berhasil upload: ${file.name}`, 'success');
        this.appendImageCard(data);
      } catch (err) {
        showToast(`Gagal upload ${file.name}: ${err.message}`, 'error');
      }
    }
  },

  appendImageCard(img) {
    const grid = document.getElementById('uploaded-images-grid');
    if (!grid) return;

    const card = document.createElement('div');
    card.id = `img-card-${img.id}`;
    card.className = 'uploaded-img-card';
    card.style.cssText = 'position: relative; border-radius: 8px; overflow: hidden; border: 1px solid var(--border-default); background: var(--bg-surface); aspect-ratio: 1;';
    
    card.innerHTML = `
      <img src="${img.thumbnail_url || img.image_url}" style="width:100%; height:100%; object-fit:cover;">
      <div style="position: absolute; top: 6px; right: 6px; display: flex; gap: 4px;">
        <button type="button" onclick="AdminImageManager.deleteImage(${img.id})" class="btn btn-sm btn-danger" style="padding: 2px 6px; font-size: 11px;">Hapus</button>
      </div>
      <div style="position: absolute; bottom: 6px; left: 6px;">
        ${img.is_primary ? '<span class="badge badge-success" style="font-size:10px;">Utama</span>' : `<button type="button" onclick="AdminImageManager.setPrimary(${img.id})" class="btn btn-sm btn-secondary" style="padding: 2px 6px; font-size: 10px;">Jadikan Utama</button>`}
      </div>
    `;
    grid.appendChild(card);
  },

  async deleteImage(imageId) {
    if (!confirm('Yakin ingin menghapus foto produk ini secara permanen?')) return;

    try {
      const res = await fetch(`/api/admin/products/${this.productId}/images/${imageId}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Gagal menghapus');
      
      const el = document.getElementById(`img-card-${imageId}`);
      if (el) el.remove();
      showToast('Foto berhasil dihapus dari storage!', 'info');
      window.location.reload();
    } catch (err) {
      showToast(err.message, 'error');
    }
  },

  async setPrimary(imageId) {
    try {
      const res = await fetch(`/api/admin/products/${this.productId}/images/${imageId}/primary`, {
        method: 'POST'
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Gagal mengubah foto utama');
      showToast('Foto utama berhasil diperbarui', 'success');
      window.location.reload();
    } catch (err) {
      showToast(err.message, 'error');
    }
  }
};

// Quick Toggle Product Active / Draft Status from Table
async function toggleProductActive(productId, checkbox) {
  const newStatus = checkbox.checked ? 'active' : 'draft';
  try {
    const res = await fetch(`/api/admin/products/${productId}/status`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Gagal mengubah status');
    showToast(`Produk sekarang ${newStatus === 'active' ? 'AKTIF di toko' : 'NONAKTIF / DRAFT'}`, 'success');
  } catch (err) {
    showToast(err.message, 'error');
    checkbox.checked = !checkbox.checked; // Revert checkbox
  }
}

// Order Status Transition Helper
async function updateOrderStatus(orderId, newStatus) {
  if (!confirm(`Konfirmasi ubah status pesanan menjadi ${newStatus}?`)) return;

  try {
    const res = await fetch(`/api/admin/orders/${orderId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: newStatus })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Gagal mengubah status');
    showToast('Status pesanan berhasil diperbarui', 'success');
    window.location.reload();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Override Digital License Key for Order Item (Admin Manual Override)
async function overrideOrderLicenseKey(orderId, itemId, currentKey = '') {
  const newKey = prompt('Masukkan atau ubah Kode Serial Lisensi untuk item ini:', currentKey);
  if (newKey === null) return;

  try {
    const res = await fetch(`/api/admin/orders/${orderId}/items/${itemId}/license`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ license_code: newKey.trim() })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Gagal mengubah lisensi');
    showToast('Kode lisensi berhasil disimpan dan diperbarui!', 'success');
    window.location.reload();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// Toggle Customer Status (Active vs Suspended)
async function toggleCustomerStatus(customerId, currentStatus) {
  const nextStatus = currentStatus === 'active' ? 'suspended' : 'active';
  const confirmMsg = nextStatus === 'suspended' ? 
    'Bekukan akun pelanggan ini? Pelanggan tidak akan bisa login.' : 
    'Aktifkan kembali akun pelanggan ini?';
  
  if (!confirm(confirmMsg)) return;

  try {
    const res = await fetch(`/api/admin/customers/${customerId}/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: nextStatus })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Gagal mengubah status pelanggan');
    showToast(`Status akun pelanggan diubah menjadi ${nextStatus.toUpperCase()}`, 'success');
    window.location.reload();
  } catch (err) {
    showToast(err.message, 'error');
  }
}
