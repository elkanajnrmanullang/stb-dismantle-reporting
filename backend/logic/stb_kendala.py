import pandas as pd
from datetime import datetime
from calendar import monthrange
from .models import KendalaSTB

def _normalize_series(s: pd.Series) -> pd.Series:
    """
    
    """
    return (
        s.astype(str)
         .str.strip()
         .str.replace(r"\s+", " ", regex=True)
         .str.lower()
    )


def _normalize_str(x) -> str:
    """
    Normalisasi single string: str, trim, collapse spaces, lower-case.
    """
    if x is None:
        return ""
    return " ".join(str(x).strip().split()).lower()


def _unify_status(val: str) -> str:
    """
    """
    v = _normalize_str(val)
    if v == "kendala":
        return "kendala"
    if v == "close":
        return "close"
    if v == "open":
        return "open"
    if v == "tiba":
        return "tiba"
    if v == "progress":
        return "progress"
    if v == "sampai":
        return "sampai"
    if v == "assign":
        return "assign"
    return v  


# ========== Util Parsing Tanggal ==========
def _parse_last_activity_exact(series: pd.Series) -> pd.Series:
    """
   
    """
    s = pd.Series([pd.NaT] * len(series), index=series.index)

    formats = [
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y %H:%M:%S",
    ]
    remaining = series.copy()

    for fmt in formats:
        mask = s.isna()
        if not mask.any():
            break
        parsed = pd.to_datetime(remaining[mask], format=fmt, errors="coerce")
        s.loc[mask] = parsed

    mask = s.isna()
    if mask.any():
        parsed = pd.to_datetime(remaining[mask], errors="coerce", dayfirst=True)
        s.loc[mask] = parsed

    return s

def process_kendala_stb(df: pd.DataFrame, records: list, bulan: int, tahun: int) -> None:
    """

    """
    if df is None or df.empty:
        print("⚠️ KendalaSTB | DataFrame kosong, tidak diproses.")
        return

    required = {"status", "id_sto", "last_activity_at"}
    cols_lower = {c.lower(): c for c in df.columns}
    missing = [c for c in required if c not in cols_lower]
    if missing:
        raise KeyError(f"Kolom wajib hilang: {missing}. Kolom tersedia: {list(df.columns)}")

    df = df.copy()

    df["status"] = _normalize_series(df[cols_lower["status"]]).map(_unify_status)
    df["id_sto"] = _normalize_series(df[cols_lower["id_sto"]])

    df["last_activity_at"] = _parse_last_activity_exact(df[cols_lower["last_activity_at"]])
    df = df[~df["last_activity_at"].isna()].copy()

    df["bulan"] = df["last_activity_at"].dt.month
    df["tahun"] = df["last_activity_at"].dt.year
    df["tanggal"] = df["last_activity_at"].dt.day

    print(f"✅ KendalaSTB | bulan={bulan} tahun={tahun} | status unik={df['status'].dropna().unique()}")

    g_totals = (
        df.groupby(["id_sto", "status"], dropna=False)
          .size()
          .rename("n")
          .reset_index()
    )
    totals_dict = {(r["id_sto"], r["status"]): int(r["n"]) for _, r in g_totals.iterrows()}

    df_bulan = df[(df["bulan"] == bulan) & (df["tahun"] == tahun) & (df["status"] == "kendala")]
    g_kendala = (
        df_bulan.groupby(["id_sto", "tanggal"], dropna=False)
                .size()
                .rename("n")
                .reset_index()
    )
    kendala_map = {}
    for _, r in g_kendala.iterrows():
        sto = r["id_sto"]
        day = int(r["tanggal"])
        kendala_map.setdefault(sto, {})[day] = int(r["n"])

    progress_statuses = {"tiba", "progress", "sampai"}
    days_in_month = monthrange(tahun, bulan)[1]

    for row in records:
        if getattr(row, "is_total_row", False):
            continue

        sto_norm = _normalize_str(row.sto)

        saldo_awal = 0
        progress_ct = 0
        berhasil_ct = 0
        saldo_akhir_ct = 0

        for (k_sto, k_status), n in totals_dict.items():
            if k_sto != sto_norm:
                continue
            saldo_awal += n
            if k_status in progress_statuses:
                progress_ct += n
            elif k_status == "close":
                berhasil_ct += n
            elif k_status == "open":
                saldo_akhir_ct += n

        row.saldo_awal = int(saldo_awal)
        row.progress = int(progress_ct)
        row.berhasil = int(berhasil_ct)
        row.saldo_akhir = int(saldo_akhir_ct)

        total_kendala_baris = 0
        day_counts = kendala_map.get(sto_norm, {})
        for t in range(1, 32):
            val = int(day_counts.get(t, 0)) if t <= days_in_month else 0
            setattr(row, f"t{t}", val)
            total_kendala_baris += val

        row.kendala = int(total_kendala_baris)
        row.waktu_update = datetime.now()

        print(
            f"🔹 STO {row.sto} -> SA:{row.saldo_awal} "
            f"PROG:{row.progress} KEND(m):{row.kendala} "
            f"CLOSE:{row.berhasil} OPEN:{row.saldo_akhir}"
        )


def generate_kendala_stb_total_row(records: list) -> list:
    """

    """
    total_row = KendalaSTB(
        teknisi=sum((r.teknisi or 0) for r in records if not r.is_total_row),
        service_area="TOTAL",
        sto="",
        saldo_awal=sum((r.saldo_awal or 0) for r in records if not r.is_total_row),
        progress=sum((r.progress or 0) for r in records if not r.is_total_row),
        berhasil=sum((r.berhasil or 0) for r in records if not r.is_total_row),
        kendala=sum((r.kendala or 0) for r in records if not r.is_total_row),
        saldo_akhir=sum((r.saldo_akhir or 0) for r in records if not r.is_total_row),
        is_total_row=True,
        waktu_update=datetime.now(),
    )

    for i in range(1, 32):
        setattr(
            total_row,
            f"t{i}",
            sum((getattr(r, f"t{i}", 0) or 0) for r in records if not r.is_total_row),
        )

    return [total_row]
    