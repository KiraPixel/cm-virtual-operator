import os

from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Float, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class Transport(Base):
    __tablename__ = 'transport'
    id = Column(Integer, primary_key=True)
    storage_id = Column(Integer, ForeignKey('storage.ID'), nullable=False)
    model_id = Column(Integer, ForeignKey('transport_model.id'), nullable=False)
    uNumber = Column(Text)
    vin = Column(Text)
    x = Column(Float)
    y = Column(Float)
    alert_preset = Column(Integer)
    parser_1c = Column(Integer)

    def __repr__(self):
        return f'<Transport {self.uNumber}>'


class Storage(Base):
    __tablename__ = 'storage'

    ID = Column(Integer, primary_key=True)
    name = Column(String(100))
    type = Column(String(100))
    region = Column(String(100))
    address = Column(String(100))
    organization = Column(String(100))
    home_storage = Column(Integer)

    def __repr__(self):
        return '<Storage %r>' % self.name


class Alert(Base):
    __tablename__ = 'alert'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Integer, nullable=False, default=0)
    date_closed = Column(Integer, nullable=True)
    uNumber = Column(Text, nullable=False)
    type = Column(Text, nullable=False)
    data = Column(Text, nullable=False)
    status = Column(Integer, nullable=True, default=0)

    def __repr__(self):
        return f'<Alert {self.uNumber}, Type: {self.type}>'


class AlertTypePresets(Base):
    __tablename__ = 'alerts_type_presets'
    id = Column(Text(255), primary_key=True, autoincrement=True)
    preset_name =Column(Text, nullable=False)
    enable_alert_types = Column(Text)
    disable_alert_types = Column(Text)
    wialon_danger_distance = Column(Integer)
    wialon_danger_hours_not_work = Column(Integer)
    active = Column(Integer, nullable=False, default=1)
    editable = Column(Integer, nullable=False, default=1)


class CashCesar(Base):
    __tablename__ = 'cash_cesar'
    unit_id = Column(Integer, primary_key=True)
    object_name = Column(Text, nullable=False)
    pin = Column(Integer, default=0)
    vin = Column(Text, nullable=False)
    last_time = Column(Integer, default=0)
    pos_x = Column(Float, default=0.0)
    pos_y = Column(Float, default=0.0)
    created_at = Column(Integer, default=0)
    device_type = Column(Text, nullable=False)
    linked = Column(Boolean, nullable=True, default=False)

    __table_args__ = (
        Index('idx_cash_cesar_object_name', 'object_name'),
    )


class CashWialon(Base):
    __tablename__ = 'cash_wialon'
    id = Column(Integer, primary_key=True, index=True)
    uid = Column(Integer, nullable=False, default=0)
    nm = Column(Text, nullable=False)
    pos_x = Column(Float, default=0.0)
    pos_y = Column(Float, default=0.0)
    gps = Column(Integer, default=0)
    valid_nav = Column(Integer, default=1)
    last_time = Column(Integer, default=0)
    last_pos_time = Column(Integer, default=0)
    linked = Column(Boolean, nullable=True, default=False)  # TINYINT(1) NULL DEFAULT '0'
    cmd = Column(Text, nullable=True, default='')
    sens = Column(Text, nullable=True, default='')

    __table_args__ = (
        Index('idx_cash_wialon_nm', 'nm'),
    )


class IgnoredStorage(Base):
    __tablename__ = 'ignored_storage'
    id = Column(Integer, primary_key=True)
    named = Column(Text, nullable=False)
    pos_x = Column(Float, nullable=False)
    pos_y = Column(Float, nullable=False)
    radius = Column(Integer, nullable=False)


class SystemSettings(Base):
    __tablename__ = 'system_settings'
    id = Column(Integer, primary_key=True)
    enable_voperator = Column(Integer)
    enable_xml_parser = Column(Integer)
    enable_db_cashing = Column(Integer)


# Индекс для поля uNumber в Transport
Index('idx_transport_unumber', Transport.uNumber)


def get_engine():
    """Возвращает объект engine для базы данных"""
    return create_engine(os.getenv('SQLALCHEMY_DATABASE_URL', 'sqlite:///default.db'))


def create_db():
    """Создает базу данных и таблицы"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    return engine


def create_session(engine):
    """Создает и возвращает сессию"""
    Session = sessionmaker(bind=engine)
    return Session()
