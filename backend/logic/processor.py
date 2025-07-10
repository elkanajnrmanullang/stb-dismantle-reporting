import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows
from datetime import datetime, timedelta

def generate_25_to_25_dates(start_date, end_date):
    current = start_date
    result = []
    while current <= end_date:
        result.append(current.strftime('%d-%m'))
        current += timedelta(days=1)
    return result

def process_files(repl1, repl2, dis1, dis2, output_path, start_date=None, end_date=None):
    df_repl1 = pd.read_excel(repl1)
    df_repl2 = pd.read_excel(repl2)
    df_dis1 = pd.read_excel(dis1)
    df_dis2 = pd.read_excel(dis2)

    df_stb = pd.concat([df_repl1, df_repl2], ignore_index=True)
    df_dismantle = pd.concat([df_dis1, df_dis2], ignore_index=True)

    for df in [df_stb, df_dismantle]:
        df['Tanggal'] = pd.to_datetime(df['Tanggal'], dayfirst=True, errors='coerce')
        if start_date and end_date:
            df.dropna(subset=['Tanggal'], inplace=True)
            df = df[(df['Tanggal'] >= start_date) & (df['Tanggal'] <= end_date)]
        df['Tanggal_str'] = df['Tanggal'].dt.strftime('%d-%m')

    paste_stb = df_stb.copy()
    paste_dismantle = df_dismantle.copy()

    stb_summary = df_stb.groupby(['Area', 'Tanggal_str']).size().unstack(fill_value=0).sort_index(axis=1)
    dis_summary = df_dismantle.groupby(['Area', 'Tanggal_str']).size().unstack(fill_value=0).sort_index(axis=1)

    wb = Workbook()
    ws_stb = wb.active
    ws_stb.title = "PASTE STB"
    for r in dataframe_to_rows(paste_stb, index=False, header=True):
        ws_stb.append(r)

    ws_dis = wb.create_sheet("PASTE DISMANTLE")
    for r in dataframe_to_rows(paste_dismantle, index=False, header=True):
        ws_dis.append(r)

    ws_dash_stb = wb.create_sheet("DASHBOARD STB")
    ws_dash_stb.append(['Area'] + list(stb_summary.columns))
    for idx, row in stb_summary.iterrows():
        ws_dash_stb.append([idx] + row.tolist())

    ws_dash_dis = wb.create_sheet("DASHBOARD DISMANTLE")
    ws_dash_dis.append(['Area'] + list(dis_summary.columns))
    for idx, row in dis_summary.iterrows():
        ws_dash_dis.append([idx] + row.tolist())

    wb.save(output_path)

    return generate_25_to_25_dates(start_date, end_date)

def get_tanggal_list_from_output(output_path, sheet_name="DASHBOARD STB"):
    try:
        df = pd.read_excel(output_path, sheet_name=sheet_name)
        return list(df.columns[1:])
    except Exception:
        return []
