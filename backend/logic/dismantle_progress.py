import pandas as pd
from datetime import datetime

def process_dismantle_progress(df: pd.DataFrame, records: list, bulan: int, tahun: int):
    df['TANGGAL DISMANTLING'] = pd.to_datetime(
        df['TANGGAL DISMANTLING'], errors='coerce', dayfirst=True
    )
    df['bulan'] = df['TANGGAL DISMANTLING'].dt.month
    df['tahun'] = df['TANGGAL DISMANTLING'].dt.year

    print("DEBUG TANGGAL")
    print("Unik STATUS:", df['STATUS'].dropna().unique())
    print("Bulan unik:", df['bulan'].dropna().unique())
    print("Tahun unik:", df['tahun'].dropna().unique())
    print("Contoh tanggal:", df['TANGGAL DISMANTLING'].head(3))
    print("Jumlah NaT (gagal parsing):", df['TANGGAL DISMANTLING'].isna().sum())

    for record in records:
        sto = record.sto
        df_sto = df[df['STO'].astype(str).str.strip().str.upper() == sto.upper()]

        # Berhasil & Kendala Bulan Lalu
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
            df_sto['STATUS'].astype(str).str.strip().str.upper().isin(['TIBA', 'SAMPAI'])
        ].shape[0]

        # Hitung t1–t31 & total berhasil
        total_berhasil = 0
        for i in range(1, 32):
            kondisi = (
                (df_sto['STATUS'].astype(str).str.strip().str.upper() == 'CLOSE') &
                (df_sto['TANGGAL DISMANTLING'].dt.day == i) &
                (df_sto['bulan'] == bulan) &
                (df_sto['tahun'] == tahun)
            )
            count = df_sto[kondisi].shape[0]
            setattr(record, f"t{i}", count)
            total_berhasil += count

        record.berhasil = total_berhasil

        # Hitung kendala bulan berjalan
        record.kendala = df_sto[
            (df_sto['STATUS'].astype(str).str.strip().str.upper() == 'KENDALA') &
            (df_sto['bulan'] == bulan) &
            (df_sto['tahun'] == tahun)
        ].shape[0]

        # DEBUG sisa saldo
        jumlah_open = df_sto[
            df_sto['STATUS'].astype(str).str.strip().str.upper() == 'OPEN'
        ].shape[0]
        print(f"STO {sto} - Jumlah OPEN: {jumlah_open}")
        record.saldo_akhir = jumlah_open

        record.waktu_update = datetime.now()
