from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "roadcare_secret"

# =========================
# KONFIGURASI
# =========================
DB_NAME = "login.db"
UPLOAD_FOLDER = "static/uploads"

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Membuat folder upload otomatis (DIMATIKAN KARENA VERCEL READ-ONLY)
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
# DATABASE
# =========================
def init_db():

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # TABEL USERS
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')

    # TABEL LAPORAN
    c.execute('''
        CREATE TABLE IF NOT EXISTS laporan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nama_jalan TEXT,
            deskripsi TEXT,
            alamat TEXT,
            koordinat TEXT,
            patokan TEXT,
            tanggal_upload TEXT,
            foto TEXT
        )
    ''')

    # ADMIN DEFAULT
    c.execute('''
        INSERT OR IGNORE INTO users (username, password, role)
        VALUES (?, ?, ?)
    ''', ("admin", "1234", "admin"))

    # USER DEFAULT
    c.execute('''
        INSERT OR IGNORE INTO users (username, password, role)
        VALUES (?, ?, ?)
    ''', ("user", "1234", "user"))

    conn.commit()
    conn.close()

# Jalankan database (DIMATIKAN AGAR TIDAK ERROR DI VERCEL)
# init_db()

# =========================
# LOGIN
# =========================
@app.route('/', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = c.fetchone()

        conn.close()

        if user:

            session['username'] = user[1]
            session['role'] = user[3]

            return redirect(url_for('dashboard'))

        else:
            flash('Username atau password salah!')

    return render_template('login.html')

# =========================
# DASHBOARD
# =========================
@app.route('/dashboard')
def dashboard():

    if 'username' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("SELECT * FROM laporan ORDER BY id DESC")

    laporan = c.fetchall()

    conn.close()

    return render_template(
        'dashboard.html',
        laporan=laporan,
        role=session['role'],
        username=session['username']
    )

# =========================
# UPLOAD LAPORAN
# =========================
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

            filename = secure_filename(file.filename)

            filepath = os.path.join(
                app.config['UPLOAD_FOLDER'],
                filename
            )

            file.save(filepath)

            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()

            c.execute('''
                INSERT INTO laporan
                (
                    nama_jalan,
                    deskripsi,
                    alamat,
                    koordinat,
                    patokan,
                    tanggal_upload,
                    foto
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                nama_jalan,
                deskripsi,
                alamat,
                koordinat,
                patokan,
                tanggal_upload,
                filename
            ))

            conn.commit()
            conn.close()

            flash('Laporan berhasil dikirim!')

            return redirect(url_for('dashboard'))

    return render_template('laporan.html')

# =========================
# HAPUS LAPORAN (ADMIN ONLY)
# =========================
@app.route('/hapus/<int:id>')
def hapus(id):

    if 'username' not in session:
        return redirect(url_for('login'))

    # Hanya admin yang boleh hapus
    if session['role'] != 'admin':

        flash('Akses ditolak!')

        return redirect(url_for('dashboard'))

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("DELETE FROM laporan WHERE id=?", (id,))

    conn.commit()
    conn.close()

    flash('Laporan berhasil dihapus!')

    return redirect(url_for('dashboard'))

# =========================
# LOGOUT
# =========================
@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))

# =========================
# RUN APP
# =========================
if __name__ == "__main__":

    app.run(debug=True)
