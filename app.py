from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import psycopg2 # Menggantikan sqlite3
from datetime import datetime
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "roadcare_secret")

# Konfigurasi Cloudinary
cloudinary.config( 
  cloud_name = os.environ.get("CLOUDINARY_CLOUD_NAME"), 
  api_key = os.environ.get("CLOUDINARY_API_KEY"), 
  api_secret = os.environ.get("CLOUDINARY_API_SECRET")
)

# Fungsi koneksi ke PostgreSQL Cloud
def get_db_connection():
    # Mengambil URL database dari environment variable Vercel
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

# Catatan: Buat tabel users dan laporan di dashboard Supabase/Neon kamu terlebih dahulu 
# atau jalankan query otomatis saat app pertama kali menyala.

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['username'] = user[1] # Sesuaikan dengan urutan kolom PostgreSQL
            session['role'] = user[3]
            return redirect(url_for('dashboard'))
        else:
            flash('Username atau password salah!')
    return render_template('login.html')

@app.route('/laporan', methods=['GET', 'POST'])
def laporan():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        nama_jalan = request.form['nama_jalan']
        deskripsi = request.form['deskripsi']
        alamat = request.form['alamat']
        koordinat = request.form['koordinat']
        patokan = request.form['patokan']
        tanggal_upload = datetime.now().strftime('%d-%m-%Y %H:%M')
        
        file = request.files['foto']
        if file:
            # Upload langsung ke Cloudinary, bukan ke folder lokal
            upload_result = cloudinary.uploader.upload(file)
            foto_url = upload_result['secure_url'] # Mengambil link foto online

            conn = get_db_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO laporan (nama_jalan, deskripsi, alamat, koordinat, patokan, tanggal_upload, foto)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (nama_jalan, deskripsi, alamat, koordinat, patokan, tanggal_upload, foto_url))
            conn.commit()
            conn.close()

            flash('Laporan berhasil dikirim!')
            return redirect(url_for('dashboard'))

    return render_template('laporan.html')

# Sisa route lainnya (dashboard, hapus, logout) disesuaikan menggunakan %s menggantikan ? pada query SQL-nya.