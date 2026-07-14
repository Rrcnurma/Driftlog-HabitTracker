"""
gui/report_tab.py
Isi tab "Laporan" - tombol "Buat Laporan Sekarang" + area tampilan hasil.
Menggunakan ttkbootstrap untuk tampilan yang lebih modern.
"""

import tkinter as tk
import ttkbootstrap as tb
from tkinter import messagebox
from backend.report_engine import deploy_laporan_sebagai_website


def buat_tab_report(parent):
    """
    Fungsi ini membuat dan mengembalikan Frame untuk tab Laporan.

    Parameter:
        parent: widget induk (notebook dari main.py)

    Return:
        frame yang siap ditambahkan sebagai tab
    """

    frame = tb.Frame(parent, padding=20)

    label_judul = tb.Label(
        frame,
        text='Laporan Progress Habit',
        font=('Segoe UI', 14, 'bold'),
        bootstyle='light'
    )
    label_judul.pack(anchor='w', pady=(0, 10))

    area_log = tk.Text(frame, height=18, wrap='word', state='disabled',
                        font=('Consolas', 9), relief='flat',
                        background='#1A1D24', foreground='#E8E9EB',
                        insertbackground='#E8E9EB')
    area_log.pack(fill='both', expand=True, pady=(0, 15))

    def tulis_log(teks):
        area_log.config(state='normal')
        area_log.insert('end', teks + '\n')
        area_log.see('end')
        area_log.config(state='disabled')
        area_log.update()

    def saat_tombol_diklik():
        tombol.config(state='disabled')
        area_log.config(state='normal')
        area_log.delete('1.0', 'end')
        area_log.config(state='disabled')

        try:
            tulis_log("Memulai proses...")
            tulis_log("Menghitung laporan dari data habit di S3...")

            hasil = deploy_laporan_sebagai_website()

            tulis_log("Grafik berhasil dibuat.")
            tulis_log(f"Jaringan (VPC/Subnet/SG) berhasil disiapkan.")
            tulis_log(f"EC2 web server dinyalakan: {hasil['instance_id']}")
            tulis_log(f"Bucket aset website: {hasil['bucket_aset']}")
            tulis_log(f"File di bucket: {', '.join(hasil['file_di_bucket'])}")
            tulis_log("")
            tulis_log(f"Periode: {hasil['laporan']['periode']}")
            for nama_habit, persen in hasil['laporan']['detail'].items():
                tulis_log(f"  - {nama_habit}: {persen}%")
            tulis_log(f"\n{hasil['laporan']['insight']}")
            tulis_log("\n=== LAPORAN BERHASIL DIBUAT & DI-DEPLOY ===")

            messagebox.showinfo("Berhasil", "Laporan berhasil dibuat dan di-deploy!")

        except Exception as error:
            tulis_log(f"\nGAGAL: {error}")
            messagebox.showerror("Gagal", f"Terjadi kesalahan:\n{error}")

        finally:
            tombol.config(state='normal')

    tombol = tb.Button(
        frame,
        text='Buat Laporan Sekarang',
        bootstyle='primary',
        command=saat_tombol_diklik
    )
    tombol.pack(fill='x')

    return frame