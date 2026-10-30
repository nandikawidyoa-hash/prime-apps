# PRIME APPS — Premium Full-Stack Digital Webstore & Admin Backoffice

Platform webstore profesional, modern, dan siap produksi untuk penjualan produk digital, lisensi aplikasi resmi, tools AI, developer tools, dan software bergaransi.

Dibangun dengan filosofi desain terinspirasi dari Apple editorial & modern SaaS: minimalis, responsif, tipografi presisi, dukungan dark/light mode bawaan, serta arsitektur backend full-stack tangguh dengan sistem pengiriman lisensi digital otomatis (*instant license delivery*).

---

## ⚡ Fitur Utama

### 🛍️ Storefront & Customer Portal
1. **Editorial Hero Section:** Menampilkan headline terkonfigurasi, status vault pengiriman instan, trust badge garansi legalitas, dan sorotan kategori.
2. **Katalog Produk Cerdas:** Pencarian instan kata kunci/SKU, filter kategori interaktif, filter produk unggulan, dan pengurutan (Terbaru, Terpopuler, Harga Terendah, Harga Tertinggi).
3. **Detail Produk Editorial:** Galeri multi-foto dengan switcher thumbnail, badge ketersediaan stok lisensi, komparasi harga promo coret, spesifikasi fitur checklist, dan panduan aktivasi.
4. **Keranjang Belanja Real-Time:** Pengaturan kuantitas produk, kalkulasi subtotal instan, dan penghapusan item.
5. **Mesin Kupon Voucher:** Validasi kode promo di backend (tipe persentase % atau nominal tetap Rp), batas minimal belanja, dan batas kuota pemakaian.
6. **Checkout Indonesia:** Input data penerima lisensi (Nama, Email, WhatsApp) dan pemilihan metode pembayaran lokal (QRIS instan, Virtual Account BCA, Mandiri, E-Wallet).
7. **Simulator Pembayaran Gateway:** Tampilan visual dinamis QRIS Standar BI dan nomor Virtual Account dengan fitur salin clipboard, poller status transaksi otomatis, dan simulasi pelunasan webhook untuk pengujian sandbox.
8. **Digital License Key Vault:** Pengiriman instan kode serial lisensi ke layar pelanggan dan akun pengguna tepat setelah pembayaran lunas, dilengkapi tombol satu-klik *Salin Lisensi* dan petunjuk aktivasi resmi.
9. **Dashboard Akun Pelanggan:** Riwayat seluruh transaksi pembelian dan brankas penyimpanan kode lisensi yang dapat diakses kembali kapan saja.
10. **Halaman Informasi Lengkap:** Pusat Bantuan (FAQ), Tentang Kami, Kebijakan Garansi & Refund, Syarat Layanan, Kebijakan Privasi, Formulir Kontak CS, serta 404 & 503 Maintenance Screen.

---

### 🛡️ Dashboard Admin Backoffice
1. **Ringkasan Analitik Dashboard:** Metrik pendapatan aktual, total pesanan masuk, antrian pesanan pending, total pelanggan, jumlah katalog produk aktif, daftar 5 produk terlaris, dan grafik tren penjualan 7 hari terakhir (grafik SVG native tajam tanpa dependensi CDN eksternal).
2. **Manajemen Produk Lengkap:** Tambah, edit, arsipkan, dan hapus produk. Mengatur nama, slug URL, kategori, brand, SKU, harga reguler, harga promo, status aktivasi, fitur, dan SEO meta.
3. **Multi-Image Uploader Dropzone:** Drag-and-drop upload beberapa foto produk sekaligus dari HP atau komputer, sanitasi dan optimasi via Pillow (JPEG/WebP dan auto-generate thumbnail), pemilihan foto utama (primary badge), dan penghapusan permanen dari storage fisik.
4. **Pool Kunci Serial Lisensi (Batch Stock):** Input massal kode lisensi (satu baris per serial). Sistem otomatis mendistribusikan satu kode unik saat order lunas (*idempotent fulfillment*).
5. **Manajemen Pesanan & Alur Status:** Filter pesanan berdasarkan status (PENDING, PAID, FULFILLED, FAILED, REFUNDED), pelunasan manual untuk transfer langsung, tombol pengembalian dana (refund), serta catatan internal admin.
6. **Kategori & Brand:** CRUD kategori produk dengan ikon emoji dan brand publisher resmi.
7. **Voucher & Diskon:** Generator kode promo dengan kuota dan masa aktif.
8. **Pengaturan Toko Fleksibel:** Mengubah nama toko, tagline, teks banner hero, kontak WhatsApp, email support, rekening transfer bank, serta tombol toggle *Maintenance Mode* tanpa perlu merestart server.
9. **Laporan Penjualan & Ekspor CSV:** Filter laporan berdasarkan rentang tanggal kalender, rekapitulasi omset bersih dan tingkat sukses pembayaran, serta tombol unduh file CSV untuk pembukuan akuntansi.
10. **Audit Trail Keamanan:** Pencatatan otomatis setiap aksi administratif sensitif (login, perubahan produk, transaksi, pengaturan) lengkap dengan ID user dan alamat IP.

