import sys
import time

import schedule
from models import create_session, get_engine, Transport, Alert, CashWialon
from location_module import calculate_distance
from system_status_manager import get_status as get_db_status


# Создаем engine и сессию
engine = get_engine()
session = create_session(engine)


def create_alert(uNumber, type, data):
    """Создает новый алерт"""
    new_alert = Alert(
        date=int(time.time()),  # текущая дата в формате UNIX
        uNumber=uNumber,
        type=type,
        data=data
    )
    session.add(new_alert)
    session.commit()


def alert_update(uNumber, type, data):
    """Обновляет data у существующего алерта"""
    alert = session.query(Alert).filter_by(uNumber=uNumber, type=type, status=0).first()
    if alert:
        alert.data = data
        session.commit()


def close_alert(uNumber, type):
    """Закрывает алерт, изменяя его статус на 1"""
    alert = session.query(Alert).filter_by(uNumber=uNumber, type=type, status=0).first()
    if alert:
        alert.status = 1
        session.commit()


def search_alert(uNumber, type, data=None):
    """Ищет алерт по uNumber, type и data"""
    query = session.query(Alert).filter_by(uNumber=uNumber, type=type, status=0)
    if data:
        query = query.filter(Alert.data.like(f"%{data}%"))
    return query.first()


def process_wialon(uNumber, transport_cord):
    """отрабатываем часть wialon"""

    while get_db_status('db') == 1:
        time.sleep(1)

    wialon = session.query(CashWialon).filter(CashWialon.nm.like(f"%{uNumber}%")).first()

    if not wialon:
        close_alert(uNumber, 'distance')
        close_alert(uNumber, 'gps')
        if not search_alert(uNumber, 'no_equipment'):
            create_alert(uNumber, 'no_equipment', 'Wialon')
        return

    close_alert(uNumber, 'no_equipment')

    if time.time() - wialon.last_time > 48 * 3600 or wialon.last_time == 0:
        close_alert(uNumber, 'distance')
        close_alert(uNumber, 'gps')
        if not search_alert(uNumber,"not_work"):
            create_alert(uNumber, 'not_work', 'Wialon')
        return
    else:
        close_alert(uNumber, 'not_work')

    if wialon.pos_y == 0 or wialon.pos_x == 0:
        close_alert(uNumber, 'distance')
        if not search_alert(uNumber,"gps"):
            create_alert(uNumber, 'gps', 'Wialon')
        return
    else:
        close_alert(uNumber, 'gps')


    # блок дистанции
    if transport_cord is None:
        close_alert(uNumber, 'distance')
        return

    danger_distance = 5  # дистанция в км, которую мы считаем опасной
    wialon_cords = wialon.pos_y, wialon.pos_x
    distance = calculate_distance(transport_cord, wialon_cords)
    if distance >= danger_distance:
        if not search_alert(uNumber, 'distance'):
            create_alert(uNumber, 'distance', distance)
        else:
            alert_update(uNumber, 'distance', distance)  # Обновление дистанции в алерте
    else:
        close_alert(uNumber, 'distance')


def process_transports():
    """Основная функция для обработки данных транспортных средств"""
    # Получаем все транспортные средства
    transports = session.query(Transport).all()

    print("Начало обработки:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    start_time = time.time()

    for transport in transports:
        while get_db_status('db') == 1:
            time.sleep(1)
        uNumber = transport.uNumber
        transport_cord = None

        if transport.x != 0 and transport.y != 0:
            transport_cord = transport.x, transport.y  # переворачиваем корды, ибо это баг виалона

        process_wialon(uNumber, transport_cord)

    end_time = time.time()
    print("\nОбработка завершена:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    print(f"Время обработки: {end_time - start_time:.2f} секунд")


# Расписание задач
schedule.every(5).minutes.do(process_transports)  # Выполнять process_transports() каждые 5 минут

if __name__ == "__main__":
    process_transports()
    print("Запуск планировщика задач...")
    while True:
        schedule.run_pending()
        time.sleep(1)  # Задержка, чтобы не перегружать процессор

