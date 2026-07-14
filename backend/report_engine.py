"""
report_engine.py
File ini adalah "otak" dari fitur utama Driftlog: tombol "Buat Laporan Sekarang".

Yang dilakukan file ini secara berurutan:
1. Ambil semua data habit dari S3, hitung persentase konsistensi tiap habit
2. Bikin grafik (gambar PNG) dari hasil hitungan itu
3. Siapkan jaringan cloud (panggil network_setup.py)
4. Nyalakan EC2 sebagai web server
5. Bikin bucket S3 khusus buat aset website, upload gambar grafik ke situ
6. Bikin halaman HTML sederhana yang menampilkan laporan + gambar dari S3
7. Verifikasi: cek ulang isi bucket S3 buat mastiin semua ke-upload
"""

import json
import matplotlib
matplotlib.use('Agg')  # mode 'Agg' = gambar dibuat tanpa perlu tampilan layar
import matplotlib.pyplot as plt

from backend.aws_client import get_ec2_client, get_s3_client
from backend.habit_manager import ambil_semua_habit
from backend.network_setup import setup_jaringan_lengkap

BUCKET_ASET_WEBSITE = 'driftlog-web-assets'


def hitung_laporan():
    """
    Membaca semua data habit dari S3, lalu menghitung persentase
    konsistensi tiap habit (berapa persen hari yang dicentang True).

    Return: dictionary, contoh:
        {
            "periode": "2026-07-05 s/d 2026-07-11 (5 hari tercatat)",
            "detail": {"Olahraga": 60.0, "Baca buku": 100.0},
            "insight": "Konsistensi terbaik: Baca buku"
        }
    """
    semua_data = ambil_semua_habit()

    if len(semua_data) == 0:
        raise ValueError("Belum ada data habit sama sekali. Isi checklist harian dulu.")

    jumlah_hari = len(semua_data)
    tanggal_pertama = semua_data[0]['tanggal']
    tanggal_terakhir = semua_data[-1]['tanggal']

    # Kumpulkan semua nama habit yang pernah dicatat (dari hari manapun)
    semua_nama_habit = set()
    for data_harian in semua_data:
        semua_nama_habit.update(data_harian['habits'].keys())

    # Hitung persentase tiap habit
    detail_persentase = {}
    for nama_habit in semua_nama_habit:
        jumlah_dikerjakan = 0
        for data_harian in semua_data:
            # .get(nama_habit, False) -> ambil nilainya, kalau habit itu
            # gak ada di hari tsb, anggap False (gak dikerjakan)
            if data_harian['habits'].get(nama_habit, False):
                jumlah_dikerjakan += 1

        persentase = round((jumlah_dikerjakan / jumlah_hari) * 100, 1)
        detail_persentase[nama_habit] = persentase

    # Cari habit dengan persentase tertinggi buat insight
    habit_terbaik = max(detail_persentase, key=detail_persentase.get)

    laporan = {
        'periode': f"{tanggal_pertama} s/d {tanggal_terakhir} ({jumlah_hari} hari tercatat)",
        'detail': detail_persentase,
        'insight': f"Konsistensi terbaik: {habit_terbaik} ({detail_persentase[habit_terbaik]}%)"
    }

    return laporan


def buat_grafik_png(laporan, path_simpan='grafik_laporan.png'):
    """
    Membuat gambar grafik batang (bar chart) dari hasil hitung_laporan(),
    lalu menyimpannya sebagai file PNG di komputer lokal dulu
    (sebelum nanti di-upload ke S3).

    Parameter:
        laporan: dictionary hasil dari hitung_laporan()
        path_simpan: nama file PNG yang akan dibuat

    Return: path_simpan (string) - lokasi file gambar yang baru dibuat
    """
    nama_habit = list(laporan['detail'].keys())
    nilai_persen = list(laporan['detail'].values())

    plt.figure(figsize=(6, 4))
    plt.bar(nama_habit, nilai_persen, color='#4A90D9')
    plt.ylabel('Persentase (%)')
    plt.title('Konsistensi Habit - Driftlog')
    plt.ylim(0, 100)
    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig(path_simpan)
    plt.close()

    print(f"Grafik berhasil dibuat: {path_simpan}")
    return path_simpan


