from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os
from datetime import datetime, timedelta
from calendar import month_name
from logic.database import SessionLocal
from sqlalchemy.orm import Session
from logic.models import (
    ProgressDismantle, KendalaDismantle,
    STBProgress, KendalaSTB,
    VisitDismantle, VisitSTB
)
from logic.processor import (
    process_files,
    get_tanggal_list_from_output,
    get_dismantle_progress_table,
    get_dismantle_kendala_table
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

@app.context_processor
def utility_processor():
    return dict(getattr=getattr)

@app.route('/')
def home():
    print("Rendering...")
    output_path = os.path.join(OUTPUT_FOLDER, 'ReportingSTB_Dismantle.xlsx')

    now = datetime.now()
    prev_month_dt = now.replace(day=1) - timedelta(days=1)
    prev_month_label = month_name[prev_month_dt.month].upper()
    prev_month_number = prev_month_dt.month

    waktu_update = now.strftime('%d-%B-%Y %H:%M')
    tanggal_list = []

    try:
        tanggal_list = get_tanggal_list_from_output(output_path)
        if not tanggal_list:
            raise ValueError("Tanggal kosong")
        tanggal_list = [str(t) for t in tanggal_list]
    except Exception as e:
        print(">> Error ambil tanggal_list:", e)
        tanggal_list = list(map(str, list(range(1, 32))))

    db = SessionLocal()
    data_dismantle = db.query(ProgressDismantle).filter_by(is_total_row=False).all()
    kendala_dismantle = db.query(KendalaDismantle).filter_by(is_total_row=False).all()
    db.close()

    return render_template(
        'index.html',
        tanggal_list=tanggal_list,
        waktu_update=waktu_update,
        data_dismantle=data_dismantle,
        prev_month_label=prev_month_label,
        prev_month_number=prev_month_number,
        kendala_dismantle=kendala_dismantle
    )



@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'GET':
        return render_template('upload.html', download_ready=False)

    try:
        file_replacement = request.files['replacement']
        file_dismantle = request.files['dismantle']

        if file_replacement.filename == '' or file_dismantle.filename == '':
            raise Exception("File belum lengkap diunggah.")

        path_replacement = os.path.join(UPLOAD_FOLDER, "replacement.xlsx")
        path_dismantle = os.path.join(UPLOAD_FOLDER, "dismantle.xlsx")
        file_replacement.save(path_replacement)
        file_dismantle.save(path_dismantle)

        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        end_date = datetime(now.year, now.month, 31)

        output_path = os.path.join(OUTPUT_FOLDER, 'ReportingSTB_Dismantle.xlsx')

        process_files(
            replacement_file=path_replacement,
            dismantle_file=path_dismantle,
            output_path=output_path,
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
    path = os.path.join(OUTPUT_FOLDER, 'ReportingSTB_Dismantle.xlsx')
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    else:
        flash("❌ File hasil belum tersedia.", "error")
        return redirect(url_for('home'))

@app.route("/dismantle/progress")
def dismantle_progress():
    db = SessionLocal()
    data = db.query(ProgressDismantle).order_by(ProgressDismantle.service_area, ProgressDismantle.sto).all()
    db.close()

    now = datetime.now()
    prev_month_dt = now.replace(day=1) - timedelta(days=1)
    prev_month_label = month_name[prev_month_dt.month].upper()
    prev_month_number = prev_month_dt.month

    tanggal_list = [f't{i}' for i in range(1, 32)]
    waktu_update = now.strftime('%d %B %Y %H:%M')

    return render_template(
        'subtable_dismantle_progress.html',
        data_dismantle=data,
        tanggal_list=tanggal_list,
        waktu_update=waktu_update,
        prev_month_label=prev_month_label,
        prev_month_number=prev_month_number
    )


@app.route("/dismantle/kendala")
def dismantle_kendala_table():
    from calendar import month_name
    from datetime import datetime, timedelta

    db = SessionLocal()
    data = db.query(KendalaDismantle).filter_by(is_total_row=False).order_by(KendalaDismantle.service_area, KendalaDismantle.sto).all()
    db.close()

    # Hitung bulan sebelumnya
    now = datetime.now()
    prev_month_dt = now.replace(day=1) - timedelta(days=1)
    prev_month_label = month_name[prev_month_dt.month].upper()
    prev_month_number = prev_month_dt.month
    waktu_update = now.strftime('%d-%B-%Y %H:%M')

    # Siapkan progres_harian: list [t1, t2, ..., t31]
    for row in data:
        row.progres_harian = [getattr(row, f"t{i}", 0) or 0 for i in range(1, 32)]

    return render_template(
        "components/subtable_dismantle_kendala.html",
        kendala_dismantle=data,
        prev_month_label=prev_month_label,
        prev_month_number=prev_month_number,
        waktu_update=waktu_update
    )

@app.route("/dismantle/visit")
def dismantle_visit_table():
    waktu_update = datetime.now().strftime('%d-%B-%Y %H:%M')

    ringkasan_dismantle = [
        {"service_area": "BOGOR", "total_visit": 0, "dismantle": 0, "kendala": 0, "sisa": 1},
    ]

    total_visit = sum(row["total_visit"] for row in ringkasan_dismantle)
    total_dismantle = sum(row["dismantle"] for row in ringkasan_dismantle)
    total_kendala = sum(row["kendala"] for row in ringkasan_dismantle)
    total_sisa = sum(row["sisa"] for row in ringkasan_dismantle)

    return render_template(
        "components/subtable_visit.html",
        ringkasan_dismantle=ringkasan_dismantle,
        total_visit=total_visit,
        total_dismantle=total_dismantle,
        total_kendala=total_kendala,
        total_sisa=total_sisa,
        waktu_update=waktu_update
    )

if __name__ == '__main__':
    app.run(debug=True)