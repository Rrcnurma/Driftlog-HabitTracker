# Driftlog

Aplikasi desktop habit tracker yang terintegrasi dengan AWS (S3 & EC2) lewat Boto3. Setiap hari, user checklist kebiasaan yang sudah dikerjakan. Data disimpan sebagai object di S3. Kapan pun diinginkan, user bisa klik satu tombol untuk membangun sebuah "website laporan" progress kebiasaannya di cloud: aplikasi otomatis menyiapkan jaringan (VPC, Subnet, Security Group), menyalakan EC2 sebagai web server, membuat grafik, lalu meng-upload semuanya ke S3.

## Fitur

- Checklist habit harian, tersimpan sebagai JSON di S3
- **Tambah habit custom** — user bisa menambahkan jenis habit baru sendiri langsung dari aplikasi (tidak hardcode), tersimpan sebagai konfigurasi terpisah di S3
- Generate laporan progress (grafik + ringkasan persentase konsistensi)
- Otomatis provisioning infrastruktur cloud: VPC, Internet Gateway, Public Subnet, Route Table, Security Group (port 80 & 22), EC2 instance
- Upload aset (gambar grafik + halaman HTML) ke S3 bucket
- Verifikasi otomatis isi bucket S3
- UI modern pakai ttkbootstrap (tema `cyborg` — dark theme)

## Teknologi

Python, Tkinter + ttkbootstrap (GUI), Boto3 (AWS SDK), matplotlib (grafik), berjalan di atas [Ministack](https://pypi.org/project/ministack/) sebagai emulator AWS lokal dan [Stackport](https://pypi.org/project/stackport/) sebagai dashboard visual.

## Struktur Project

```
Projek_Driftlog/
├── main.py                    # Entry point aplikasi
├── requirements.txt
├── README.md
├── .gitignore
├── test_koneksi.py            # Script test koneksi awal (opsional)
├── lihat_hasil_website.py     # Script bantu verifikasi hasil laporan secara visual
├── backend/
│   ├── __init__.py
│   ├── aws_client.py          # Konfigurasi koneksi Boto3 ke Ministack
│   ├── habit_manager.py       # Simpan/ambil data habit harian & config habit dari S3
│   ├── network_setup.py       # Provisioning VPC, Subnet, Route Table, Security Group
│   └── report_engine.py       # Hitung laporan, buat grafik, deploy EC2 + upload S3
└── frontend/
    ├── __init__.py
    ├── input_tab.py           # Tab checklist harian + form tambah habit baru
    └── report_tab.py          # Tab generate laporan
```

Data konfigurasi habit (daftar nama habit yang di-track) disimpan otomatis di S3 sebagai `config/daftar_habit.json` di dalam bucket `driftlog-data`, dan akan dibuat otomatis dengan nilai default saat aplikasi pertama kali dijalankan.

## Cara Menjalankan

Butuh **3 terminal terpisah**, semua harus tetap terbuka bersamaan.

### 1. Install dependency Python

```
pip install -r requirements.txt
```

### 2. Terminal 1 — Ministack (emulator AWS)

```
pip install ministack
```

Jalankan dengan mode **persisten** (agar data S3 tidak hilang saat Ministack di-restart):

**Windows (Command Prompt):**
```
set S3_PERSIST=1
ministack
```

**macOS/Linux:**
```
S3_PERSIST=1 ministack
```

Biarkan terminal ini tetap terbuka. Ministack akan berjalan di `http://localhost:4566`.

### 3. Terminal 2 — Stackport (dashboard visual, opsional tapi disarankan)

```
pip install stackport
stackport
```

Buka `http://localhost:8080` di browser. Untuk bisa melihat bucket/resource milik aplikasi ini, buka **Settings → Endpoints**, edit endpoint yang mengarah ke `localhost:4566`, lalu isi:
- Access Key ID: `121212121212`
- Secret Access Key: `admin123`

(Ministack mengisolasi data per-akun berdasarkan Access Key, jadi tanpa langkah ini Stackport akan tampak kosong walau datanya sebenarnya ada.)

### 4. Terminal 3 — Jalankan aplikasi Driftlog

Pastikan Ministack & Stackport masih berjalan di dua terminal lain, lalu:

```
python main.py
```

### 5. (Opsional) Verifikasi hasil laporan secara visual

Karena Ministack memisahkan data per-akun, membuka URL S3 langsung di browser tidak akan menampilkan apapun (bukan bug — ini karakteristik desain Ministack). Untuk melihat hasil laporan (gambar grafik + halaman ringkasan) secara visual setelah membuat laporan lewat aplikasi:

```
python lihat_hasil_website.py
```

Script ini mengambil file dari S3 lewat Boto3 (menggunakan kredensial yang sama seperti aplikasi), lalu membukanya di browser sebagai file lokal.

## Catatan Teknis

- **Ministack** adalah API endpoint (emulator AWS), bukan website — wajar bila diakses langsung lewat browser tanpa path tertentu menghasilkan halaman kosong/error. Ministack dirancang untuk diakses lewat AWS SDK seperti Boto3, bukan manusia secara langsung.
- **S3 dipilih (bukan DynamoDB)** karena kebutuhan data aplikasi ini adalah menyimpan & membaca file (JSON, gambar) secara utuh, tanpa kebutuhan query/filter kompleks yang menjadi kekuatan utama database seperti DynamoDB.
- **EC2** pada aplikasi ini berperan sebagai web server yang menyajikan laporan progress habit. Karena keterbatasan emulator (Ministack tidak menjalankan sistem operasi sungguhan di dalam instance EC2), pembuktian fungsi EC2 dilakukan melalui instance ID & status yang berhasil dibuat, dikombinasikan dengan bukti bahwa aset web (gambar & HTML) berhasil di-generate dan diupload ke S3.
- **Persistence S3**: dijalankan dengan `S3_PERSIST=1` sehingga data bucket tersimpan ke disk, bukan hanya di memori — bertahan walau proses Ministack di-restart.