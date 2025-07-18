import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from datetime import datetime

def detect_column(df, expected_names):
    if isinstance(expected_names, str):
        expected_names = [expected_names]
    for expected in expected_names:
        for col in df.columns:
            if col.strip().lower() == expected.strip().lower():
                return col
    raise ValueError(f"❌ Kolom tidak ditemukan. Kolom tersedia: {list(df.columns)}")

def process_files(repl1, repl2, dis1, dis2, output_path, start_date=None, end_date=None):
    df_repl1 = pd.read_excel(repl1)
    df_repl2 = pd.read_excel(repl2)
    df_dis1 = pd.read_excel(dis1)
    df_dis2 = pd.read_excel(dis2)

    df_stb = pd.concat([df_repl1, df_repl2], ignore_index=True)
    df_dismantle = pd.concat([df_dis1, df_dis2], ignore_index=True)

    status_col_stb = detect_column(df_stb, ['status', 'STATUS'])
    status_col_dis = detect_column(df_dismantle, ['status', 'STATUS'])

    df_stb = df_stb[df_stb[status_col_stb].astype(str).str.strip().str.lower() == 'open']
    df_dismantle = df_dismantle[df_dismantle[status_col_dis].astype(str).str.strip().str.lower() == 'open']

    # Save to Excel
    wb = Workbook()

    ws_stb = wb.active
    ws_stb.title = "PASTE STB"
    for row in dataframe_to_rows(df_stb, index=False, header=True):
        ws_stb.append(row)

    ws_dis = wb.create_sheet("PASTE DISMANTLE")
    for row in dataframe_to_rows(df_dismantle, index=False, header=True):
        ws_dis.append(row)

    wb.save(output_path)
    return []  # tanggal_list kosong karena tidak digunakan lagi

def get_tanggal_list_from_output(output_path):
    return []

def get_card_summary(output_path):
    try:
        df_stb = pd.read_excel(output_path, sheet_name="PASTE STB")
        df_dis = pd.read_excel(output_path, sheet_name="PASTE DISMANTLE")

        # Deteksi kolom status
        status_col_stb = detect_column(df_stb, ['status', 'STATUS'])
        status_col_dis = detect_column(df_dis, ['status', 'STATUS'])

        total_replace = len(df_stb[df_stb[status_col_stb].astype(str).str.lower().str.strip() == 'open'])
        total_dismantle = len(df_dis[df_dis[status_col_dis].astype(str).str.lower().str.strip() == 'open'])

        return total_replace, total_dismantle

    except Exception as e:
        print("Gagal mengambil card summary:", e)
        return 0, 0
