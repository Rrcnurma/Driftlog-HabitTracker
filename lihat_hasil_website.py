"""
lihat_hasil_website.py
Script ini buat "membuka" hasil laporan (gambar & html) tanpa lewat browser,
karena Ministack mengisolasi data per-akun (lihat penjelasan di chat).

Cara pakai: python lihat_hasil_website.py
Ini akan download ulang gambar & html dari S3 ke folder lokal,
lalu otomatis membukanya pakai aplikasi default di komputer kamu.
"""

import os
import webbrowser
from backend.aws_client import get_s3_client

BUCKET_ASET_WEBSITE = 'driftlog-web-assets'


def download_dan_buka():
    s3 = get_s3_client()

    # Download gambar grafik
    s3.download_file(
        Bucket=BUCKET_ASET_WEBSITE,
        Key='grafik_laporan.png',
        Filename='hasil_grafik.png'
    )
    print("Gambar berhasil didownload: hasil_grafik.png")

    # Ambil isi HTML dari S3 (sebagai teks, bukan langsung didownload ke file)
    response = s3.get_object(Bucket=BUCKET_ASET_WEBSITE, Key='index.html')
    isi_html = response['Body'].read().decode('utf-8')

    # PENTING: isi_html aslinya berisi tag <img src="http://localhost:4566/...">
    # yang mengarah ke Ministack. Karena file ini akan dibuka SECARA LOKAL
    # (file:///...), src itu perlu diganti supaya menunjuk ke file gambar
    # yang sudah didownload tadi (hasil_grafik.png), bukan ke Ministack lagi.
    import re
    isi_html_lokal = re.sub(
        r'src="http://localhost:4566/[^"]+"',
        'src="hasil_grafik.png"',
        isi_html
    )

    with open('hasil_laporan.html', 'w', encoding='utf-8') as file_html:
        file_html.write(isi_html_lokal)
    print("Halaman HTML berhasil disimpan (dengan gambar lokal): hasil_laporan.html")

    # Buka otomatis pakai browser
    path_html = os.path.abspath('hasil_laporan.html')
    webbrowser.open(f'file://{path_html}')
    print("Halaman laporan dibuka di browser.")


if __name__ == '__main__':
    download_dan_buka()