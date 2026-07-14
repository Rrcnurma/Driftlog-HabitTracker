"""
habit_manager.py
File ini isinya fungsi-fungsi buat menyimpan dan mengambil data habit harian,
disimpan sebagai file JSON di S3 (bucket: driftlog-data, folder: habits/).
"""

import json
from datetime import date
from backend.aws_client import get_s3_client

BUCKET_NAME = 'driftlog-data'


def pastikan_bucket_ada():
    """
    Cek apakah bucket 'driftlog-data' sudah ada di S3.
    Kalau belum ada, buat dulu. Dipanggil sekali di awal (main.py)
    biar app gak error 'bucket not found' pas pertama kali dipakai.
    """
    s3 = get_s3_client()
    response = s3.list_buckets()

    # response['Buckets'] itu sebuah list, isinya banyak dictionary.
    # Kita loop satu-satu, cek apakah ada yang 'Name'-nya sama dengan BUCKET_NAME.
    nama_bucket_yang_ada = [b['Name'] for b in response['Buckets']]

    if BUCKET_NAME not in nama_bucket_yang_ada:
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"Bucket '{BUCKET_NAME}' berhasil dibuat.")
    else:
        print(f"Bucket '{BUCKET_NAME}' sudah ada.")


def simpan_habit_hari_ini(data_habits):
    """
    Menyimpan checklist habit untuk HARI INI ke S3.

    Parameter:
        data_habits: dictionary, contoh -> {"olahraga": True, "baca_buku": False}

    File akan disimpan dengan nama sesuai tanggal hari ini, misal:
        habits/2026-07-11.json
    """
    s3 = get_s3_client()

    tanggal_hari_ini = date.today().isoformat()  # contoh hasil: '2026-07-11'

    # Susun data lengkap yang mau disimpan (tanggal + habits)
    data_lengkap = {
        'tanggal': tanggal_hari_ini,
        'habits': data_habits
    }

    # json.dumps() mengubah dictionary Python jadi teks JSON.
    # Ini WAJIB, karena s3.put_object() cuma nerima teks/bytes, bukan dictionary langsung.
    isi_file_json = json.dumps(data_lengkap)

    key = f"habits/{tanggal_hari_ini}.json"

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=isi_file_json
    )

    print(f"Data habit tanggal {tanggal_hari_ini} berhasil disimpan.")


def ambil_semua_habit():
    """
    Mengambil SEMUA data habit yang pernah disimpan di S3.
    Dipakai buat tab History dan buat report_engine.py (nanti).

    Return: list of dictionary, contoh:
        [
            {"tanggal": "2026-07-10", "habits": {"olahraga": True, ...}},
            {"tanggal": "2026-07-11", "habits": {"olahraga": False, ...}},
        ]
    """
    s3 = get_s3_client()

    # list_objects_v2 dengan Prefix='habits/' artinya:
    # "kasih aku semua file yang namanya diawali 'habits/'"
    # Ini cara S3 mensimulasikan folder (sebenarnya S3 gak punya folder asli,
    # cuma nama file yang mengandung '/' dianggap folder oleh convention).
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix='habits/')

    semua_data = []

    # Kalau bucket masih kosong / belum ada file habits/, key 'Contents' gak akan muncul.
    # Makanya kita cek dulu pakai 'in', biar gak error KeyError.
    if 'Contents' not in response:
        return semua_data  # balikin list kosong

    for obj in response['Contents']:
        key = obj['Key']

        # Ambil isi file satu per satu
        file_response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        isi_teks = file_response['Body'].read().decode('utf-8')

        # json.loads() mengubah teks JSON kembali jadi dictionary Python
        data = json.loads(isi_teks)
        semua_data.append(data)

    # Urutkan berdasarkan tanggal, dari yang paling lama ke paling baru
    semua_data.sort(key=lambda item: item['tanggal'])

    return semua_data


def ambil_daftar_habit():
    """
    Mengambil daftar nama habit yang aktif (yang mau di-track user).
    Disimpan sebagai file konfigurasi terpisah di S3: config/daftar_habit.json

    Kalau file ini belum pernah ada (pemakaian pertama kali), akan dibuat
    otomatis dengan daftar habit default.

    Return: list of string, contoh: ['Olahraga', 'Baca buku']
    """
    s3 = get_s3_client()
    key = 'config/daftar_habit.json'

    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        isi_teks = response['Body'].read().decode('utf-8')
        return json.loads(isi_teks)
    except s3.exceptions.NoSuchKey:
        # Belum ada file konfigurasi -> buat dengan daftar default
        daftar_default = ['Olahraga', 'Baca buku', 'Minum air 8 gelas', 'Tidur cukup (7-8 jam)']
        simpan_daftar_habit(daftar_default)
        return daftar_default


def simpan_daftar_habit(daftar_habit):
    """
    Menyimpan daftar nama habit ke S3 (menimpa yang lama).

    Parameter:
        daftar_habit: list of string, contoh: ['Olahraga', 'Baca buku', 'Meditasi']
    """
    s3 = get_s3_client()
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key='config/daftar_habit.json',
        Body=json.dumps(daftar_habit)
    )


def tambah_habit_baru(nama_habit_baru):
    """
    Menambahkan satu nama habit baru ke daftar yang sudah ada.
    Kalau nama itu sudah ada sebelumnya, tidak akan ditambahkan dobel.

    Parameter:
        nama_habit_baru: string, contoh: 'Meditasi'

    Return: daftar habit terbaru (list of string), setelah ditambahkan
    """
    daftar_sekarang = ambil_daftar_habit()

    nama_habit_baru = nama_habit_baru.strip()  # buang spasi berlebih di awal/akhir

    if nama_habit_baru == '':
        raise ValueError("Nama habit tidak boleh kosong.")

    if nama_habit_baru in daftar_sekarang:
        raise ValueError(f"Habit '{nama_habit_baru}' sudah ada di daftar.")

    daftar_sekarang.append(nama_habit_baru)
    simpan_daftar_habit(daftar_sekarang)

    print(f"Habit baru '{nama_habit_baru}' berhasil ditambahkan.")
    return daftar_sekarang


def hapus_habit(tanggal):
    """
    Menghapus data habit untuk tanggal tertentu.
    Parameter tanggal formatnya string, contoh: '2026-07-11'
    (Fitur ini opsional/bonus, buat jaga-jaga kalau ada salah input.)
    """
    s3 = get_s3_client()
    key = f"habits/{tanggal}.json"
    s3.delete_object(Bucket=BUCKET_NAME, Key=key)
    print(f"Data habit tanggal {tanggal} berhasil dihapus.")