/**
 * PRIME APPS — Client Application JS
 * Handles Theme, Cart, Checkout, Gallery, Payment Simulator, and WhatsApp Orders
 */

// Theme Management
(function initTheme() {
  const savedTheme = localStorage.getItem('prime_theme') || 
    (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  document.documentElement.setAttribute('data-theme', savedTheme);
})();

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('prime_theme', next);
  
  const icon = document.getElementById('theme-toggle-icon');
  if (icon) {
    icon.innerHTML = next === 'dark' ? '☀️' : '🌙';
  }
}

// Toast Notifications
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 250);
  }, 3500);
}

// Rupiah Formatter
function formatRupiah(amount) {
  return new Intl.NumberFormat('id-ID', {
    style: 'currency',
    currency: 'IDR',
    maximumFractionDigits: 0
  }).format(amount);
}

// Cart Client Engine
const Cart = {
  async add(productId, quantity = 1) {
    try {
      const res = await fetch('/api/cart/items', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ product_id: productId, quantity: quantity })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Gagal menambahkan produk');
      
      showToast('Produk berhasil ditambahkan ke keranjang!', 'success');
      this.updateBadge(data.total_items);
      return data;
    } catch (err) {
      showToast(err.message, 'error');
    }
  },

  async update(productId, quantity) {
    try {
      const res = await fetch(`/api/cart/items/${productId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quantity: quantity })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Gagal memperbarui keranjang');
      this.updateBadge(data.total_items);
      window.location.reload();
    } catch (err) {
      showToast(err.message, 'error');
    }
  },

  async remove(productId) {
    try {
      const res = await fetch(`/api/cart/items/${productId}`, {
        method: 'DELETE'
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Gagal menghapus produk');
      showToast('Item dihapus dari keranjang', 'info');
      this.updateBadge(data.total_items);
      window.location.reload();
    } catch (err) {
      showToast(err.message, 'error');
    }
  },

  async fetchCount() {
    try {
      const res = await fetch('/api/cart/count');
      if (res.ok) {
        const data = await res.json();
        this.updateBadge(data.count);
      }
    } catch (e) {}
  },

  updateBadge(count) {
    const desktopBadge = document.getElementById('cart-badge-count');
    if (desktopBadge) {
      desktopBadge.textContent = count;
      desktopBadge.style.display = count > 0 ? 'inline-flex' : 'none';
    }
    const mobileBadge = document.getElementById('mobile-cart-badge');
    if (mobileBadge) {
      mobileBadge.textContent = count;
      mobileBadge.style.display = count > 0 ? 'inline-flex' : 'none';
    }
  }
};

// Clipboard Utility
function copyToClipboard(text, elementId = null) {
  navigator.clipboard.writeText(text).then(() => {
    showToast('Berhasil disalin ke clipboard!', 'success');
    if (elementId) {
      const el = document.getElementById(elementId);
      if (el) {
        const originalText = el.textContent;
        el.textContent = 'Tersalin!';
        setTimeout(() => el.textContent = originalText, 2000);
      }
    }
  }).catch(() => {
    showToast('Gagal menyalin text', 'error');
  });
}

// Gallery Switcher for Product Detail
function switchMainImage(thumbElement, fullUrl) {
  const mainImg = document.getElementById('product-gallery-main');
  if (mainImg) {
    mainImg.src = fullUrl;
  }
  document.querySelectorAll('.gallery-thumb-item').forEach(el => el.classList.remove('active'));
  if (thumbElement) {
    thumbElement.classList.add('active');
  }
}

// WhatsApp Order Direct Helper
function orderViaWhatsApp(productName, price, productSlug, storeName = 'PRIME APPS', rawPhone = '+62 812-3456-7890') {
  const cleanPhone = (rawPhone || '6281234567890').replace(/[^0-9]/g, '');
  const url = `${window.location.origin}/product/${productSlug}`;
  const text = encodeURIComponent(
    `Halo Admin ${storeName},\n\nSaya ingin memesan lisensi resmi produk berikut:\n` +
    `• Nama Produk: *${productName}*\n` +
    `• Harga: *Rp ${parseInt(price).toLocaleString('id-ID')}*\n` +
    `• Link: ${url}\n\n` +
    `Mohon info ketersediaan stok lisensi & instruksi pembayarannya (QRIS / Rekening Bank). Terima kasih!`
  );
  window.open(`https://wa.me/${cleanPhone}?text=${text}`, '_blank');
}

// Payment Simulator Poller
let pollerInterval = null;
function startPaymentStatusPolling(orderNumber) {
  if (pollerInterval) clearInterval(pollerInterval);
  
  pollerInterval = setInterval(async () => {
    try {
      const res = await fetch(`/api/orders/${orderNumber}/status`);
      if (res.ok) {
        const data = await res.json();
        if (data.payment_status === 'PAID') {
          clearInterval(pollerInterval);
          showToast('Pembayaran berhasil dikonfirmasi!', 'success');
          setTimeout(() => {
            window.location.href = `/order/${orderNumber}/success`;
          }, 1000);
        }
      }
    } catch (err) {
      console.error('Polling error', err);
    }
  }, 2500);
}

// Simulate Payment Gateway Action
async function simulatePaymentAction(orderNumber, action = 'pay') {
  try {
    const btn = document.getElementById('simulate-pay-btn');
    if (btn) btn.disabled = true;
    showToast('Memproses simulasi pembayaran...', 'info');

    const res = await fetch(`/api/payments/simulate/${orderNumber}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: action })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Gagal memproses simulasi');

    showToast('Pembayaran Berhasil! Mengalihkan ke lisensi digital...', 'success');
    setTimeout(() => {
      window.location.href = `/order/${orderNumber}/success`;
    }, 1200);
  } catch (err) {
    showToast(err.message, 'error');
    const btn = document.getElementById('simulate-pay-btn');
    if (btn) btn.disabled = false;
  }
}

// Auto-run badge check on page load
document.addEventListener('DOMContentLoaded', () => {
  Cart.fetchCount();
});