def buat_halaman_html(laporan, url_gambar):
    """
    Membuat isi (teks) halaman HTML yang menampilkan laporan
    dan grafik, sudah dipercantik dengan CSS inline.

    Parameter:
        laporan: dictionary hasil dari hitung_laporan()
        url_gambar: URL gambar grafik di S3

    Return: teks HTML (string)
    """
    baris_kartu = ''
    for nama_habit, persen in laporan['detail'].items():
        # Warna bar disesuaikan sama besarnya persentase:
        # tinggi = hijau, sedang = kuning, rendah = merah muda
        if persen >= 70:
            warna = '#22C55E'
        elif persen >= 40:
            warna = '#F59E0B'
        else:
            warna = '#F87171'

        baris_kartu += f"""
        <div class="kartu-habit">
            <div class="baris-atas">
                <span class="nama-habit">{nama_habit}</span>
                <span class="persen-habit">{persen}%</span>
            </div>
            <div class="progress-track">
                <div class="progress-isi" style="width:{persen}%; background:{warna};"></div>
            </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Laporan Driftlog</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #EEF2FF 0%, #F4F6FA 100%);
            margin: 0;
            padding: 40px 20px;
            color: #1F2430;
        }}
        .kontainer {{
            max-width: 680px;
            margin: 0 auto;
            background: #FFFFFF;
            border-radius: 18px;
            box-shadow: 0 10px 30px rgba(31, 36, 48, 0.08);
            padding: 40px;
        }}
        .label-app {{
            display: inline-block;
            background: #4A6FE3;
            color: white;
            font-size: 12px;
            font-weight: 600;
            letter-spacing: 0.5px;
            padding: 4px 12px;
            border-radius: 999px;
            margin-bottom: 16px;
        }}
        h1 {{
            font-size: 28px;
            margin: 0 0 4px 0;
        }}
        .periode {{
            color: #6B7280;
            font-size: 14px;
            margin-bottom: 28px;
        }}
        .kartu-habit {{
            margin-bottom: 16px;
        }}
        .baris-atas {{
            display: flex;
            justify-content: space-between;
            font-size: 14px;
            margin-bottom: 6px;
        }}
        .nama-habit {{
            font-weight: 500;
        }}
        .persen-habit {{
            font-weight: 700;
            color: #4A6FE3;
        }}
        .progress-track {{
            background: #EDEFF3;
            border-radius: 999px;
            height: 10px;
            overflow: hidden;
        }}
        .progress-isi {{
            height: 100%;
            border-radius: 999px;
        }}
        .insight-box {{
            background: #EEF2FF;
            border-left: 4px solid #4A6FE3;
            border-radius: 8px;
            padding: 14px 18px;
            margin: 24px 0;
            font-size: 14px;
        }}
        .grafik-wrap {{
            margin-top: 24px;
            text-align: center;
        }}
        .grafik-wrap img {{
            max-width: 100%;
            border-radius: 12px;
            border: 1px solid #EDEFF3;
        }}
        .footer {{
            text-align: center;
            color: #9CA3AF;
            font-size: 12px;
            margin-top: 28px;
        }}
    </style>
</head>
<body>
    <div class="kontainer">
        <span class="label-app">DRIFTLOG</span>
        <h1>Laporan Progress Habit</h1>
        <p class="periode">Periode: {laporan['periode']}</p>

        {baris_kartu}

        <div class="insight-box">
            {laporan['insight']}
        </div>

        <div class="grafik-wrap">
            <img src="{url_gambar}" alt="Grafik konsistensi habit">
        </div>

        <p class="footer">Dibuat otomatis oleh Driftlog</p>
    </div>
</body>
</html>"""

    return html


def deploy_laporan_sebagai_website():
    """
    Fungsi UTAMA yang dipanggil dari GUI saat tombol "Buat Laporan Sekarang"
    diklik. Menjalankan seluruh alur dari awal sampai akhir.

    Return: dictionary berisi ringkasan semua yang berhasil dibuat.
    """
    # 1. Hitung laporan dari data habit yang ada
    laporan = hitung_laporan()

    # 2. Bikin grafik PNG (masih di komputer lokal)
    path_gambar_lokal = buat_grafik_png(laporan)

    # 3. Siapkan jaringan (VPC, Subnet, Route Table, Security Group)
    info_jaringan = setup_jaringan_lengkap()

    # 4. Nyalakan EC2 sebagai web server, taruh di public subnet,
    #    pasang security group yang sudah dibuat
    ec2 = get_ec2_client()
    hasil_ec2 = ec2.run_instances(
        ImageId='ami-mock-ubuntu',
        InstanceType='t2.micro',
        MinCount=1,
        MaxCount=1,
        SubnetId=info_jaringan['subnet_id'],
        SecurityGroupIds=[info_jaringan['security_group_id']],
    )
    instance_id = hasil_ec2['Instances'][0]['InstanceId']
    print(f"EC2 web server berhasil dinyalakan: {instance_id}")

    # 5. Siapkan bucket S3 khusus buat aset website (kalau belum ada)
    s3 = get_s3_client()
    daftar_bucket = [b['Name'] for b in s3.list_buckets()['Buckets']]
    if BUCKET_ASET_WEBSITE not in daftar_bucket:
        s3.create_bucket(Bucket=BUCKET_ASET_WEBSITE)
        print(f"Bucket '{BUCKET_ASET_WEBSITE}' berhasil dibuat.")

    # 6. Upload gambar grafik ke S3
    key_gambar = 'grafik_laporan.png'
    with open(path_gambar_lokal, 'rb') as file_gambar:
        s3.put_object(
            Bucket=BUCKET_ASET_WEBSITE,
            Key=key_gambar,
            Body=file_gambar,
            ContentType='image/png'
        )
    url_gambar = f"http://localhost:4566/{BUCKET_ASET_WEBSITE}/{key_gambar}"
    print(f"Gambar grafik berhasil diupload ke S3: {url_gambar}")

    # 7. Bikin halaman HTML, upload juga ke S3 (sebagai bukti/dokumentasi
    #    halaman yang "akan" ditampilkan EC2 web server)
    isi_html = buat_halaman_html(laporan, url_gambar)
    s3.put_object(
        Bucket=BUCKET_ASET_WEBSITE,
        Key='index.html',
        Body=isi_html,
        ContentType='text/html'
    )
    print("Halaman index.html berhasil diupload ke S3.")

    # 8. Verifikasi: list ulang isi bucket, pastikan semua file ada
    response_verifikasi = s3.list_objects_v2(Bucket=BUCKET_ASET_WEBSITE)
    daftar_file = [obj['Key'] for obj in response_verifikasi.get('Contents', [])]
    print(f"Verifikasi isi bucket '{BUCKET_ASET_WEBSITE}': {daftar_file}")

    return {
        'laporan': laporan,
        'instance_id': instance_id,
        'info_jaringan': info_jaringan,
        'bucket_aset': BUCKET_ASET_WEBSITE,
        'file_di_bucket': daftar_file,
    }