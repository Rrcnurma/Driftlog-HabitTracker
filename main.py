"""
main.py
Entry point aplikasi Driftlog. Jalankan file ini buat membuka aplikasi:
    python main.py

Menggunakan ttkbootstrap (extension Tkinter) untuk tampilan yang lebih modern,
mirip komponen Bootstrap di web, tanpa perlu mengubah widget di file lain
(gui/input_tab.py dan gui/report_tab.py tetap pakai ttk biasa - ttkbootstrap
otomatis "menimpa" tampilan semua widget ttk begitu tema-nya diaktifkan).
"""

import ttkbootstrap as tb
from backend.habit_manager import pastikan_bucket_ada
from frontend.input_tab import buat_tab_input
from frontend.report_tab import buat_tab_report


def main():
    print("Menghubungkan ke Ministack...")
    pastikan_bucket_ada()

    # tb.Window itu pengganti tk.Tk(), sekaligus otomatis mengaktifkan tema.
    # 'cyborg' adalah tema gelap bawaan ttkbootstrap: latar hitam pekat,
    # warna aksen cyan/hijau terang, kesan futuristik/techy.
    window = tb.Window(themename='cyborg')
    window.title("Driftlog")

    # Ukuran window dihitung otomatis dari resolusi layar user (bukan angka
    # tetap), supaya konsisten kelihatan "setengah layar" di laptop manapun,
    # entah itu 1366x768, 1920x1080, dll.
    lebar_layar = window.winfo_screenwidth()
    tinggi_layar = window.winfo_screenheight()
    lebar_jendela = int(lebar_layar * 0.5)
    tinggi_jendela = int(tinggi_layar * 0.85)
    window.geometry(f"{lebar_jendela}x{tinggi_jendela}")

    notebook = tb.Notebook(window, bootstyle='primary')
    notebook.pack(fill='both', expand=True, padx=16, pady=16)

    tab_input = buat_tab_input(notebook)
    notebook.add(tab_input, text='  Input Harian  ')

    tab_report = buat_tab_report(notebook)
    notebook.add(tab_report, text='  Laporan  ')

    window.mainloop()


if __name__ == '__main__':
    main()