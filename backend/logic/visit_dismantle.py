import pandas as pd
from datetime import datetime, date
from logic.models import VisitDismantle

# ======== ACUAN STO -> SERVICE AREA ========
STO_TO_SERVICE_AREA = {
    "BOO": "BOGOR",
    "CPS": "CIAPUS - PAGELARAN", "PAG": "CIAPUS - PAGELARAN",
    "CJU": "CIAWI - CISARUA", "CRI": "CIAWI - CISARUA", "CSR": "CIAWI - CISARUA", "CWI": "CIAWI - CISARUA",
    "BJD": "CIBINONG", "CBI": "CIBINONG", "TJH": "CIBINONG",
    "CAU": "CILEUNGSI", "CLS": "CILEUNGSI", "JGL": "CILEUNGSI",
    "CNE": "CINERE", "PCM": "CINERE",
    "DEP": "DEPOK",
    "CGD": "DRAMAGA", "DMG": "DRAMAGA", "JSA": "DRAMAGA", "LBI": "DRAMAGA", "LWL": "DRAMAGA",
    "CSN": "GUNUNG PUTRI - CIANGSANA", "GPI": "GUNUNG PUTRI - CIANGSANA",
    "KHL": "KEDUNG HALANG",
    "CSE": "PARUNG - SEMPLAK", "PAR": "PARUNG - SEMPLAK", "SPL": "PARUNG - SEMPLAK",
    "CTR": "PASIR MAUNG", "PMU": "PASIR MAUNG", "STL": "PASIR MAUNG",
    "CSL": "SUKMAJAYA", "SKJ": "SUKMAJAYA",
    "BGL": "CIBADAK", "CBD": "CIBADAK", "CCR": "CIBADAK", "CKB": "CIBADAK", "JPK": "CIBADAK",
    "KLU": "CIBADAK", "PLR": "CIBADAK",
    "CMO": "SUKABUMI", "NLD": "SUKABUMI", "SGN": "SUKABUMI", "SKB": "SUKABUMI",
}

# ===== Utilities =====
def _norm_series(s: pd.Series) -> pd.Series:
    return (
        s.astype(str)
         .str.strip()
         .str.replace(r"\s+", " ", regex=True)
         .str.lower()
    )

def _norm_str(x) -> str:
    if x is None:
        return ""
    return " ".join(str(x).strip().split()).lower()

def _unify_status(val: str) -> str:
    """
    Normalisasi status umum untuk DISMANTLE/KENDALA/PROGRESS.
    Catatan: SAMPAI/TIBA/TAKEN TIDAK diubah ke 'cek lensa' di sini,
    karena aturan CEK LENSA khusus hanya untuk perhitungan SISA (lihat _status_for_sisa).
    """
    v = _norm_str(val).replace("_", " ").replace("-", " ")
    # CLOSE
    if v in {"close", "closed", "berhasil", "done", "sukses"} or "close" in v:
        return "close"
    # KENDALA
    if "kendala" in v or "gagal" in v or "trouble" in v:
        return "kendala"
    # CEK LENSA / ASSIGN (akan dihitung ke SISA tanpah batas tanggal)
    if (("cek" in v and "lensa" in v) or "assign" in v or "assigned" in v):
        return "cek lensa"
    # OPEN
    if "open" in v:
        return "open"
    # PROGRESS / TIBA / SAMPAI / TAKEN (nanti dipetakan ke 'cek lensa' khusus untuk SISA)
    if v in {"progress"} or "tiba" in v or "sampai" in v or "taken" in v:
        return "progress"
    return v

def _to_datetime_general(series: pd.Series) -> pd.Series:
    # 1) parse general
    parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)

    # 2) Excel serial (angka)
    as_text = series.astype(str).str.strip()
    cleaned_num = pd.to_numeric(as_text.str.replace(",", ".", regex=False), errors="coerce")
    mask_num = parsed.isna() & cleaned_num.notna()
    if mask_num.any():
        parsed.loc[mask_num] = pd.to_datetime(
            cleaned_num[mask_num].astype("float64"),
            unit="D", origin="1899-12-30", errors="coerce"
        )

    # 3) fallback berbagai format umum
    remain_mask = parsed.isna()
    if remain_mask.any():
        remain = as_text[remain_mask]
        fmts = [
            "%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y",
            "%d-%m-%Y %H:%M", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y",
            "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"
        ]
        tmp = pd.Series([pd.NaT] * len(remain), index=remain.index)
        for fmt in fmts:
            m = tmp.isna()
            if not m.any(): break
            tmp.loc[m] = pd.to_datetime(remain[m], format=fmt, errors="coerce")
        parsed.loc[remain_mask] = tmp

    return parsed.fillna(pd.Timestamp.today().normalize())

