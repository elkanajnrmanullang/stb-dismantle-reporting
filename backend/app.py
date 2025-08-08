from flask import Flask, render_template, request, send_file, redirect, url_for, flash
import os
import pandas as pd
from logic.dismantle_progress import process_dismantle_progress
from logic.rumus_dismantle_kendala import process_dismantle_kendala
from logic.stb_progress import process_stb_progress
from datetime import datetime, timedelta
from calendar import month_name
from logic.database import SessionLocal
from logic.models import (
    ProgressDismantle, KendalaDismantle,
    STBProgress, KendalaSTB,
    VisitDismantle, VisitSTB
)
from logic.processor import (
    process_files,
    get_tanggal_list_from_output
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

@app.context_processor
def inject_request():
    from flask import request
    return dict(request=request)

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

    try:
        tanggal_list = get_tanggal_list_from_output(output_path)
        if not tanggal_list:
            raise ValueError("Tanggal kosong")
        tanggal_list = [str(t) for t in tanggal_list]
    except Exception:
        tanggal_list = list(map(str, list(range(1, 32))))

    db = SessionLocal()

    kendala_dismantle_all = db.query(KendalaDismantle).all()
    kendala_dismantle = [row for row in kendala_dismantle_all if not row.is_total_row]
    kendala_dismantle_total = [row for row in kendala_dismantle_all if row.is_total_row]

    visit_dismantle = db.query(VisitDismantle).all()
    visit_stb = db.query(VisitSTB).all()
    visit_stb_data = db.query(VisitSTB).filter_by(is_total=False).order_by(VisitSTB.service_area).all()

    dismantle_data_raw = db.query(ProgressDismantle).filter_by(is_total_row=False).all()
    if dismantle_data_raw and dismantle_data_raw[0].waktu_update:
        waktu_update_dismantle = dismantle_data_raw[0].waktu_update.strftime("%d-%m-%Y %H:%M")
    else:
        waktu_update_dismantle = "-"

    stb_progress_raw = db.query(STBProgress).filter_by(is_total_row=False).all()
    if stb_progress_raw and stb_progress_raw[0].waktu_update:
        waktu_update_stb = stb_progress_raw[0].waktu_update.strftime("%d-%m-%Y %H:%M")
    else:
        waktu_update_stb = "-"

    stb_progress = []
    for row in stb_progress_raw:
        progres_harian = [getattr(row, f"t{i}", 0) or 0 for i in range(1, 32)]
        stb_progress.append({
            "jumlah": row.teknisi,
            "service_area": row.service_area,
            "sto": row.sto,
            "awal": row.saldo_awal,
            "assign": row.assign,
            "progres_harian": progres_harian,
            "total_berhasil": row.berhasil,
            "kendala": row.kendala,
            "sisa_saldo": row.saldo_akhir
        })

    kendala_stb_raw = db.query(KendalaSTB).filter_by(is_total_row=False).all()
    for row in kendala_stb_raw:
        progres = [getattr(row, f"t{i}", 0) or 0 for i in range(1, 32)]
        row.progres_harian = progres

    ringkasan_stb = []
    for row in visit_stb_data:
        ringkasan_stb.append({
            "service_area": row.service_area,
            "total_visit": row.visit,
            "dismantle": row.dismantle,
            "kendala": row.kendala,
            "sisa": row.sisa_assign
        })

    data_dismantle = dismantle_data_raw
    total_visit = sum(row["total_visit"] for row in ringkasan_stb)
    total_dismantle = sum(row["dismantle"] for row in ringkasan_stb)
    total_kendala = sum(row["kendala"] for row in ringkasan_stb)
    total_sisa = sum(row["sisa"] for row in ringkasan_stb)
    
    stb_progress = db.query(STBProgress).filter_by(is_total_row=False).all()

    db.close()

    return render_template(
        'index.html',
        tanggal_list=tanggal_list,
        waktu_update=waktu_update_dismantle,
        data_dismantle=data_dismantle,
        prev_month_label=prev_month_label,
        prev_month_number=prev_month_number,
        kendala_dismantle=kendala_dismantle,
        kendala_dismantle_total=kendala_dismantle_total,
        visit_dismantle=visit_dismantle,
        visit_stb=visit_stb,
        stb_progress=stb_progress,
        kendala_stb=kendala_stb_raw,
        ringkasan_stb=ringkasan_stb,
        total_visit=total_visit,
        total_dismantle=total_dismantle,
        total_kendala=total_kendala,
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

        # Proses ETL awal (untuk ekspor Excel)
        process_files(
            replacement_file=path_replacement,
            dismantle_file=path_dismantle,
            output_path=output_path,
            start_date=start_date,
            end_date=end_date
        )

        # -------------------------------
        # ⬇ Proses Dismantle
        # -------------------------------
        df_dismantle = pd.read_excel(path_dismantle)
        db = SessionLocal()

        # Bersihkan baris total sebelumnya
        db.query(ProgressDismantle).filter_by(is_total_row=True).delete()
        db.query(KendalaDismantle).filter_by(is_total_row=True).delete()
        db.commit()

        # Hitung progress dismantle
        records = db.query(ProgressDismantle).filter_by(is_total_row=False).all()
        process_dismantle_progress(df_dismantle, records, now.month, now.year)
        for r in records:
            db.add(r)

        # Hitung kendala dismantle
        kendala_records = db.query(KendalaDismantle).filter_by(is_total_row=False).all()
        progress_records = db.query(ProgressDismantle).filter_by(is_total_row=False).all()
        process_dismantle_kendala(df_dismantle, kendala_records, progress_records, now.month, now.year)
        for r in kendala_records:
            db.add(r)

        # -------------------------------
        # ⬇ Proses Replacement STB
        # -------------------------------
        df_replacement = pd.read_excel(path_replacement)

        # Bersihkan baris total sebelumnya
        db.query(STBProgress).filter_by(is_total_row=True).delete()
        db.commit()

        stb_records = db.query(STBProgress).filter_by(is_total_row=False).all()
        process_stb_progress(df_replacement, stb_records, now.month, now.year)
        for r in stb_records:
            db.add(r)

        db.commit()
        db.close()

        flash("✅ Berhasil menggabungkan dan memproses file Excel!", "success")
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
    
    total_teknisi = sum([row.jumlah_teknisi or 0 for row in data])
    
    now = datetime.now()

    prev_month_dt = now.replace(day=1) - timedelta(days=1)
    prev_month_label = month_name[prev_month_dt.month].upper()
    prev_month_number = prev_month_dt.month
    if data and data[0].waktu_update:
        waktu_update = data[0].waktu_update.strftime('%d-%B-%Y %H:%M')
    else:
        waktu_update = "-"
    tanggal_list = [f't{i}' for i in range(1, 32)]

    return render_template(
        'components/subtable_dismantle_progress.html',
        data_dismantle=data,
        tanggal_list=tanggal_list,
        waktu_update=waktu_update,
        prev_month_label=prev_month_label,
        prev_month_number=prev_month_number
    )

@app.route("/replacement/progress")
def replacement_progress():
    db = SessionLocal()
    data = db.query(STBProgress).order_by(STBProgress.service_area, STBProgress.sto).all()
    db.close()

    now = datetime.now()
    prev_month_dt = now.replace(day=1) - timedelta(days=1)
    prev_month_label = month_name[prev_month_dt.month].upper()
    prev_month_number = prev_month_dt.month

    tanggal_list = [f't{i}' for i in range(1, 32)]
    waktu_update = now.strftime('%d %B %Y %H:%M')

    # Parsing progres_harian
    for row in data:
        progres = []
        for i in range(1, 32):
            val = getattr(row, f"t{i}", None)
            progres.append(val if val is not None else 0)
        row.progres_harian = progres

    return render_template(
        "components/subtable_stb_progress.html",
        stb_progress=data,
        tanggal_list=tanggal_list,
        bulan_lalu=prev_month_label,
        waktu_update=waktu_update,
    )



@app.route("/stb/kendala")
def replacement_kendala():
    db = SessionLocal()
    data = db.query(KendalaSTB).filter_by(is_total_row=False).order_by(KendalaSTB.service_area, KendalaSTB.sto).all()
    db.close()

    now = datetime.now()
    prev_month_dt = now.replace(day=1) - timedelta(days=1)
    prev_month_label = month_name[prev_month_dt.month].upper()
    prev_month_number = prev_month_dt.month
    waktu_update = now.strftime('%d %B %Y %H:%M')

    tanggal_list = [f't{i}' for i in range(1, 32)]
    for row in data:
        progres = [getattr(row, f"t{i}", 0) or 0 for i in range(1, 32)]
        row.progres_harian = progres

    return render_template(
        "components/subtable_stb_kendala.html",
        kendala_stb=data,
        tanggal_list=tanggal_list,
        waktu_update=waktu_update,
        prev_month_label=prev_month_label,
        prev_month_number=prev_month_number
    )

@app.route("/kendala/visit")
def visit_stb_table():
    db = SessionLocal()
    data = db.query(VisitSTB).filter_by(is_total=False).order_by(VisitSTB.service_area).all()
    db.close()

    waktu_update = datetime.now().strftime('%d-%B-%Y %H:%M')

    ringkasan_stb = []
    for row in data:
        ringkasan_stb.append({
            "service_area": row.service_area,
            "total_visit": row.visit,
            "dismantle": row.dismantle,
            "kendala": row.kendala,
            "sisa": row.sisa_assign
        })

    total_visit = sum(row["total_visit"] for row in ringkasan_stb)
    total_dismantle = sum(row["dismantle"] for row in ringkasan_stb)
    total_kendala = sum(row["kendala"] for row in ringkasan_stb)
    total_sisa = sum(row["sisa"] for row in ringkasan_stb)

    return render_template(
        "components/subtable_stb_ringkasan.html",
        ringkasan_stb=ringkasan_stb,
        total_visit=total_visit,
        total_dismantle=total_dismantle,
        total_kendala=total_kendala,
        total_sisa=total_sisa,
        waktu_update=waktu_update
    )

if __name__ == '__main__':
    app.run(debug=True)