---

## 🏗️ Arsitektur & Teknologi

| Lapisan | Teknologi | Catatan Rancang Bangun |
|---|---|---|
| **Backend Framework** | **FastAPI 0.92+ (Python 3.11)** | Kecepatan tinggi, typing terstruktur Pydantic, async request handling |
| **Server ASGI** | **Uvicorn** | Standar industri untuk arsitektur modern Python |
| **Database** | **SQLite 3 (WAL Mode + Foreign Keys)** | Ringan, bebas biaya lisensi, dilengkapi indexing performa tinggi |
| **Keamanan Autentikasi** | **PBKDF2-HMAC-SHA256 (100.000 iterasi)** | Standar kriptografi NIST, session cookie bertandatangan HMAC SHA-256 |
| **Otorisasi (RBAC)** | **Superadmin, Admin, Customer** | Isolasi endpoint admin ketat di tingkat middleware dan dependency injection |
| **Media & Storage** | **Pillow (PIL) + Storage Service** | Validasi MIME type mendalam, sanitasi EXIF, kompresi dan thumbnail otomatis |
| **Frontend Styling** | **Modern CSS Design System** | Token CSS Apple & SaaS editorial, dark mode & light mode, responsive Android/iOS/Desktop |
| **Client Script** | **Vanilla Modern JavaScript** | Keranjang dinamis, poller status transaksi, clipboard copy, SVG chart rendering |

---

## 📁 Struktur Direktori Proyek

```
.
├── app/
│   ├── config.py              # Konfigurasi aplikasi, path, dan batasan upload
│   ├── database.py            # Koneksi SQLite, skema tabel, indexing, dan audit log
│   ├── security.py            # Password hashing PBKDF2, session token HMAC, RBAC
│   ├── storage.py             # Validasi MIME file foto, optimasi Pillow, simpan storage
│   ├── models.py              # Schema validasi data input Pydantic
│   ├── main.py                # Inisialisasi FastAPI, middleware maintenance, static mount
│   ├── routers/
│   │   ├── auth.py            # Register, login customer, login admin, logout
│   │   ├── storefront.py      # Halaman katalog, detail produk, keranjang, checkout, static info
│   │   ├── orders.py          # API keranjang, checkout order, voucher apply, status polling
│   │   ├── payments.py        # Simulator pembayaran gateway & webhook handler Midtrans/Xendit
│   │   ├── admin.py           # Dashboard ringkasan analitik, grafik SVG, audit trail
│   │   ├── admin_products.py  # CRUD produk, upload galeri foto, pool lisensi serial
│   │   ├── admin_categories.py# CRUD kategori dan brand
│   │   ├── admin_orders.py    # Manajemen pesanan masuk, alur status, catatan internal
│   │   ├── admin_customers.py # Direktori pelanggan dan riwayat transaksi belanja
│   │   ├── admin_vouchers.py  # Manajemen kode voucher promosi diskon
│   │   └── admin_settings.py  # Pengaturan toko live & ekspor laporan penjualan CSV
│   ├── templates/             # Template Jinja2 responsif
│   │   ├── base.html          # Layout global storefront dengan tema dark/light
│   │   ├── storefront/        # Template index, catalog, product, cart, checkout, payment, success
│   │   └── admin/             # Template overview, products, orders, settings, reports, audit
│   └── static/
│       ├── css/style.css      # Design system CSS bertema Apple & Modern SaaS
│       ├── js/app.js          # Client script keranjang, simulator, tema, clipboard
│       ├── js/admin.js        # Drag-drop uploader foto, render grafik SVG, aksi admin
│       └── uploads/           # Penyimpanan permanen foto produk & thumbnail
├── scripts/
│   ├── seed_data.py           # Seeder produk demo, lisensi resmi, voucher, order sampel
│   └── create_superadmin.py   # CLI aman untuk membuat / mempromosikan Superadmin
├── tests/
│   └── test_suite.py          # Pengujian otomatis end-to-end (Auth, RBAC, Cart, Order, Webhook)
├── bootstrap.py               # Module resolver otomatis
├── run.py                     # Entrypoint server production/development
├── run_tests.py               # Runner pengujian otomatis
├── .env.example               # Contoh variabel lingkungan
└── README.md                  # Dokumentasi teknis lengkap
```

---

## 🚀 Panduan Menjalankan Proyek

### 1. Inisialisasi Basis Data & Data Awal (Seed)
Jalankan script seeder untuk mengisi data awal (kategori, brand, 6 produk digital unggulan, gambar produk asli beresolusi tinggi, kupon voucher, dan akun default):

```bash
python3 scripts/seed_data.py
```

Akun default yang langsung aktif setelah proses seed:
- **Superadmin:** `admin@primeapps.id` | Password: `SuperAdmin2026!`
- **Customer:** `budi@gmail.com` | Password: `Customer2026!`

### 2. Menjalankan Server Aplikasi
Jalankan server Uvicorn:

```bash
python3 run.py
```

