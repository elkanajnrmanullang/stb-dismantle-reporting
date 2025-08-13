
markdown
Copy
Edit
# 📊 Sistem Web Otomatisasi Pelaporan Harian Dismantling & Replacement STB – Telkom Akses

Proyek ini bertujuan untuk membantu **PT Telkom Indonesia**, khususnya **Telkom Akses**, dalam memonitor dan mengelola data **perangkat STB (Set Top Box)** yang mengalami proses **dismantle (pencabutan)** maupun **replacement (penggantian)** oleh teknisi di lapangan.  

Dengan sistem ini, proses pelaporan yang sebelumnya dilakukan secara manual dan memakan waktu dapat diotomatisasi, sehingga mempercepat proses rekapitulasi, meningkatkan akurasi data, dan memudahkan manajemen dalam memantau progres pekerjaan secara real-time.  

Sistem memproses file Excel gabungan (per kategori), menghitung rekap harian (tanggal 1–31), menyimpan ke database PostgreSQL, dan menampilkannya dalam dashboard web interaktif dengan fitur ekspor Excel & capture gambar.

---

## 🚀 Fitur Utama
- **Upload File Excel** (Dismantle & Replacement)
- **Pemrosesan Otomatis**:
  - Rekap progress harian berdasarkan status (`CLOSE`, `OPEN`, `KENDALA`, `ASSIGN`)
  - Rekap kendala harian
  - Saldo awal & saldo akhir
  - Summary visit harian per area
- **Database PostgreSQL** dengan format denormalisasi (tanggal 1–31 sebagai kolom)
- **Dashboard Interaktif**:
  - Tabel progress & kendala
  - Tabel visit harian gabungan
  - Card ringkasan
  - Grafik per area (opsional)
- **Export Excel Final** (PASTE & DASHBOARD)
- **Capture Tabel** ke `.png` langsung dari browser

---

## 🛠️ Tech Stack
**Frontend**  
- HTML + Tailwind CSS  
- Alpine.js (interaktivitas)  

**Backend**  
- Python Flask  
- Pandas, NumPy (ETL & perhitungan)  
- SQLAlchemy (ORM)  

**Database**  
- PostgreSQL  

**Export**  
- OpenPyXL / XlsxWriter  
