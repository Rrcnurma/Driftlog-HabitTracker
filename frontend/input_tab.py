"""
gui/input_tab.py
Isi tab "Input Harian" - checklist habit (dinamis, bisa ditambah user) + tombol simpan.
Menggunakan ttkbootstrap untuk tampilan yang lebih modern.
"""

import tkinter as tk
import ttkbootstrap as tb
from tkinter import messagebox
from backend.habit_manager import simpan_habit_hari_ini, ambil_daftar_habit, tambah_habit_baru
from datetime import date


def buat_tab_input(parent):
    """
    Fungsi ini membuat dan mengembalikan sebuah Frame (kontainer)
    yang isinya checklist habit + form tambah habit + tombol simpan.

    Parameter:
        parent: widget induk tempat tab ini akan ditempel (notebook dari main.py)

    Return:
        frame yang siap ditambahkan sebagai tab
    """

    frame = tb.Frame(parent, padding=20)

    # --- Judul + tanggal hari ini ---
    tanggal_hari_ini = date.today().strftime('%A, %d %B %Y')
    label_tanggal = tb.Label(frame, text=tanggal_hari_ini, font=('Segoe UI', 12, 'bold'),
                              bootstyle='secondary')
    label_tanggal.pack(anchor='w', pady=(0, 15))

    # --- Area checklist ---
    area_checklist = tb.Frame(frame)
    area_checklist.pack(fill='x', anchor='w')

    variabel_checklist = {}

    def gambar_ulang_checklist():
        for widget in area_checklist.winfo_children():
            widget.destroy()
        variabel_checklist.clear()

        try:
            daftar_habit = ambil_daftar_habit()
        except Exception as error:
            messagebox.showerror("Gagal Memuat", f"Gagal mengambil daftar habit:\n{error}")
            return

        for nama_habit in daftar_habit:
            var = tk.BooleanVar(value=False)
            variabel_checklist[nama_habit] = var

            checkbox = tb.Checkbutton(area_checklist, text=nama_habit, variable=var,
                                       bootstyle='primary')
            checkbox.pack(anchor='w', pady=5)

    gambar_ulang_checklist()

    # --- Tombol Simpan ---
    def saat_tombol_simpan_diklik():
        data_habits = {
            nama: var.get() for nama, var in variabel_checklist.items()
        }

        try:
            simpan_habit_hari_ini(data_habits)
            messagebox.showinfo("Berhasil", "Data habit hari ini berhasil disimpan!")
        except Exception as error:
            messagebox.showerror("Gagal Menyimpan", f"Terjadi kesalahan:\n{error}")

    tombol_simpan = tb.Button(
        frame,
        text='Simpan Hari Ini',
        bootstyle='primary',
        command=saat_tombol_simpan_diklik
    )
    tombol_simpan.pack(fill='x', pady=(15, 20))

    # --- Garis pemisah ---
    tb.Separator(frame, orient='horizontal').pack(fill='x', pady=(0, 15))

    # --- Form tambah habit baru ---
    label_form = tb.Label(frame, text='Tambah habit baru', font=('Segoe UI', 11, 'bold'),
                           bootstyle='secondary')
    label_form.pack(anchor='w', pady=(0, 8))

    baris_form = tb.Frame(frame)
    baris_form.pack(fill='x')

    input_habit_baru = tb.Entry(baris_form)
    input_habit_baru.pack(side='left', fill='x', expand=True, padx=(0, 8))

    def saat_tombol_tambah_diklik():
        nama_baru = input_habit_baru.get()

        try:
            tambah_habit_baru(nama_baru)
            input_habit_baru.delete(0, 'end')
            gambar_ulang_checklist()
            messagebox.showinfo("Berhasil", f"Habit '{nama_baru.strip()}' berhasil ditambahkan!")
        except ValueError as error:
            messagebox.showwarning("Tidak Bisa Ditambahkan", str(error))
        except Exception as error:
            messagebox.showerror("Gagal", f"Terjadi kesalahan:\n{error}")

    tombol_tambah = tb.Button(
        baris_form,
        text='+ Tambah',
        bootstyle='outline-primary',
        command=saat_tombol_tambah_diklik
    )
    tombol_tambah.pack(side='right')

    return frame