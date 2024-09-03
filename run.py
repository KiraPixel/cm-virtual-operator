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
    wialon = session.query(CashWialon).filter(CashWialon.nm.like(f"%{uNumber}%")).first()
    equipment_alert = search_alert(uNumber, 'no_equipment', 'Wialon')
    if not wialon:
        if not equipment_alert:
            create_alert(uNumber, 'no_equipment', 'Wialon')

        close_alert(uNumber, 'distance')
        close_alert(uNumber, 'gps')
        close_alert(uNumber, 'not_work')
        return

    close_alert(uNumber, 'no_equipment')
    # Сохранение данных wialon
    pos_x, pos_y, last_time = wialon.pos_x, wialon.pos_y, wialon.last_time
    wialon_cords = pos_y, pos_x

    # Чекаем есть ли алерты
    gps_alert = search_alert(uNumber, 'gps', 'Wialon')
    not_work_alert = search_alert(uNumber, 'not_work', 'Wialon')
    danger_alert = search_alert(uNumber, 'distance')

    # накидываем тригеры
    trigger_pos = False
    trigger_not_work = False
    #накидываем тригеры
    if pos_x == 0 or pos_y == 0:
        trigger_pos = True
    if time.time() - last_time > 48 * 3600:
        trigger_not_work = True

    # создаем или закрываем алерт по позиции
    if trigger_pos and not gps_alert:
        create_alert(uNumber, 'gps', 'Wialon')
    elif not trigger_pos and gps_alert:
        close_alert(uNumber, 'gps')

    # создаем или закрываем алерт по работе оборудования
    if trigger_not_work and not not_work_alert:
        create_alert(uNumber, 'not_work', 'Wialon')
    elif not trigger_not_work and not_work_alert:
        close_alert(uNumber, 'not_work')

    # закрываем алерт на дистанцию, если, что-то не работает
    if trigger_pos or trigger_not_work:
        close_alert(uNumber, 'distance')
        return

    # блок дистанции
    danger_distance = 5  # дистанция в км, которую мы считаем опасной
    if transport_cord is not None:
        distance = calculate_distance(transport_cord, wialon_cords)
        if distance >= danger_distance:
            if not danger_alert:
                create_alert(uNumber, 'distance', distance)
            else:
                alert_update(uNumber, 'distance', distance)  # Обновление дистанции в алерте
        else:
            close_alert(uNumber, 'distance')
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

