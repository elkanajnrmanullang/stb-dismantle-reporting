from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os
import sys
from datetime import datetime, timedelta
from calendar import month_name

from flask import Flask, render_template, request, send_file, redirect, url_for, flash
from dotenv import load_dotenv

# ==== ENV ====
load_dotenv()

# ==== PATH (kalau pakai impor dari root project) ====
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

# ==== FLASK APP (pakai template/static di folder frontend) ====
app = Flask(
    __name__,
    template_folder='../frontend/templates',
    static_folder='../frontend'
)

# Healthcheck untuk Railway
@app.route("/healthz")
def healthz():
    return "ok", 200

# ===== Logic & DB Imports (setelah app dibuat) =====
from backend.logic.processor import process_files, get_tanggal_list_from_output
from backend.logic.dismantle_progress import process_dismantle_progress
from backend.logic.rumus_dismantle_kendala import process_dismantle_kendala
from backend.logic.stb_progress import process_stb_progress, generate_stb_total_rows
from backend.logic.stb_kendala import process_kendala_stb, generate_kendala_stb_total_row
from backend.logic.visit_dismantle import process_visit_dismantle
from backend.logic.visit_stb import process_visit_stb
from backend.logic.database import SessionLocal
from backend.logic.models import (
    ProgressDismantle, KendalaDismantle,
    STBProgress, KendalaSTB,
    VisitDismantle, VisitSTB
)


# ==== Konfigurasi App ====
app.secret_key = os.getenv("SECRET_KEY", "default_secret_key")
UPLOAD_FOLDER = '../uploads'
OUTPUT_FOLDER = '../outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@app.context_processor
def inject_request():
    from flask import request as _request
    return dict(request=_request)

@app.context_processor
def utility_processor():
    return dict(getattr=getattr)

