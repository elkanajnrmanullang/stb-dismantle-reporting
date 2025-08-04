from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

def generate_tanggal_columns(prefix='t', jumlah_col=False):
    return {
        f"{'jumlah_' if jumlah_col else ''}{prefix}{i}": Column(Integer, default=0)
        for i in range(1, 32)
    }

def generate_jumlah_fields(fields):
    return {
        f"jumlah_{field}": Column(Integer, default=0)
        for field in fields
    }

class ProgressDismantle(Base):
    __tablename__ = 'progress_dismantle'

    id = Column(Integer, primary_key=True)
    teknisi = Column(Integer, default=0)
    service_area = Column(String, nullable=False)
    sto = Column(String, nullable=False)
    berhasil_bulan_lalu = Column(Integer, default=0)
    kendala_bulan_lalu = Column(Integer, default=0)
    saldo_awal = Column(Integer, default=0)
    progress = Column(Integer, default=0)
    berhasil = Column(Integer, default=0)
    kendala = Column(Integer, default=0)
    saldo_akhir = Column(Integer, default=0)
    waktu_update = Column(DateTime, default=datetime.utcnow)
    is_total_row = Column(Boolean, default=False)
    is_total_col = Column(Boolean, default=False)

    locals().update(generate_tanggal_columns())
    locals().update(generate_tanggal_columns('t', jumlah_col=True))
    locals().update(generate_jumlah_fields([
        'teknisi', 'berhasil_bulan_lalu', 'kendala_bulan_lalu',
        'saldo_awal', 'progress', 'berhasil', 'kendala', 'saldo_akhir'
    ]))

class KendalaDismantle(Base):
    __tablename__ = 'kendala_dismantle'

    id = Column(Integer, primary_key=True)
    teknisi = Column(Integer, default=0)
    service_area = Column(String, nullable=False)
    sto = Column(String, nullable=False)
    berhasil_bulan_lalu = Column(Integer, default=0)
    kendala_bulan_lalu = Column(Integer, default=0)
    saldo_awal = Column(Integer, default=0)
    progress = Column(Integer, default=0)
    berhasil = Column(Integer, default=0)
    kendala = Column(Integer, default=0)
    saldo_akhir = Column(Integer, default=0)
    waktu_update = Column(DateTime, default=datetime.utcnow)
    is_total_row = Column(Boolean, default=False)
    is_total_col = Column(Boolean, default=False)

    locals().update(generate_tanggal_columns())
    locals().update(generate_tanggal_columns('t', jumlah_col=True))
    locals().update(generate_jumlah_fields([
        'teknisi', 'berhasil_bulan_lalu', 'kendala_bulan_lalu',
        'saldo_awal', 'progress', 'berhasil', 'kendala', 'saldo_akhir'
    ]))

class STBProgress(Base):
    __tablename__ = 'stb_progress'

    id = Column(Integer, primary_key=True)
    teknisi = Column(Integer, default=0)
    service_area = Column(String, nullable=False)
    sto = Column(String, nullable=False)
    saldo_awal = Column(Integer, default=0)
    assign = Column(Integer, default=0)
    progress = Column(Integer, default=0)
    berhasil = Column(Integer, default=0)
    kendala = Column(Integer, default=0)
    saldo_akhir = Column(Integer, default=0)
    waktu_update = Column(DateTime, default=datetime.utcnow)
    is_total_row = Column(Boolean, default=False)
    is_total_col = Column(Boolean, default=False)

    locals().update(generate_tanggal_columns())
    locals().update(generate_tanggal_columns('t', jumlah_col=True))
    locals().update(generate_jumlah_fields([
        'teknisi', 'saldo_awal', 'assign',
        'progress', 'berhasil', 'kendala', 'saldo_akhir'
    ]))

class KendalaSTB(Base):
    __tablename__ = 'kendala_stb'

    id = Column(Integer, primary_key=True)
    teknisi = Column(Integer, default=0)
    service_area = Column(String, nullable=False)
    sto = Column(String, nullable=False)
    saldo_awal = Column(Integer, default=0)
    progress = Column(Integer, default=0)
    berhasil = Column(Integer, default=0)
    kendala = Column(Integer, default=0)
    saldo_akhir = Column(Integer, default=0)
    waktu_update = Column(DateTime, default=datetime.utcnow)
    is_total_row = Column(Boolean, default=False)
    is_total_col = Column(Boolean, default=False)

    locals().update(generate_tanggal_columns())
    locals().update(generate_tanggal_columns('t', jumlah_col=True))
    locals().update(generate_jumlah_fields([
        'teknisi', 'saldo_awal', 'progress',
        'berhasil', 'kendala', 'saldo_akhir'
    ]))
# ================================
# VISIT TABLES
# ================================
class VisitDismantle(Base):
    __tablename__ = 'visit_dismantle'

    id = Column(Integer, primary_key=True)
    service_area = Column(String, nullable=False)
    
    # Nilai data per-area
    visit = Column(Integer, default=0)
    dismantle = Column(Integer, default=0)
    kendala = Column(Integer, default=0)
    sisa_assign = Column(Integer, default=0)

    jumlah_visit = Column(Integer, default=0)
    jumlah_dismantle = Column(Integer, default=0)
    jumlah_kendala = Column(Integer, default=0)
    jumlah_sisa_assign = Column(Integer, default=0)

    is_total = Column(Boolean, default=False)
    waktu_update = Column(DateTime, default=datetime.utcnow)


class VisitSTB(Base):
    __tablename__ = 'visit_stb'

    id = Column(Integer, primary_key=True)
    service_area = Column(String, nullable=False)
    
    visit = Column(Integer, default=0)
    dismantle = Column(Integer, default=0)
    kendala = Column(Integer, default=0)
    sisa_assign = Column(Integer, default=0)

    jumlah_visit = Column(Integer, default=0)
    jumlah_dismantle = Column(Integer, default=0)
    jumlah_kendala = Column(Integer, default=0)
    jumlah_sisa_assign = Column(Integer, default=0)

    is_total = Column(Boolean, default=False)
    waktu_update = Column(DateTime, default=datetime.utcnow)