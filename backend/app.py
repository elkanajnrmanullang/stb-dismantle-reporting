from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os
from datetime import datetime
from logic.processor import (
    process_files,
    get_tanggal_list_from_output,
    get_card_summary,
    get_dismantle_progress_table
)

app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend'
)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = '../uploads'
OUTPUT_FOLDER = '../outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.context_processor
def inject_request():
    from flask import request
    return dict(request=request)

@app.route('/')
def home():
    print(">>> RENDERING index.html dari /frontend/templates")
    output_path = os.path.join(OUTPUT_FOLDER, 'hasil.xlsx')

    waktu_update = datetime.now().strftime('%d-%B-%Y %H:%M')
    tanggal_list = []
    total_replace = 0
    total_dismantle = 0

    # Placeholder sebelum data upload
    from logic.placeholder_area import placeholder_area

    try:
        tanggal_list = get_tanggal_list_from_output(output_path)
        if not tanggal_list:
            raise ValueError("Tanggal kosong")
        tanggal_list = [str(t) for t in tanggal_list]
    except Exception as e:
        print(">> Error ambil tanggal_list:", e)
        tanggal_list = list(map(str, list(range(25, 32)) + list(range(1, 26))))

    try:
        total_replace, total_dismantle = get_card_summary(output_path)
    except Exception as e:
        print(">> Error ambil card summary:", e)

    return render_template(
        'index.html',
        tanggal_list=tanggal_list,
        waktu_update=waktu_update,
        total_replace=total_replace,
        total_dismantle=total_dismantle,
        data_dismantle=[],  
        placeholder_area=placeholder_area
    )
 
@app.route("/dismantle/kendala")
def dismantle_kendala_table():
    output_path = os.path.join(OUTPUT_FOLDER, 'hasil.xlsx')
    waktu_update = datetime.now().strftime('%d-%B-%Y %H:%M')

    try:
        kendala_dismantle, tanggal_list = get_dismantle_kendala_table(output_path)
    except Exception as e:
        print(">> Gagal generate kendala dismantle:", e)
        kendala_dismantle, tanggal_list = [], []

    return render_template(
        "components/subtable_dismantle_kendala.html",
        kendala_dismantle=kendala_dismantle,
        tanggal_list=tanggal_list,
        waktu_update=waktu_update,
        placeholder_area=placeholder_area
    )
    

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'GET':
        return render_template('upload.html', download_ready=False)

    try:
        files = {
            'replacement1': request.files['replacement1'],
            'replacement2': request.files['replacement2'],
            'dismantle1': request.files['dismantle1'],
            'dismantle2': request.files['dismantle2'],
        }

        saved_paths = {}
        for key, file in files.items():
            if file.filename == '':
                raise Exception(f"File '{key}' tidak ditemukan.")
            path = os.path.join(UPLOAD_FOLDER, key + ".xlsx")
            file.save(path)
            saved_paths[key] = path

        now = datetime.now()
        if now.day >= 25:
            start_date = datetime(now.year, now.month, 25)
            end_date = datetime(now.year + 1, 1, 25) if now.month == 12 else datetime(now.year, now.month + 1, 25)
        else:
            start_date = datetime(now.year - 1, 12, 25) if now.month == 1 else datetime(now.year, now.month - 1, 25)
            end_date = datetime(now.year, now.month, 25)

        output_path = os.path.join(OUTPUT_FOLDER, 'hasil.xlsx')

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

@app.route('/download')
def download_file():
    path = os.path.join(OUTPUT_FOLDER, 'hasil.xlsx')
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    else:
        flash("❌ File hasil belum tersedia.", "error")
        return redirect(url_for('home'))

@app.route('/api/card-summary')
def api_card_summary():
    output_path = os.path.join(OUTPUT_FOLDER, 'hasil.xlsx')
    try:
        total_replace, total_dismantle = get_card_summary(output_path)
        return {
            'total_replace': total_replace,
            'total_dismantle': total_dismantle,
            'success': True
        }
    except Exception as e:
        print(">> API card summary error:", e)
        return {'success': False, 'message': str(e)}

@app.route("/dismantle/progress")
def dismantle_progress_table():
    output_path = os.path.join(OUTPUT_FOLDER, 'hasil.xlsx')
    waktu_update = datetime.now().strftime('%d-%B-%Y %H:%M')

    try:
        data_dismantle, tanggal_list = get_dismantle_progress_table(output_path)
    except Exception as e:
        print(">> Gagal generate progress dismantle:", e)
        data_dismantle, tanggal_list = [], []

    return render_template(
        "components/subtable_dismantle_progress.html",
        data_dismantle=data_dismantle,
        tanggal_list=tanggal_list,
        waktu_update=waktu_update
    )

if __name__ == '__main__':
    app.run(debug=True)
