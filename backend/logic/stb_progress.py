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

    for row in records:
        sto = row.sto
        df_sto = df[df['id_sto'] == sto]

        # Hitung saldo awal: seluruh data dengan sto yang sama
        row.saldo_awal = len(df_sto)

        # Assign
        row.assign = len(df_sto[df_sto['status'] == 'assign'])

        # Progress harian
        total_berhasil = 0
        for t in range(1, 32):
            count = len(df_sto[
                (df_sto['status'] == 'close') &
                (df_sto['bulan'] == bulan) &
                (df_sto['tahun'] == tahun) &
                (df_sto['tanggal'] == t)
            ])
            setattr(row, f"t{t}", count)
            total_berhasil += count

        row.berhasil = total_berhasil
        row.kendala = len(df_sto[df_sto['status'] == 'kendala'])
        row.saldo_akhir = len(df_sto[df_sto['status'] == 'open'])
        row.waktu_update = datetime.now()

        print(f"✅ {sto} → AWAL: {row.saldo_awal}, ASSIGN: {row.assign}, "
              f"BERHASIL: {row.berhasil}, KENDALA: {row.kendala}, SISA: {row.saldo_akhir}")