def _find_col(df: pd.DataFrame, candidates) -> str:
    norm_cols = {_norm_str(c): c for c in df.columns}
    for cand in candidates:
        key = _norm_str(cand)
        if key in norm_cols:
            return norm_cols[key]
    for cand in candidates:
        key = _norm_str(cand)
        for k, orig in norm_cols.items():
            if k.startswith(key):
                return orig
    raise KeyError(f"Kolom salah satu dari {candidates} tidak ditemukan. Kolom tersedia: {list(df.columns)}")

def _areas_from_mapping():
    return list(dict.fromkeys(STO_TO_SERVICE_AREA.values()))

def _sa_to_stos():
    sa_map = {}
    for sto, sa in STO_TO_SERVICE_AREA.items():
        sa_map.setdefault(sa.upper(), set()).add(sto.upper())
    return sa_map

# ---- Seed placeholder (dan FLUSH!) ----
def ensure_visit_dismantle_placeholders(db_session) -> None:
    exist = { (r.service_area or "").strip().upper()
              for r in db_session.query(VisitDismantle).filter_by(is_total=False).all() }
    all_areas = [a.upper() for a in _areas_from_mapping()]
    need = []
    now = datetime.now()
    for sa in all_areas:
        if sa not in exist:
            need.append(VisitDismantle(
                service_area=sa, visit=0, dismantle=0, kendala=0, sisa_assign=0,
                is_total=False, waktu_update=now
            ))
    if need:
        for r in need: db_session.add(r)
        db_session.flush()
        print(f"✅ Seed VisitDismantle placeholders: {len(need)} area baru ditambahkan.")

