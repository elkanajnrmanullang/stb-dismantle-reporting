from logic.database import SessionLocal
from logic.models import (
    ProgressDismantle, KendalaDismantle,
    STBProgress, KendalaSTB,
    VisitDismantle, VisitSTB
)
from datetime import datetime

placeholder_area = [
    {'teknisi': 18, 'service_area': 'BOGOR', 'sto': 'BOO'},
    {'teknisi': 3, 'service_area': 'CIAPUS - PAGELARAN', 'sto': 'CPS'},
    {'teknisi': 7, 'service_area': 'CIAPUS - PAGELARAN', 'sto': 'PAG'},
    {'teknisi': 3, 'service_area': 'CIAWI - CISARUA', 'sto': 'CJU'},
    {'teknisi': 9, 'service_area': 'CIAWI - CISARUA', 'sto': 'CRI'},
    {'teknisi': 10, 'service_area': 'CIAWI - CISARUA', 'sto': 'CSR'},
    {'teknisi': 11, 'service_area': 'CIAWI - CISARUA', 'sto': 'CWI'},
    {'teknisi': 4, 'service_area': 'CIBINONG', 'sto': 'BJD'},
    {'teknisi': 14, 'service_area': 'CIBINONG', 'sto': 'CBI'},
    {'teknisi': 2, 'service_area': 'CIBINONG', 'sto': 'TJH'},
    {'teknisi': 2, 'service_area': 'CILEUNGSI', 'sto': 'CAU'},
    {'teknisi': 11, 'service_area': 'CILEUNGSI', 'sto': 'CLS'},
    {'teknisi': 2, 'service_area': 'CILEUNGSI', 'sto': 'JGL'},
    {'teknisi': 5, 'service_area': 'CINERE', 'sto': 'CNE'},
    {'teknisi': 6, 'service_area': 'CINERE', 'sto': 'PCM'},
    {'teknisi': 17, 'service_area': 'DEPOK', 'sto': 'DEP'},
    {'teknisi': 2, 'service_area': 'DRAMAGA', 'sto': 'CGD'},
    {'teknisi': 9, 'service_area': 'DRAMAGA', 'sto': 'DMG'},
    {'teknisi': 1, 'service_area': 'DRAMAGA', 'sto': 'JSA'},
    {'teknisi': 1, 'service_area': 'DRAMAGA', 'sto': 'LBI'},
    {'teknisi': 9, 'service_area': 'DRAMAGA', 'sto': 'LWL'},
    {'teknisi': 5, 'service_area': 'GUNUNG PUTRI - CIANGSANA', 'sto': 'CSN'},
    {'teknisi': 3, 'service_area': 'GUNUNG PUTRI - CIANGSANA', 'sto': 'GPI'},
    {'teknisi': 8, 'service_area': 'KEDUNG HALANG', 'sto': 'KHL'},
    {'teknisi': 2, 'service_area': 'PARUNG - SEMPLAK', 'sto': 'CSE'},
    {'teknisi': 4, 'service_area': 'PARUNG - SEMPLAK', 'sto': 'PAR'},
    {'teknisi': 12, 'service_area': 'PARUNG - SEMPLAK', 'sto': 'SPL'},
    {'teknisi': 3, 'service_area': 'PASIR MAUNG', 'sto': 'CTR'},
    {'teknisi': 2, 'service_area': 'PASIR MAUNG', 'sto': 'PMU'},
    {'teknisi': 2, 'service_area': 'PASIR MAUNG', 'sto': 'STL'},
    {'teknisi': 18, 'service_area': 'SUKMAJAYA', 'sto': 'CSL'},
    {'teknisi': 5, 'service_area': 'SUKMAJAYA', 'sto': 'SKJ'},
    {'teknisi': 1, 'service_area': 'CIBADAK', 'sto': 'BGL'},
    {'teknisi': 9, 'service_area': 'CIBADAK', 'sto': 'CBD'},
    {'teknisi': 5, 'service_area': 'CIBADAK', 'sto': 'CCR'},
    {'teknisi': 2, 'service_area': 'CIBADAK', 'sto': 'CKB'},
    {'teknisi': 4, 'service_area': 'CIBADAK', 'sto': 'JPK'},
    {'teknisi': 1, 'service_area': 'CIBADAK', 'sto': 'KLU'},
    {'teknisi': 6, 'service_area': 'CIBADAK', 'sto': 'PLR'},
    {'teknisi': 5, 'service_area': 'SUKABUMI', 'sto': 'CMO'},
    {'teknisi': 1, 'service_area': 'SUKABUMI', 'sto': 'NLD'},
    {'teknisi': 2, 'service_area': 'SUKABUMI', 'sto': 'SGN'},
    {'teknisi': 23, 'service_area': 'SUKABUMI', 'sto': 'SKB'}
]

visit_service_areas = [
    'BOGOR', 'CIAPUS - PAGELARAN', 'CIAWI - CISARUA',
    'CIBADAK', 'CIBINONG', 'CILEUNGSI', 'CINERE', 'DEPOK',
    'DRAMAGA', 'GUNUNG PUTRI - CIANGSANA', 'KEDUNG HALANG',
    'PARUNG - SEMPLAK', 'PASIR MAUNG', 'SUKABUMI', 'SUKMAJAYA'
]

def insert_placeholder():
    db = SessionLocal()
    now = datetime.now()
    success = 0
    failed = 0

    for area in placeholder_area:
        exists = db.query(ProgressDismantle).filter_by(service_area=area['service_area'], sto=area['sto']).first()
        if exists:
            continue 

        try:
            db.add_all([
                ProgressDismantle(teknisi=area['teknisi'], service_area=area['service_area'], sto=area['sto'], waktu_update=now),
                KendalaDismantle(teknisi=area['teknisi'], service_area=area['service_area'], sto=area['sto'], waktu_update=now),
                STBProgress(teknisi=area['teknisi'], service_area=area['service_area'], sto=area['sto'], waktu_update=now),
                KendalaSTB(teknisi=area['teknisi'], service_area=area['service_area'], sto=area['sto'], waktu_update=now)
            ])
            success += 1
        except Exception as e:
            print(f"❌ Gagal insert untuk {area['service_area']} - {area['sto']}: {e}")
            failed += 1

    for sa in visit_service_areas:
        try:
            if not db.query(VisitDismantle).filter_by(service_area=sa).first():
                db.add(VisitDismantle(service_area=sa))
            if not db.query(VisitSTB).filter_by(service_area=sa).first():
                db.add(VisitSTB(service_area=sa))
        except Exception as e:
            print(f"❌ Gagal insert visit untuk {sa}: {e}")

    try:
        db.commit()
        print(f"✅ {success} area berhasil dimasukkan ke 4 tabel utama (x4 = {success*4} records)")
        print(f"✅ {len(visit_service_areas)} area berhasil dimasukkan ke tabel visit_dismantle & visit_stb (x2 = {len(visit_service_areas)*2} records)")
        if failed > 0:
            print(f"⚠️ {failed} area gagal insert.")
    except Exception as e:
        print(f"❌ Commit gagal: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    insert_placeholder()
