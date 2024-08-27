import os
from sqlalchemy import create_engine, Column, Integer, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base

# Создаем базовый класс
Base = declarative_base()


class SystemStatus(Base):
    __tablename__ = 'system_status'

    id = Column(Integer, primary_key=True, autoincrement=True)  # Добавляем первичный ключ
    db_update = Column(Boolean, nullable=False, default=False)
    transport_update = Column(Boolean, nullable=False, default=False)
    tech_update = Column(Boolean, nullable=False, default=False)


# Получаем URL подключения из переменной окружения или используем SQLite по умолчанию
DATABASE_URL = os.getenv('SQLALCHEMY_DATABASE_URL', 'sqlite:///default.db')

# Создаем движок и сессию
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def get_status(name=None):
    """Получает статус обновления для db, transport или всех."""
    session = Session()
    try:
        status_record = session.query(SystemStatus).first()
        if not status_record:
            # Если записи нет, создаем её с дефолтными значениями
            status_record = SystemStatus()
            session.add(status_record)
            session.commit()

        if name == 'db':
            result = status_record.db_update or status_record.tech_update
        elif name == 'transport':
            result = status_record.transport_update or status_record.tech_update
        elif name is None:
            result = status_record.db_update or status_record.transport_update or status_record.tech_update
        else:
            return False

        return result
    finally:
        session.close()


def set_status(name, status):
    """Устанавливает статус обновления для db или transport."""
    if name not in ['db', 'transport']:
        return False

    session = Session()
    try:
        status_record = session.query(SystemStatus).first()
        if not status_record:
            status_record = SystemStatus()
            session.add(status_record)
            session.commit()

        if name == 'db':
            status_record.db_update = status
        elif name == 'transport':
            status_record.transport_update = status

        session.commit()
        return True
    except Exception as e:
        print(f"Error occurred: {e}")
        return False
    finally:
        session.close()