"""
test_koneksi.py
File ini cuma buat mastiin backend/aws_client.py berhasil connect ke Ministack.
Jalankan ini dulu SEBELUM lanjut bikin file lain.

Cara pakai:
1. Pastikan Ministack sudah jalan (terminal 1: `ministack`)
2. Pastikan Stackport sudah jalan (terminal 2: `stackport`)
3. Jalankan file ini di terminal 3: `python test_koneksi.py`
"""

from backend.aws_client import get_s3_client, get_ec2_client

print("Mencoba konek ke S3...")
s3 = get_s3_client()

response = s3.list_buckets()
print("Koneksi S3 berhasil!")
print(f"Jumlah bucket saat ini: {len(response['Buckets'])}")

print("\nMencoba konek ke EC2...")
ec2 = get_ec2_client()

response = ec2.describe_instances()
print("Koneksi EC2 berhasil!")

print("\n=== SEMUA KONEKSI BERHASIL ===")