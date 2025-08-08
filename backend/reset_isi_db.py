# backend/reset_all.py

from logic.database import SessionLocal
from logic.models import (
    ProgressDismantle, KendalaDismantle,
    STBProgress, KendalaSTB,
    VisitDismantle, VisitSTB
)

def reset_table(model, fields: list[str], where_clause=None):
    db = SessionLocal()
    try:
        query = db.query(model)
        if where_clause:
            query = query.filter_by(**where_clause)
        records = query.all()

        for row in records:
            for field in fields:
                setattr(row, field, 0 if 'waktu_update' not in field else None)

        db.commit()
        print(f"✅ {model.__name__}: {len(records)} baris berhasil di-reset.")
    except Exception as e:
        db.rollback()
        print(f"❌ {model.__name__}: Gagal reset - {str(e)}")
    finally:
        db.close()

def reset_all():
    # Reset ProgressDismantle
    reset_table(ProgressDismantle, [
        'berhasil_bulan_lalu', 'kendala_bulan_lalu', 'saldo_awal',
        'progress', 'waktu_update'
    ], where_clause={"is_total_row": False})

    # Reset KendalaDismantle
    reset_table(KendalaDismantle, [f"t{i}" for i in range(1, 32)] + [
        'berhasil', 'kendala', 'saldo_awal', 'saldo_akhir', 'waktu_update'
    ], where_clause={"is_total_row": False})

    # Reset STBProgress
    reset_table(STBProgress, [f"t{i}" for i in range(1, 32)] + [
        'saldo_awal', 'assign', 'berhasil', 'kendala', 'saldo_akhir', 'waktu_update'
    ], where_clause={"is_total_row": False})

    # Reset KendalaSTB
    reset_table(KendalaSTB, [f"t{i}" for i in range(1, 32)] + [
        'saldo_awal', 'berhasil', 'kendala', 'saldo_akhir', 'waktu_update'
    ], where_clause={"is_total_row": False})

    # Reset VisitDismantle
    reset_table(VisitDismantle, ['visit', 'dismantle', 'kendala', 'sisa_assign'], where_clause={"is_total": False})

    # Reset VisitSTB
    reset_table(VisitSTB, ['visit', 'dismantle', 'kendala', 'sisa_assign'], where_clause={"is_total": False})


if __name__ == "__main__":
    reset_all()
