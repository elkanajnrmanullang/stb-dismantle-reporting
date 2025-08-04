import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from datetime import datetime

placeholder_area = [
    {'teknisi': 18, 'service_area': 'BOGOR', 'sto': 'BOO'},
    {'teknisi': 3, 'service_area': 'CIAPUS - PAGELARAN', 'sto': 'CPS'},
    {'teknisi': 7, 'service_area': 'CIAPUS - PAGELARAN', 'sto': 'PAG'},
    {'teknisi': 9, 'service_area': 'CIBUNIAN', 'sto': 'CIB'},
]

def detect_column(df, expected_names):
    if isinstance(expected_names, str):
        expected_names = [expected_names]
    for expected in expected_names:
        for col in df.columns:
            if col.strip().lower() == expected.strip().lower():
                return col
    raise ValueError(f"❌ Kolom tidak ditemukan. Kolom tersedia: {list(df.columns)}")

def process_files(repl1, repl2, dis1, dis2, output_path, start_date=None, end_date=None):
    df_replacement1 = pd.read_excel(repl1)
    df_replacement2 = pd.read_excel(repl2)
    df_dismantle1 = pd.read_excel(dis1)
    df_dismantle2 = pd.read_excel(dis2)

    df_stb = pd.concat([df_replacement1, df_replacement2], ignore_index=True)
    df_dismantle = pd.concat([df_dismantle1, df_dismantle2], ignore_index=True)

    # Format kolom 'no_inet' jadi angka (int / pd.NA kalau gagal)
    try:
        no_inet_col_stb = detect_column(df_stb, ['no_inet'])
        df_stb[no_inet_col_stb] = pd.to_numeric(df_stb[no_inet_col_stb], errors='coerce').astype('Int64')
    except Exception as e:
        print(">> Gagal konversi no_inet STB:", e)

    try:
        no_inet_col_dis = detect_column(df_dismantle, ['no inet', 'no_inet'])
        df_dismantle[no_inet_col_dis] = pd.to_numeric(df_dismantle[no_inet_col_dis], errors='coerce').astype('Int64')
    except Exception as e:
        print(">> Gagal konversi NO INET Dismantle:", e)

    wb = Workbook()
    ws_stb = wb.active
    ws_stb.title = "PASTE STB"
    for row in dataframe_to_rows(df_stb, index=False, header=True):
        ws_stb.append(row)

    ws_dis = wb.create_sheet("PASTE DISMANTLE")
    for row in dataframe_to_rows(df_dismantle, index=False, header=True):
        ws_dis.append(row)

    wb.save(output_path)

def get_tanggal_list_from_output(output_path):
    try:
        df = pd.read_excel(output_path, sheet_name="PASTE DISMANTLE")
        tanggal_col = detect_column(df, ['tanggal', 'created_at', 'tgl'])
        df['tanggal'] = pd.to_datetime(df[tanggal_col], errors='coerce')
        tanggal_range = pd.date_range("2024-06-25", "2024-07-25")
        return [d.strftime("%-d") for d in tanggal_range]
    except:
        return list(map(str, list(range(25, 32)) + list(range(1, 26))))

