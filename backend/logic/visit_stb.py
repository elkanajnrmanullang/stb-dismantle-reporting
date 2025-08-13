import pandas as pd
from datetime import datetime, date
from logic.models import VisitSTB

# ======== ACUAN STO -> SERVICE AREA (sama dengan visit_dismantle) ========
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
    Normalisasi status untuk STB:
    - CLOSE/BERHASIL/DONE/SUKSES -> 'close'
    - mengandung KENDALA/GAGAL/TROUBLE -> 'kendala'
    - mengandung 'assign' -> 'assign'
    """
    v = _norm_str(val).replace("_", " ").replace("-", " ")
    if v in {"close", "closed", "berhasil", "done", "sukses"}: return "close"
    if "kendala" in v or "gagal" in v or "trouble" in v:       return "kendala"
    if "assign" in v:                                          return "assign"
    return v

def _to_datetime_general(series: pd.Series) -> pd.Series:
    # Parser umum + dukung Excel serial
    parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)

    as_text = series.astype(str).str.strip()
    cleaned_num = pd.to_numeric(as_text.str.replace(",", ".", regex=False), errors="coerce")
    mask_num = parsed.isna() & cleaned_num.notna()
    if mask_num.any():
        parsed.loc[mask_num] = pd.to_datetime(
            cleaned_num[mask_num].astype("float64"),
            unit="D", origin="1899-12-30", errors="coerce"
        )

    remain_mask = parsed.isna()
    if remain_mask.any():
        remain = as_text[remain_mask]
        fmts = ["%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y",
                "%d-%m-%Y %H:%M", "%d-%m-%Y %H:%M:%S", "%d-%m-%Y"]
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
    # startswith fallback
    for cand in candidates:
        key = _norm_str(cand)
        for k, orig in norm_cols.items():
            if k.startswith(key):
                return orig
    raise KeyError(f"Kolom salah satu dari {candidates} tidak ditemukan. Kolom tersedia: {list(df.columns)}")

def _areas_from_mapping() -> list[str]:
    return list(dict.fromkeys(STO_TO_SERVICE_AREA.values()))

def _sa_to_stos() -> dict[str, set[str]]:
    sa_map: dict[str, set[str]] = {}
    for sto, sa in STO_TO_SERVICE_AREA.items():
        sa_map.setdefault(sa.upper(), set()).add(sto.upper())
    return sa_map

# ---- Seed placeholder VisitSTB ----
def ensure_visit_stb_placeholders(db_session) -> None:
    exist = {
        (r.service_area or "").strip().upper()
        for r in db_session.query(VisitSTB).filter_by(is_total=False).all()
    }
    all_areas = [a.upper() for a in _areas_from_mapping()]
    need = []
    now = datetime.now()
    for sa in all_areas:
        if sa not in exist:
            need.append(VisitSTB(
                service_area=sa, visit=0, dismantle=0, kendala=0, sisa_assign=0,
                is_total=False, waktu_update=now
            ))
    if need:
        for r in need: db_session.add(r)
        db_session.flush()
        print(f"✅ Seed VisitSTB placeholders: {len(need)} area baru ditambahkan.")

# ===== Core =====
def process_visit_stb(df: pd.DataFrame, db_session, today: date | None = None) -> None:
    """
    Replacement/STB (per Service Area):
    - dismantle(HI) = COUNTIFS(status='close',   id_sto∈SA, DATE(last_activity_at)=TODAY)
    - kendala (HI)  = COUNTIFS(status='kendala', id_sto∈SA, DATE(last_activity_at)=TODAY)
    - visit (HI)    = dismantle + kendala
    - sisa_assign   = COUNTIFS(status='assign',  id_sto∈SA)   <-- tanpa filter tanggal (pakai SEMUA baris file)
    """
    ensure_visit_stb_placeholders(db_session)

    rows = db_session.query(VisitSTB).filter_by(is_total=False).all()
    idx = { (r.service_area or "").strip().upper(): r for r in rows }

    if df is None or df.empty:
        for r in rows:
            r.visit = r.dismantle = r.kendala = r.sisa_assign = 0
            r.waktu_update = datetime.now()
        _write_total_row(db_session, rows)
        return

    # Kolom inti (beri banyak kandidat agar robust)
    col_sto = _find_col(df, ["id_sto", "sto", "id sto", "sto id", "idsto"])
    col_status = _find_col(df, ["status", "sts", "status desc", "keterangan status"])
    col_tgl = _find_col(df, ["last_activity_at", "last activity", "last activity at", "tgl aktivitas", "tanggal aktivitas"])

    df = df.copy()
    df[col_status] = _norm_series(df[col_status]).map(_unify_status)
    df[col_sto] = df[col_sto].astype(str).str.strip().str.upper()
    df[col_tgl] = _to_datetime_general(df[col_tgl])

    if today is None:
        today = datetime.now().date()
    j_days = (pd.Timestamp(today) - df[col_tgl].dt.normalize()).dt.days

    sa_to_stos = _sa_to_stos()
    now = datetime.now()

    for sa in _areas_from_mapping():
        key = sa.upper()
        r = idx.get(key)
        if r is None:
            r = VisitSTB(service_area=key, is_total=False)
            db_session.add(r); db_session.flush()
            idx[key] = r

        sto_set = sa_to_stos.get(key, set())
        if not sto_set:
            r.visit = r.dismantle = r.kendala = r.sisa_assign = 0
            r.waktu_update = now
            continue

        mask_sa = df[col_sto].isin(sto_set)

        # HI (hari ini) dari last_activity_at
        dsm_hi = int(((df[col_status] == "close")   & mask_sa & (j_days == 0)).sum())
        ken_hi = int(((df[col_status] == "kendala") & mask_sa & (j_days == 0)).sum())
        # Sisa Assign: semua data status 'assign' (tanpa filter tanggal)
        sisa   = int(((df[col_status] == "assign") & mask_sa).sum())

        r.dismantle   = dsm_hi
        r.kendala     = ken_hi
        r.visit       = dsm_hi + ken_hi
        r.sisa_assign = sisa
        r.waktu_update = now

        print(f"🔹 VISIT-STB | {key} -> HI:CLOSE={dsm_hi} KEND={ken_hi} SISA(assign, all)={sisa}  (STO={len(sto_set)})")

    _write_total_row(db_session, rows)

def _write_total_row(db_session, rows):
    total_visit = sum((r.visit or 0) for r in rows)
    total_dsm   = sum((r.dismantle or 0) for r in rows)
    total_kend  = sum((r.kendala or 0) for r in rows)
    total_sisa  = sum((r.sisa_assign or 0) for r in rows)

    db_session.query(VisitSTB).filter_by(is_total=True).delete()
    db_session.add(VisitSTB(
        service_area="TOTAL",
        jumlah_visit=total_visit,
        jumlah_dismantle=total_dsm,
        jumlah_kendala=total_kend,
        jumlah_sisa_assign=total_sisa,
        is_total=True,
        waktu_update=datetime.now()
    ))