Aplikasi webstore langsung dapat diakses di:
- **Storefront Publik:** [http://localhost:8000](http://localhost:8000)
- **Login Admin Panel:** [http://localhost:8000/admin/login](http://localhost:8000/admin/login)
- **Dokumentasi API Interaktif (Swagger UI):** [http://localhost:8000/api/docs](http://localhost:8000/api/docs)

### 3. Menjalankan Pengujian Otomatis
Jalankan seluruh rangkaian test suite untuk memverifikasi integritas sistem:

```bash
python3 run_tests.py
```

---

## 🔐 Cara Membuat Akun Superadmin Baru Secara Mandiri

Untuk membuat akun administrator baru secara aman melalui CLI tanpa melalui antarmuka publik:

```bash
python3 scripts/create_superadmin.py "email_anda@domain.com" "KataSandiKuat2026!" "Nama Lengkap Anda" "0812xxxxxxxx"
```

Password otomatis di-hash menggunakan algoritma **PBKDF2-HMAC-SHA256 (100.000 iterasi)** dengan salt kriptografis unik 16-byte sebelum disimpan ke dalam database.

---

## 📸 Panduan Upload Foto Produk Melalui Dashboard

1. Masuk ke Admin Panel di `/admin/login` menggunakan akun Superadmin.
2. Buka menu **Manajemen Produk** -> Klik **Tambah Produk Baru**.
3. Isi informasi produk (Nama, Kategori, Harga, Deskripsi, Fitur, Serial Keys).
4. Klik tombol **Simpan Data Produk**.
5. Pada form edit yang terbuka, area **Galeri Foto Produk** akan aktif:
   - Tarik & lepas (drag-and-drop) beberapa file gambar (PNG, JPG, WEBP) ke dropzone, atau klik area dropzone untuk memilih dari galeri HP / komputer.
   - Server memvalidasi header MIME type dan struktur byte internal via Pillow, lalu menyimpan file utama dan thumbnail WebP/JPEG ke storage.
   - Anda dapat memilih foto mana yang dijadikan **Foto Utama (Thumbnail)** atau menghapus foto yang salah dengan tombol **Hapus**.
   - Foto otomatis langsung tampil di katalog toko dan halaman detail produk.

---

## 💳 Integrasi Pembayaran Indonesia (Payment Gateway)

Arsitektur sistem telah mengadopsi standar alur kerja payment gateway Indonesia (Midtrans Snap / Core API & Xendit Invoice):

1. **Mode Simulasi Sandbox (Bawaan Aktif):**
   - Saat checkout, pesanan diterbitkan dengan nomor `#PRM-YYYYMMDD-XXXX`.
   - Pada halaman `/payment/{order_number}`, pembeli melihat QRIS dinamis dan nomor Virtual Account.
   - Terdapat panel simulator *Bayar Sekarang* yang menembakkan simulasi status `SETTLEMENT` ke backend.
   - Backend memproses pesanan secara **idempoten**, mengunci stok lisensi serial dari pool, menyimpannya di transaksi, dan menampilkan lisensi secara instan di layar pelanggan.

2. **Beralih ke Gateway Live (Midtrans / Xendit):**
   - Masukkan `MIDTRANS_SERVER_KEY` dan `MIDTRANS_CLIENT_KEY` ke file konfigurasi `.env`.
   - Konfigurasikan Webhook Callback URL di dashboard merchant Midtrans:
     `https://domain-anda.com/api/payments/webhook`
   - Endpoint webhook secara otomatis memvalidasi tanda tangan hash SHA-512 `signature_key` dari Midtrans sebelum melakukan aktivasi lisensi digital.

---

## 🌐 Panduan Deployment ke Server Produksi (VPS / Cloud)

### 1. Menjalankan dengan Systemd Daemon (Linux Ubuntu/Debian)
Buat file service di `/etc/systemd/system/primeapps.service`:

```ini
[Unit]
Description=PRIME APPS Webstore Service
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/primeapps
Environment="PATH=/var/www/primeapps/venv/bin"
EnvironmentFile=/var/www/primeapps/.env
ExecStart=/var/www/primeapps/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

Aktifkan service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now primeapps
```

### 2. Konfigurasi Reverse Proxy Nginx + SSL Let's Encrypt
```nginx
server {
    server_name toko.domainanda.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/uploads/ {
        alias /var/www/primeapps/app/static/uploads/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    client_max_body_size 10M;
}
```

Pasang SSL gratis:
```bash
sudo certbot --nginx -d toko.domainanda.com
```

---

## 📋 Konfigurasi Eksternal yang Perlu Disiapkan Pengguna

Untuk mengaktifkan fitur live tingkat lanjut di luar lingkungan lokal/sandbox:
1. **Midtrans / Xendit Account:** Siapkan Server Key dan Merchant ID untuk memproses transaksi perbankan dan QRIS live di Indonesia.
2. **Cloud Object Storage (Opsional):** Jika ingin menyimpan foto produk di Cloudflare R2 atau AWS S3 alih-alih local disk, pasang kredensial S3 pada `.env`.
3. **Domain & SSL:** Sambungkan DNS domain toko Anda ke IP server publik untuk penerimaan webhook gateway otomatis.