@app.route('/')
def home():
    output_path = os.path.join(OUTPUT_FOLDER, 'ReportingSTB_Dismantle.xlsx')
    now = datetime.now()
    prev_month_dt = now.replace(day=1) - timedelta(days=1)
    prev_month_label = month_name[prev_month_dt.month].upper()
    prev_month_number = prev_month_dt.month

    tanggal_numbers = list(range(1, 32))

    try:
        tanggal_list = get_tanggal_list_from_output(output_path)
        if not tanggal_list:
            raise ValueError("Tanggal kosong")
        tanggal_list = [str(t) for t in tanggal_list]
    except Exception:
        tanggal_list = [str(i) for i in tanggal_numbers]

    db = SessionLocal()

    kendala_dismantle_all = db.query(KendalaDismantle).all()
    kendala_dismantle = [row for row in kendala_dismantle_all if not row.is_total_row]
    kendala_dismantle_total = [row for row in kendala_dismantle_all if row.is_total_row]

    visit_dismantle = (
        db.query(VisitDismantle)
          .order_by(VisitDismantle.is_total.asc(), VisitDismantle.service_area.asc())
          .all()
    )

    dismantle_data_raw = db.query(ProgressDismantle).filter_by(is_total_row=False).all()
    waktu_update_dismantle = (
        dismantle_data_raw[0].waktu_update.strftime("%d-%m-%Y %H:%M")
        if dismantle_data_raw and dismantle_data_raw[0].waktu_update else "-"
    )

    stb_progress_rows = db.query(STBProgress).filter_by(is_total_row=False).all()
    kendala_stb_rows = db.query(KendalaSTB).filter_by(is_total_row=False).all()

    total_rows, saldo_akhir_total, kendala_harian, kendala_total_progress = \
        generate_stb_total_rows(stb_progress_rows, kendala_stb_rows)
    stb_progress = stb_progress_rows + total_rows

    for r in kendala_stb_rows:
        r.progres_harian = [getattr(r, f"t{i}", 0) or 0 for i in tanggal_numbers]

    visit_stb = db.query(VisitSTB).all()
    visit_stb_data = db.query(VisitSTB).filter_by(is_total=False).order_by(VisitSTB.service_area).all()
    ringkasan_stb = [{
        "service_area": row.service_area,
        "total_visit": row.visit,
        "dismantle": row.dismantle,
        "kendala": row.kendala,
        "sisa": row.sisa_assign
    } for row in visit_stb_data]

    total_visit = sum(r["total_visit"] for r in ringkasan_stb)
    total_dismantle = sum(r["dismantle"] for r in ringkasan_stb)
    total_kendala_visit = sum(r["kendala"] for r in ringkasan_stb)
    total_sisa = sum(r["sisa"] for r in ringkasan_stb)

    db.close()

    return render_template(
        'index.html',
        tanggal_numbers=tanggal_numbers,
        tanggal_list=tanggal_list,
        waktu_update=waktu_update_dismantle,
        prev_month_label=prev_month_label,
        prev_month_number=prev_month_number,
        data_dismantle=dismantle_data_raw,
        kendala_dismantle=kendala_dismantle,
        kendala_dismantle_total=kendala_dismantle_total,
        visit_dismantle=visit_dismantle,
        stb_progress=stb_progress,
        kendala_harian=kendala_harian,
        kendala_total=kendala_total_progress,
        kendala_stb=kendala_stb_rows,
        visit_stb=visit_stb,
        ringkasan_stb=ringkasan_stb,
        total_visit=total_visit,
        total_dismantle=total_dismantle,
        total_kendala=total_kendala_visit,
        total_sisa=total_sisa
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

        db = SessionLocal()

        df_dismantle = pd.read_excel(path_dismantle)
        db.query(ProgressDismantle).filter_by(is_total_row=True).delete()
        db.query(KendalaDismantle).filter_by(is_total_row=True).delete()
        db.commit()

        prog_records = db.query(ProgressDismantle).filter_by(is_total_row=False).all()
        process_dismantle_progress(df_dismantle, prog_records, now.month, now.year)
        for r in prog_records:
            db.add(r)

        kendala_records = db.query(KendalaDismantle).filter_by(is_total_row=False).all()
        process_dismantle_kendala(df_dismantle, kendala_records, prog_records, now.month, now.year)
        for r in kendala_records:
            db.add(r)

        process_visit_dismantle(df_dismantle, db_session=db)
        db.flush()

        df_replacement = pd.read_excel(path_replacement)
        db.query(STBProgress).filter_by(is_total_row=True).delete()
        db.query(KendalaSTB).filter_by(is_total_row=True).delete()
        db.commit()

        stb_records = db.query(STBProgress).filter_by(is_total_row=False).all()
        process_stb_progress(df_replacement, stb_records, now.month, now.year)
        for r in stb_records:
            db.add(r)

        kendala_stb_records = db.query(KendalaSTB).filter_by(is_total_row=False).all()
        process_kendala_stb(df_replacement, kendala_stb_records, now.month, now.year)
        for r in kendala_stb_records:
            db.add(r)

        process_visit_stb(df_replacement, db_session=db)

        total_rows, saldo_akhir_total, _, _ = generate_stb_total_rows(stb_records, kendala_stb_records)
        for r in total_rows:
            r.saldo_akhir = saldo_akhir_total
            db.add(r)

        kendala_total_rows = generate_kendala_stb_total_row(kendala_stb_records)
        for r in kendala_total_rows:
            db.add(r)

        db.commit()
        db.close()

        flash("✅ Berhasil menggabungkan dan memproses file Excel!", "success")
        return render_template('upload.html', download_ready=True)

    except Exception as e:
        flash(f"❌ Gagal memproses file: {str(e)}", "error")
        return redirect(url_for('upload_files'))

@app.route("/dismantle/progress")
def dismantle_progress():
    db = SessionLocal()
    data = db.query(ProgressDismantle).order_by(ProgressDismantle.service_area, ProgressDismantle.sto).all()
    db.close()

    now = datetime.now()
    prev_month_dt = now.replace(day=1) - timedelta(days=1)
    prev_month_label = month_name[prev_month_dt.month].upper()
    waktu_update = data[0].waktu_update.strftime('%d-%B-%Y %H:%M') if data else "-"
    tanggal_list = [f't{i}' for i in range(1, 32)]

    return render_template(
        'components/subtable_dismantle_progress.html',
        data_dismantle=data,
        tanggal_list=tanggal_list,
        waktu_update=waktu_update,
        prev_month_label=prev_month_label,
        prev_month_number=prev_month_dt.month
    )

@app.route("/replacement/progress")
def replacement_progress():
    db = SessionLocal()
    rows = db.query(STBProgress).filter_by(is_total_row=False)\
        .order_by(STBProgress.service_area, STBProgress.sto).all()
    kendala_rows = db.query(KendalaSTB).filter_by(is_total_row=False).all()
    db.close()

    total_rows, _, kendala_harian, kendala_total_progress = generate_stb_total_rows(rows, kendala_rows)
    data = rows + total_rows

    now = datetime.now()
    prev_month_dt = now.replace(day=1) - timedelta(days=1)
    prev_month_label = month_name[prev_month_dt.month].upper()
    tanggal_list = [f't{i}' for i in range(1, 32)]
    waktu_update = now.strftime('%d %B %Y %H:%M')

    for row in data:
        row.progres_harian = [getattr(row, f"t{i}", 0) or 0 for i in range(1, 32)]

    return render_template(
        "components/subtable_stb_progress.html",
        stb_progress=data,
        tanggal_list=tanggal_list,
        bulan_lalu=prev_month_label,
        waktu_update=waktu_update,
        kendala_harian=kendala_harian,
        kendala_total=kendala_total_progress
    )

@app.route("/stb/kendala")
def replacement_kendala():
    db = SessionLocal()
    data = db.query(KendalaSTB).filter_by(is_total_row=False)\
        .order_by(KendalaSTB.service_area, KendalaSTB.sto).all()
    db.close()

    for r in data:
        r.progres_harian = [getattr(r, f"t{i}", 0) or 0 for i in range(1, 32)]

    now = datetime.now()
    prev_month_dt = now.replace(day=1) - timedelta(days=1)
    prev_month_label = month_name[prev_month_dt.month].upper()
    waktu_update = now.strftime('%d %B %Y %H:%M')
    tanggal_list = [f't{i}' for i in range(1, 32)]

    return render_template(
        "components/subtable_stb_kendala.html",
        kendala_stb=data,
        tanggal_list=tanggal_list,
        waktu_update=waktu_update,
        prev_month_label=prev_month_label,
        prev_month_number=prev_month_dt.month
    )

@app.route("/kendala/visit")
def visit_stb_table():
    db = SessionLocal()
    data = db.query(VisitSTB).filter_by(is_total=False).order_by(VisitSTB.service_area).all()
    db.close()

    waktu_update = datetime.now().strftime('%d-%B-%Y %H:%M')
    ringkasan_stb = [{
        "service_area": row.service_area,
        "total_visit": row.visit,
        "dismantle": row.dismantle,
        "kendala": row.kendala,
        "sisa": row.sisa_assign
    } for row in data]

    total_visit = sum(r["total_visit"] for r in ringkasan_stb)
    total_dismantle = sum(r["dismantle"] for r in ringkasan_stb)
    total_kendala = sum(r["kendala"] for r in ringkasan_stb)
    total_sisa = sum(r["sisa"] for r in ringkasan_stb)

    return render_template(
        "components/subtable_stb_ringkasan.html",
        ringkasan_stb=ringkasan_stb,
        total_visit=total_visit,
        total_dismantle=total_dismantle,
        total_kendala=total_kendala,
        total_sisa=total_sisa,
        waktu_update=waktu_update
    )

@app.route('/download')
def download_file():
    path = os.path.join(OUTPUT_FOLDER, 'ReportingSTB_Dismantle.xlsx')
    if os.path.exists(path):
        return send_file(path, as_attachment=True)
    flash("❌ File hasil belum tersedia.", "error")
    return redirect(url_for('upload_files'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
