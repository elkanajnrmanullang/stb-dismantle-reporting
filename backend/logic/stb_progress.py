import pandas as pd
from datetime import datetime
from .models import STBProgress


def process_stb_progress(df: pd.DataFrame, records: list, bulan: int, tahun: int):
    """
    STB Progress (Replacement 170K) – per STO.
      saldo_awal  = jumlah record STO (semua status, tanpa filter bulan)
      assign      = jumlah status 'assign' (tanpa filter bulan)
      t1..t31     = jumlah status 'close' per tanggal (bulan & tahun berjalan)
      berhasil    = jumlah status 'close' (tanpa filter bulan)
      kendala     = jumlah status 'kendala' (tanpa filter bulan)
      saldo_akhir = jumlah status 'open' (tanpa filter bulan)
    """
    print("✅ [DEBUG] Memulai process_stb_progress()")

    df = df.copy()

    # Normalisasi kolom (antisipasi huruf besar/kecil & spasi)
    df['status'] = (
        df['status']
        .astype(str)
        .str.lower()
        .str.replace(r'\s+', ' ', regex=True)
        .str.strip()
    )
    df['id_sto'] = (
        df['id_sto']
        .astype(str)
        .str.replace(r'\s+', ' ', regex=True)
        .str.strip()
    )
    df['last_activity_at'] = pd.to_datetime(
        df['last_activity_at'], errors='coerce', dayfirst=True
    )
    df['bulan'] = df['last_activity_at'].dt.month
    df['tahun'] = df['last_activity_at'].dt.year
    df['tanggal'] = df['last_activity_at'].dt.day

    print(f"✅ STATUS unik: {df['status'].dropna().unique()}")
    print(f"✅ Target: bulan={bulan}, tahun={tahun}")

    # Agregator total
    total_teknisi = 0
    total_saldo_awal = 0
    total_berhasil = 0
    total_kendala = 0
    total_saldo_akhir = 0
    total_tanggal = {f"t{i}": 0 for i in range(1, 32)}

    for row in records:
        if row.is_total_row:
            continue

        sto = str(row.sto)
        df_sto = df[df['id_sto'] == sto]

        # ===== Tanpa filter bulan =====
        row.saldo_awal  = int(len(df_sto))                            
        row.assign      = int((df_sto['status'] == 'assign').sum())    
        row.berhasil    = int((df_sto['status'] == 'close').sum())     
        row.kendala     = int((df_sto['status'] == 'kendala').sum())  
        row.saldo_akhir = int((df_sto['status'] == 'open').sum())     

        mask_bulan = (df_sto['bulan'] == bulan) & (df_sto['tahun'] == tahun)
        for t in range(1, 32):
            count_t = int(((df_sto['status'] == 'close') & mask_bulan & (df_sto['tanggal'] == t)).sum())
            setattr(row, f"t{t}", count_t)
            total_tanggal[f"t{t}"] += count_t

        # Agregasi total
        total_teknisi     += int(row.teknisi or 0)
        total_saldo_awal  += row.saldo_awal
        total_berhasil    += row.berhasil
        total_kendala     += row.kendala
        total_saldo_akhir += row.saldo_akhir

        row.waktu_update = datetime.now()

        print(f"🔹 STO {sto} -> SA:{row.saldo_awal} ASSIGN:{row.assign} "
              f"CLOSE(total):{row.berhasil} KEND(total):{row.kendala} OPEN(total):{row.saldo_akhir}")

    # Update baris TOTAL (jika ada)
    for row in records:
        if row.is_total_row:
            row.teknisi     = total_teknisi
            row.saldo_awal  = total_saldo_awal
            row.berhasil    = total_berhasil
            row.kendala     = total_kendala
            row.saldo_akhir = total_saldo_akhir 
            row.waktu_update = datetime.now()
            for t in range(1, 32):
                setattr(row, f"t{t}", total_tanggal[f"t{t}"])
            print("✅ Baris TOTAL diperbarui (sum per-baris).")


def generate_stb_total_rows(records, kendala_records):
    """
    Footer helper:
      - total_row: ringkasan TOTAL dari records (sum per-baris)
      - saldo_akhir_total: Σ saldo_akhir per baris (OPEN)
      - kendala_harian: dict t1..t31 hasil sum KendalaSTB per tanggal (bulan berjalan)
      - total_kendala_kolom: Σ kendala_harian
    Return: ([total_row], saldo_akhir_total, kendala_harian, total_kendala_kolom)
    """
    total_teknisi     = sum((r.teknisi or 0)     for r in records if not r.is_total_row)
    total_saldo_awal  = sum((r.saldo_awal or 0)  for r in records if not r.is_total_row)
    total_assign      = sum((r.assign or 0)      for r in records if not r.is_total_row)
    total_berhasil    = sum((r.berhasil or 0)    for r in records if not r.is_total_row)
    total_kendala     = sum((r.kendala or 0)     for r in records if not r.is_total_row)
    saldo_akhir_total = sum((r.saldo_akhir or 0) for r in records if not r.is_total_row)  # OPEN sum

    total_row = STBProgress(
        teknisi=total_teknisi,
        service_area="TOTAL",
        sto="",
        saldo_awal=total_saldo_awal,
        assign=total_assign,
        berhasil=total_berhasil,
        kendala=total_kendala,
        saldo_akhir=saldo_akhir_total,
        is_total_row=True,
        waktu_update=datetime.now()
    )

    for i in range(1, 32):
        setattr(
            total_row, f"t{i}",
            sum((getattr(r, f"t{i}", 0) or 0) for r in records if not r.is_total_row)
        )

    kendala_harian = {f"t{i}": 0 for i in range(1, 32)}
    for r in kendala_records:
        for i in range(1, 32):
            kendala_harian[f"t{i}"] += getattr(r, f"t{i}", 0) or 0
    total_kendala_kolom = sum(kendala_harian.values())

    return [total_row], saldo_akhir_total, kendala_harian, total_kendala_kolom
