import pandas as pd
from datetime import datetime
from logic.models import STBProgress

def process_stb_progress(df: pd.DataFrame, records: list, bulan: int, tahun: int):
    print("✅ [DEBUG] Memulai proses STB Progress")

    # Normalisasi kolom
    df['status'] = df['status'].astype(str).str.strip().str.lower()
    df['id_sto'] = df['id_sto'].astype(str).str.strip()
    df['last_activity_at'] = pd.to_datetime(
        df['last_activity_at'], errors='coerce', dayfirst=True
    )

    df['bulan'] = df['last_activity_at'].dt.month
    df['tahun'] = df['last_activity_at'].dt.year
    df['tanggal'] = df['last_activity_at'].dt.day

    print(f"✅ Unik STATUS: {df['status'].unique()}")
    print(f"✅ Bulan unik: {df['bulan'].unique()}")
    print(f"✅ Tahun unik: {df['tahun'].unique()}")

    total_teknisi = 0
    total_saldo_awal = 0
    total_berhasil = 0
    total_kendala = 0
    total_saldo_akhir = 0
    total_tanggal = {f"t{i}": 0 for i in range(1, 32)}

    for row in records:
        if row.is_total_row:
            continue

        sto = row.sto
        df_sto = df[df['id_sto'] == sto]

        # Saldo Awal
        row.saldo_awal = len(df_sto)
        total_saldo_awal += row.saldo_awal

        # Assign
        row.assign = len(df_sto[df_sto['status'] == 'assign'])

        # Progress Harian
        total_row_berhasil = 0
        for t in range(1, 32):
            count = len(df_sto[
                (df_sto['status'] == 'close') &
                (df_sto['bulan'] == bulan) &
                (df_sto['tahun'] == tahun) &
                (df_sto['tanggal'] == t)
            ])
            setattr(row, f"t{t}", count)
            total_row_berhasil += count
            total_tanggal[f"t{t}"] += count

        # Total Berhasil
        row.berhasil = len(df_sto[df_sto['status'] == 'close'])
        total_berhasil += row.berhasil

        # Kendala
        row.kendala = len(df_sto[df_sto['status'] == 'kendala'])
        total_kendala += row.kendala

        # Sisa Saldo
        row.saldo_akhir = len(df_sto[df_sto['status'] == 'open'])
        total_saldo_akhir += row.saldo_akhir

        # Total Teknisi
        total_teknisi += row.teknisi or 0

        row.waktu_update = datetime.now()

        print(f"✅ {sto} → SALDO AWAL: {row.saldo_awal}, ASSIGN: {row.assign}, "
              f"BERHASIL: {row.berhasil}, KENDALA: {row.kendala}, SISA: {row.saldo_akhir}")

    # Update baris total
    for row in records:
        if row.is_total_row:
            row.teknisi = total_teknisi
            row.saldo_awal = total_saldo_awal
            row.berhasil = total_berhasil
            row.kendala = total_kendala
            row.saldo_akhir = total_saldo_akhir
            row.waktu_update = datetime.now()

            for t in range(1, 32):
                setattr(row, f"t{t}", total_tanggal[f"t{t}"])
            print("✅ Baris TOTAL diupdate.")
