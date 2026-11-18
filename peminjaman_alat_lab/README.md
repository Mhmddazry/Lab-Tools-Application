# Sistem Peminjaman Alat Laboratorium

Aplikasi web lokal untuk mengelola inventaris alat laboratorium, mencatat peminjaman, dan mencatat pengembalian. Aplikasi menggunakan Flask, SQLite, dan Layered Architecture.

## Fitur

- CRUD alat: tambah, lihat, ubah, dan hapus alat beserta stok totalnya.
- Stok tersedia ditampilkan terpisah dari stok total.
- Peminjaman menyimpan nama peminjam, jumlah alat, dan tanggal jatuh tempo.
- Stok tersedia otomatis berkurang saat peminjaman disimpan.
- Peminjaman ditolak jika stok tidak mencukupi; pembaruan stok dan transaksi dilakukan secara atomik di SQLite.
- Pengembalian mengubah status transaksi dan menambah stok tersedia tepat satu kali.
- Daftar peminjaman aktif dan seluruh riwayat dapat dilihat di browser.
- Alat yang sudah memiliki riwayat peminjaman tidak dapat dihapus agar riwayat transaksi tetap utuh.

## Kebutuhan

- Python 3.9 atau lebih baru.
- `pip` untuk memasang Flask dari `requirements.txt`.

## Instalasi

Buka terminal di folder `peminjaman_alat_lab`, lalu buat virtual environment.

### Windows PowerShell

```powershell
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Jika perintah `py` tidak tersedia, gunakan `python -m venv .venv` selama Python sudah ditambahkan ke `PATH`.

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Inisialisasi database dan menjalankan aplikasi

Aktifkan virtual environment, kemudian jalankan:

```bash
flask --app app init-db
python app.py
```

Database SQLite dibuat otomatis di `instance/laboratorium.sqlite3`. Inisialisasi aman dijalankan berulang dan tidak menghapus data yang sudah ada. Aplikasi akan tersedia di <http://127.0.0.1:5000>. Inventaris awal kosong; tambahkan alat dari halaman **Inventaris** untuk memulai demo.

## Pembagian tugas untuk tiga anggota

1. **Anggota 1 — Presentation:** halaman HTML/CSS, route inventaris, formulir CRUD alat, dan tampilan daftar transaksi.
2. **Anggota 2 — Business Logic:** validasi data, aturan perubahan stok, pengecekan ketersediaan, dan alur peminjaman/pengembalian.
3. **Anggota 3 — Data Access & integrasi:** skema SQLite, repository/query, konfigurasi database, integrasi antar-layer, serta dokumentasi dan skenario demo.

Setiap anggota dapat meninjau integrasi dan laporan bersama sebelum presentasi.

## Struktur arsitektur

```text
peminjaman_alat_lab/
├── app.py                              # composition root dan startup Flask
├── business_logic/
│   ├── entities.py                     # entitas domain
│   └── services.py                     # validasi dan aturan bisnis
├── data_access/
│   ├── database.py                     # koneksi, transaksi, dan skema SQLite
│   └── repositories.py                 # seluruh query SQLite
├── presentation/
│   ├── routes.py                       # request, pemanggilan service, response
│   ├── templates/                      # tampilan HTML/Jinja
│   └── static/css/style.css            # styling
├── requirements.txt
└── README.md
```

Route tidak menjalankan query database. Business logic tidak mengetahui objek request Flask. Repository hanya mengelola penyimpanan dan operasi database. `app.py` merangkai dependency antar-layer.

## Konfigurasi opsional

- `LAB_DATABASE_PATH`: mengganti lokasi file SQLite.
- `FLASK_SECRET_KEY`: mengganti secret key sesi Flask lokal.
- `PORT`: mengganti port saat menjalankan `python app.py`.
