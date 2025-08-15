import pandas as pd
from datetime import datetime
from .models import KendalaDismantle
from logic.database import SessionLocal  # Tambahkan untuk commit langsung

def process_dismantle_kendala(df: pd.DataFrame, records: list, progress_records: list, bulan: int, tahun: int):
    df['TANGGAL DISMANTLING'] = pd.to_datetime(
        df['TANGGAL DISMANTLING'], errors='coerce', dayfirst=True
    )
    df['bulan'] = df['TANGGAL DISMANTLING'].dt.month
    df['tahun'] = df['TANGGAL DISMANTLING'].dt.year

    for record in records:
        sto = record.sto
        df_sto = df[df['STO'].astype(str).str.strip().str.upper() == sto.upper()]

        record.berhasil_bulan_lalu = df_sto[
            (df_sto['STATUS'].astype(str).str.strip().str.upper() == 'CLOSE') &
            (df_sto['bulan'] == bulan - 1) &
            (df_sto['tahun'] == tahun)
        ].shape[0]

        record.kendala_bulan_lalu = df_sto[
            (df_sto['STATUS'].astype(str).str.strip().str.upper() == 'KENDALA') &
            (df_sto['bulan'] == bulan - 1) &
            (df_sto['tahun'] == tahun)
        ].shape[0]

        record.saldo_awal = df_sto.shape[0]

        record.progress = df_sto[
            df_sto['STATUS'].astype(str).str.strip().str.upper() == 'TIBA'
        ].shape[0]

        total_kendala = 0
        for i in range(1, 32):
            kondisi = (
                (df_sto['STATUS'].astype(str).str.strip().str.upper() == 'KENDALA') &
                (df_sto['TANGGAL DISMANTLING'].dt.day == i) &
                (df_sto['bulan'] == bulan) &
                (df_sto['tahun'] == tahun)
            )
            count = df_sto[kondisi].shape[0]
            setattr(record, f"t{i}", count)
            total_kendala += count

        record.kendala = total_kendala

        # Ambil kolom 'berhasil' dari progress
        progress_match = next((p for p in progress_records if p.sto.upper() == sto.upper()), None)
        record.berhasil = progress_match.berhasil if progress_match else 0

        record.saldo_akhir = df_sto[
            df_sto['STATUS'].astype(str).str.strip().str.upper() == 'OPEN'
        ].shape[0]

        record.waktu_update = datetime.now()

    # Buat dan simpan baris TOTAL secara langsung (tidak dimasukkan ke records!)
    if records:
        total_row = KendalaDismantle(
            teknisi=sum(r.teknisi or 0 for r in records),
            jumlah_teknisi=sum(r.teknisi or 0 for r in records),
            service_area='TOTAL',
            sto='',
            berhasil_bulan_lalu=sum(r.berhasil_bulan_lalu or 0 for r in records),
            kendala_bulan_lalu=sum(r.kendala_bulan_lalu or 0 for r in records),
            saldo_awal=sum(r.saldo_awal or 0 for r in records),
            progress=sum(r.progress or 0 for r in records),
            berhasil=sum(r.berhasil or 0 for r in records),
            kendala=sum(r.kendala or 0 for r in records),
            saldo_akhir=sum(r.saldo_akhir or 0 for r in records),
            is_total_row=True,
            waktu_update=datetime.now()
        )

        for i in range(1, 32):
            nilai = sum(getattr(r, f"t{i}", 0) or 0 for r in records)
            setattr(total_row, f"t{i}", nilai)

        # Simpan langsung ke database (bukan ke records!)
        session = SessionLocal()
        session.add(total_row)
        session.commit()
        session.close()