def get_dismantle_kendala_table(output_path):
    df = pd.read_excel(output_path, sheet_name="PASTE DISMANTLE")
    df.columns = df.columns.str.lower()
    df['tanggal'] = pd.to_datetime(df['tanggal'], errors='coerce')
    df['bulan'] = df['tanggal'].dt.month
    df['tahun'] = df['tanggal'].dt.year
    tanggal_range = pd.date_range("2024-06-25", "2024-07-25")
    hasil = []
    grouped = df.groupby(['service area', 'sto'])

    for (area, sto), sub_df in grouped:
        row = {
            'teknisi': sub_df['teknisi'].nunique() if 'teknisi' in sub_df.columns else len(sub_df),
            'service_area': area,
            'sto': sto,
            'berhasil': sub_df[(sub_df['status'].str.upper() == 'CLOSE') & (sub_df['bulan'] == 5)].shape[0],
            'kendala': sub_df[sub_df['status'].str.upper().isin(['KENDALA', 'DELETE', 'BERBAYAR'])].shape[0],
            'saldo': sub_df.shape[0],
            'progress': sub_df[sub_df['status'].str.upper().isin(['TIBA', 'SAMPAI'])].shape[0]
        }
        progres_harian = []
        for tgl in tanggal_range:
            count = sub_df[(sub_df['status'].str.upper() == 'CLOSE') & (sub_df['tanggal'].dt.date == tgl.date())].shape[0]
            progres_harian.append(count)

        row['progres_harian'] = progres_harian
        row['berhasil'] = sum(progres_harian)
        row['kendala'] = sub_df[sub_df['status'].str.upper().isin(['KENDALA', 'DELETE', 'BERBAYAR'])].shape[0]
        row['sisa'] = sub_df[sub_df['status'].str.upper() == 'OPEN'].shape[0]
        hasil.append(row)

    if hasil:
        total_row = {
            'teknisi': sum(h['teknisi'] for h in hasil),
            'service_area': '',
            'sto': '',
            'berhasil': sum(h['berhasil'] for h in hasil),
            'kendala': sum(h['kendala'] for h in hasil),
            'saldo': sum(h['saldo'] for h in hasil),
            'progress': sum(h['progress'] for h in hasil),
            'progres_harian': [sum(h['progres_harian'][i] for h in hasil) for i in range(len(tanggal_range))]
        }
        total_row['sisa'] = sum(h['sisa'] for h in hasil)
        hasil.append(total_row)

    return hasil, [d.strftime("%-d") for d in tanggal_range]

def get_dismantle_progress_table(output_path):
    df = pd.read_excel(output_path, sheet_name="PASTE DISMANTLE")
    df.columns = df.columns.str.lower()
    df['tanggal'] = pd.to_datetime(df['tanggal'], errors='coerce')
    df['bulan'] = df['tanggal'].dt.month
    df['tahun'] = df['tanggal'].dt.year
    df['day'] = df['tanggal'].dt.day

    tanggal_range = pd.date_range("2024-06-25", "2024-07-25")
    hasil = []

    group = df.groupby(['service area', 'sto'])

    for (area, sto), group_df in group:
        row = {
            'teknisi': group_df['teknisi'].nunique() if 'teknisi' in group_df.columns else len(group_df),
            'service_area': area,
            'sto': sto,
            'berhasil': group_df[(group_df['status'].str.upper() == 'CLOSE') & (group_df['bulan'] == 5)].shape[0],
            'kendala': group_df[group_df['status'].str.upper().isin(['KENDALA', 'DELETE', 'BERBAYAR'])].shape[0],
            'saldo': group_df.shape[0],
            'progress': group_df[group_df['status'].str.upper().isin(['TIBA', 'SAMPAI'])].shape[0],
        }

        progres_harian = []
        for tgl in tanggal_range:
            count = group_df[(group_df['status'].str.upper() == 'CLOSE') & (group_df['tanggal'].dt.date == tgl.date())].shape[0]
            progres_harian.append(count)

        row['progres_harian'] = progres_harian
        row['total_berhasil'] = sum(progres_harian)
        row['total_kendala'] = row['kendala']
        row['total_sisa'] = group_df[group_df['status'].str.upper() == 'OPEN'].shape[0]

        hasil.append(row)

    if hasil:
        total_row = {
            'teknisi': sum(h['teknisi'] for h in hasil),
            'service_area': '',
            'sto': '',
            'berhasil': sum(h['berhasil'] for h in hasil),
            'kendala': sum(h['kendala'] for h in hasil),
            'saldo': sum(h['saldo'] for h in hasil),
            'progress': sum(h['progress'] for h in hasil),
            'progres_harian': [sum(h['progres_harian'][i] for h in hasil) for i in range(len(tanggal_range))],
        }
        total_row['total_berhasil'] = sum(total_row['progres_harian'])
        total_row['total_kendala'] = sum(h['total_kendala'] for h in hasil)
        total_row['total_sisa'] = sum(h['total_sisa'] for h in hasil)
        hasil.append(total_row)

    return hasil, [d.strftime("%-d") for d in tanggal_range]
