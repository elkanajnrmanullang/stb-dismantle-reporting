from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os
from datetime import datetime

from logic.processor import process_files  # Harus support tanggal dari-to

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='../frontend'
)

app.secret_key = 'your_secret_key'

# Folder upload & output
UPLOAD_FOLDER = '../uploads'
OUTPUT_FOLDER = '../outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Inject request context to Jinja2 (untuk navbar aktif, jika ada)
@app.context_processor
def inject_request():
    from flask import request
    return dict(request=request)

# ROUTE: Homepage Dashboard
@app.route('/')
def home():
    return render_template('index.html')

# ROUTE: Upload Page
@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'GET':
        return render_template('upload.html', download_ready=False)

    try:
        # Tangkap file dari form
        files = {
            'replacement1': request.files['replacement1'],
            'replacement2': request.files['replacement2'],
            'dismantle1': request.files['dismantle1'],
            'dismantle2': request.files['dismantle2'],
        }

        # Simpan semua file
        saved_paths = {}
        for key, file in files.items():
            if file.filename == '':
                raise Exception(f"{key} tidak memiliki file.")
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)
            saved_paths[key] = path

        # Hitung tanggal 25 ke 25
        now = datetime.now()
        if now.day >= 25:
            start_date = datetime(now.year, now.month - 1, 25)
            end_date = datetime(now.year, now.month, 25)
        else:
            if now.month == 1:
                start_date = datetime(now.year - 1, 12, 25)
                end_date = datetime(now.year, 1, 25)
            else:
                start_date = datetime(now.year, now.month - 1, 25)
                end_date = datetime(now.year, now.month, 25)

        # Lokasi output akhir
        output_path = os.path.join(OUTPUT_FOLDER, 'hasil.xlsx')

        # Proses file Excel (dengan filter tanggal 25 – 25)
        process_files(
            saved_paths['replacement1'],
            saved_paths['replacement2'],
            saved_paths['dismantle1'],
            saved_paths['dismantle2'],
            output_path,
            start_date=start_date,
            end_date=end_date
        )

        flash("✅ Berhasil menggabungkan file Excel!", "success")
        return render_template('upload.html', download_ready=True)

    except Exception as e:
        flash(f"❌ Gagal memproses file: {str(e)}", "error")
        return redirect(url_for('upload_files'))

# ROUTE: Download hasil file
@app.route('/download')
def download_file():
    path = os.path.join(OUTPUT_FOLDER, 'hasil.xlsx')
    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
