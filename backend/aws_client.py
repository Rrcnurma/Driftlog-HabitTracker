"""
aws_client.py
File ini isinya "jembatan" antara aplikasi kita dengan Ministack (emulator AWS).
Semua file lain (habit_manager.py, report_engine.py) akan import dari sini,
supaya endpoint & credentials cuma didefinisikan sekali di satu tempat.
"""

import boto3

# --- Konfigurasi Endpoint Ministack ---
# Ini sama persis kayak yang ada di notebook praktikum kamu.
ENDPOINT = 'http://localhost:4566'
REGION = 'us-east-1'

CREDENTIALS = {
    'aws_access_key_id': '121212121212',
    'aws_secret_access_key': 'admin123'
}


def get_s3_client():
    """
    Fungsi ini bikin dan balikin (return) objek client S3.
    Dipanggil dari habit_manager.py setiap kali butuh akses S3.
    """
    return boto3.client(
        's3',
        endpoint_url=ENDPOINT,
        region_name=REGION,
        **CREDENTIALS
    )


def get_ec2_client():
    """
    Sama seperti di atas, tapi untuk EC2.
    Dipanggil dari report_engine.py saat mau generate laporan mingguan.
    """
    return boto3.client(
        'ec2',
        endpoint_url=ENDPOINT,
        region_name=REGION,
        **CREDENTIALS
    )