# ===== Core =====
def process_visit_dismantle(df: pd.DataFrame, db_session, today: date | None = None) -> None:
    """
    Dismantle(HI) = COUNTIFS(status='close',   STO∈SA, HI)
    Kendala(HI)   = COUNTIFS(status='kendala', STO∈SA, HI)
    Sisa Assign   = COUNTIFS(status_for_sisa == 'cek lensa', STO∈SA)  # TANPA filter tanggal
                     di mana status_for_sisa = IF(OR(status in {'sampai','tiba','taken'}), 'cek lensa', status_unified)
    Total Visit   = Dismantle + Kendala
    """
    ensure_visit_dismantle_placeholders(db_session)

    rows = db_session.query(VisitDismantle).filter_by(is_total=False).all()
    idx = { (r.service_area or "").strip().upper(): r for r in rows }

    if df is None or df.empty:
        now = datetime.now()
        for r in rows:
            r.visit = r.dismantle = r.kendala = r.sisa_assign = 0
            r.waktu_update = now
        _write_total_row(db_session)
        return

    # Kolom wajib
    col_sto = _find_col(df, ["sto", "id_sto"])
    col_status = _find_col(df, ["status"])
    col_tgl = _find_col(df, [
        "tanggal dismantling", "tgl dismantling", "tanggal_dismantling", "tgl_dismantling",
        "tanggal create dapros", "tgl create dapros", "tanggal_create_dapros", "tgl_create_dapros",
        "created_at", "tanggal"
    ])

    # === DEBUG: kolom terdeteksi
    print(f"🧭 VISIT-DISM: kolom -> STO='{col_sto}', STATUS='{col_status}', TANGGAL='{col_tgl}'")

    df = df.copy()

    status_raw_norm = _norm_series(df[col_status])
    df["_status_norm_raw"] = status_raw_norm

    df[col_status] = status_raw_norm.map(_unify_status)

    df["_status_for_sisa"] = df[col_status].copy()
    mask_excel_like = (
        df["_status_norm_raw"].str.contains(r"\bsampai\b", na=False)
        | df["_status_norm_raw"].str.contains(r"\btiba\b", na=False)
        | df["_status_norm_raw"].str.contains(r"\btaken\b", na=False)
    )
    df.loc[mask_excel_like, "_status_for_sisa"] = "cek lensa"

    df[col_sto] = df[col_sto].astype(str).str.strip().str.upper()
    df[col_tgl] = _to_datetime_general(df[col_tgl])

    # === DEBUG: distribusi status
    print("📊 VISIT-DISM: distribusi status (unified):", df[col_status].value_counts(dropna=False).to_dict())
    print("📊 VISIT-DISM: distribusi status_for_sisa:", df["_status_for_sisa"].value_counts(dropna=False).to_dict())

    if today is None:
        today = datetime.now().date()
    tgl_norm = df[col_tgl].dt.normalize()
    today_ts = pd.Timestamp(today)

    sa_to_stos = _sa_to_stos()
    now = datetime.now()

    # STO unknown (tidak termapping) — sering jadi penyebab hitungan 0
    all_file_stos = set(df[col_sto].unique())
    mapped_stos = set(STO_TO_SERVICE_AREA.keys())
    unknown_stos = sorted(all_file_stos - mapped_stos)
    if unknown_stos:
        print(f"⚠️ VISIT-DISM: STO belum terpetakan ({len(unknown_stos)}): {unknown_stos[:30]} ...")

    for sa in _areas_from_mapping():
        key = sa.upper()
        r = idx.get(key)
        if r is None:
            r = VisitDismantle(service_area=key, is_total=False)
            db_session.add(r); db_session.flush()
            idx[key] = r

        sto_set = sa_to_stos.get(key, set())
        if not sto_set:
            r.visit = r.dismantle = r.kendala = r.sisa_assign = 0
            r.waktu_update = now
            continue

        mask_sa = df[col_sto].isin(sto_set)
        mask_hi = (tgl_norm == today_ts)

        # Hitung HI untuk dismantle & kendala
        dsm_hi = int(((df[col_status] == "close")   & mask_sa & mask_hi).sum())
        ken_hi = int(((df[col_status] == "kendala") & mask_sa & mask_hi).sum())

        # SISA tanpa filter tanggal, pakai status_for_sisa
        sisa_mask = (df["_status_for_sisa"] == "cek lensa") & mask_sa
        sisa = int(sisa_mask.sum())

        # === DEBUG per area
        if sisa > 0 or dsm_hi > 0 or ken_hi > 0:
            sample_sisa = df.loc[sisa_mask, [col_sto, "_status_norm_raw"]].head(3).to_dict("records")
            print(f"🔹 VISIT-DISM | {key} -> HI:CLOSE={dsm_hi} KEND={ken_hi} SISA={sisa} (STO={len(sto_set)}) sampel_sisa={sample_sisa}")
        else:
            print(f"▫️ VISIT-DISM | {key} -> HI:CLOSE=0 KEND=0 SISA=0 (STO={len(sto_set)})")

        r.dismantle = dsm_hi
        r.kendala   = ken_hi
        r.sisa_assign = sisa
        r.visit = dsm_hi + ken_hi
        r.waktu_update = now

    _write_total_row(db_session)

def _write_total_row(db_session):
    rows_now = db_session.query(VisitDismantle).filter_by(is_total=False).all()
    total_visit = sum((r.visit or 0) for r in rows_now)
    total_dsm   = sum((r.dismantle or 0) for r in rows_now)
    total_kend  = sum((r.kendala or 0) for r in rows_now)
    total_sisa  = sum((r.sisa_assign or 0) for r in rows_now)

    db_session.query(VisitDismantle).filter_by(is_total=True).delete()
    db_session.add(VisitDismantle(
        service_area="TOTAL",
        jumlah_visit=total_visit,
        jumlah_dismantle=total_dsm,
        jumlah_kendala=total_kend,
        jumlah_sisa_assign=total_sisa,
        is_total=True,
        waktu_update=datetime.now()
    ))
    print(f"✅ VISIT-DISM TOTAL -> visit={total_visit}, dismantle={total_dsm}, kendala={total_kend}, sisa={total_sisa}")
