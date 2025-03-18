import sys
import time

import schedule

from api_cm import get_cm_health
from models import create_session, get_engine, Transport, Alert, CashWialon, IgnoredStorage
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


def close_invalid_alerts():
    """Закрывает алерты, если uNumber не существует в таблице Transport."""
    # Получаем все уникальные uNumber из таблицы Alert, где статус 0 (алерт открыт)
    open_alerts = session.query(Alert.uNumber).filter_by(status=0).distinct().all()
    open_alerts_numbers = [alert.uNumber for alert in open_alerts]

    # Получаем все существующие uNumber из таблицы Transport
    existing_transports = session.query(Transport.uNumber).distinct().all()
    existing_transport_numbers = [transport.uNumber for transport in existing_transports]

    # Проверяем, какие uNumber отсутствуют в таблице Transport
    invalid_uNumbers = set(open_alerts_numbers) - set(existing_transport_numbers)

    if invalid_uNumbers:
        # Закрываем алерты для отсутствующих uNumber
        for uNumber in invalid_uNumbers:
            alerts_to_close = session.query(Alert).filter_by(uNumber=uNumber, status=0).all()
            for alert in alerts_to_close:
                alert.status = 1
            session.commit()
        print(f"Закрыто {len(invalid_uNumbers)} алертов для несуществующих uNumber.")
    else:
        print("Нет алертов для закрытия для несуществующих uNumber..")


def trigger_handler(uNumber, trigger_closeAll=False,
                    trigger_distance=False, trigger_distance_value=None,
                    trigger_gps=False, trigger_gps_value=None,
                    trigger_no_equipment=False, trigger_no_equipment_value=None,
                    trigger_no_docs_cords=False,
                    trigger_not_work=False, trigger_not_work_value=None):

    # хоть и есть приемники value для триггеров trigger_distance, trigger_no_equipment, trigger_not_work
    # логика готова только для виалона
    # в ином случае будет жопа :) sry

    if trigger_closeAll:
        close_alert(uNumber, 'distance')
        close_alert(uNumber, 'gps')
        close_alert(uNumber, 'no_equipment')
        close_alert(uNumber, 'no_docs_cords')
        close_alert(uNumber, 'not_work')
        return

    # поправляем триггеры
    if trigger_no_equipment:
        trigger_distance = False
        trigger_gps = False
        trigger_not_work = False

    if trigger_not_work:
        trigger_distance = False
        trigger_gps = False

    if trigger_gps:
        trigger_distance = False

    if trigger_no_docs_cords:
        trigger_distance = False

    # исполняем триггеры
    if trigger_distance:
        if not search_alert(uNumber, 'distance'):
            if trigger_distance_value:
                create_alert(uNumber, 'distance', trigger_distance_value)
        else:
            if trigger_distance_value:
                alert_update(uNumber, 'distance', trigger_distance_value)
    else:
        close_alert(uNumber, 'distance')

    if trigger_gps:
        if not search_alert(uNumber, 'gps'):
            if trigger_gps_value:
                create_alert(uNumber, 'gps', trigger_gps_value)
    else:
        close_alert(uNumber, 'gps')

    if trigger_not_work:
        if not search_alert(uNumber, 'not_work'):
            if trigger_not_work_value:
                create_alert(uNumber, 'not_work', trigger_not_work_value)
    else:
        close_alert(uNumber, 'not_work')

    if trigger_no_equipment:
        if not search_alert(uNumber, 'no_equipment'):
            if trigger_no_equipment:
                create_alert(uNumber, 'no_equipment', trigger_no_equipment_value)
    else:
        close_alert(uNumber, 'no_equipment')

    if trigger_no_docs_cords:
        if not search_alert(uNumber, 'no_docs_cords'):
            if trigger_no_docs_cords:
                create_alert(uNumber, 'no_docs_cords', 'no_docs_cords')
    else:
        close_alert(uNumber, 'no_docs_cords')



def process_wialon(uNumber, transport_cord, disable_virtual_operator, in_parser_1c, ignored_storages):
    """отрабатываем часть wialon"""

    trigger_closeAll = False
    trigger_distance = False
    trigger_distance_value = None
    trigger_no_docs_cords = False
    trigger_gps = False
    trigger_gps_value = None
    trigger_no_equipment = False
    trigger_no_equipment_value = None
    trigger_not_work = False
    trigger_not_work_value = None

    in_ignored_storage = False

    while get_db_status('db') == 1:
        time.sleep(1)

    wialon = session.query(CashWialon).filter(CashWialon.nm.like(f"%{uNumber}%")).first()
    if wialon is not None:
        wialon_cords = wialon.pos_y, wialon.pos_x
    else:
        wialon_cords = None
    danger_distance = 5  # дистанция в км, которую мы считаем опасной

    if disable_virtual_operator == 1:
        trigger_closeAll = True

    if not wialon:
        trigger_no_equipment = True
        trigger_no_equipment_value = 'Wialon'
    else:

        if time.time() - wialon.last_time > 72 * 3600 or wialon.last_time == 0:
                trigger_not_work = True
                trigger_not_work_value = 'Wialon'

        if wialon.pos_y == 0 or wialon.pos_x == 0:
            trigger_gps = True
            trigger_gps_value = 'Wialon'
        else:
            for storage in ignored_storages:
                storage_cords = (storage.pos_x, storage.pos_y)
                distance_to_storage = calculate_distance(storage_cords, wialon_cords)
                if distance_to_storage <= storage.radius:
                    in_ignored_storage = True

        if transport_cord is None:
            if in_parser_1c:
                trigger_no_docs_cords = True

        if transport_cord is not None and wialon_cords is not None:
            distance = calculate_distance(transport_cord, wialon_cords)
            if distance > danger_distance:
                trigger_distance = True
                trigger_distance_value = distance

    if in_ignored_storage:
        trigger_distance=False
        trigger_no_docs_cords=False

    trigger_handler(uNumber,
                    trigger_closeAll=trigger_closeAll,
                    trigger_no_equipment=trigger_no_equipment, trigger_no_equipment_value=trigger_no_equipment_value,
                    trigger_not_work=trigger_not_work, trigger_not_work_value=trigger_not_work_value,
                    trigger_gps=trigger_gps, trigger_gps_value=trigger_gps_value,
                    trigger_no_docs_cords=trigger_no_docs_cords,
                    trigger_distance=trigger_distance, trigger_distance_value=trigger_distance_value)




def process_transports():
    """Основная функция для обработки данных транспортных средств"""

    if not get_cm_health():
        print("Приложите подорожник к ЦМ")
        print("Фрижу задачу на час")
        time.sleep(600)
        return

    # Получаем все транспортные средства
    transports = session.query(Transport).all()
    ignored_storages = session.query(IgnoredStorage).all()

    print("Начало обработки:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    start_time = time.time()
    if get_db_status('db') != 1:
        close_invalid_alerts()

    for transport in transports:
        while get_db_status('db') == 1:
            time.sleep(1)
        uNumber = transport.uNumber
        disable_virtual_operator = transport.disable_virtual_operator
        in_parser_1c = transport.parser_1c
        transport_cord = None

        if transport.x != 0 and transport.y != 0:
            transport_cord = transport.x, transport.y  # переворачиваем корды, ибо это баг виалона
        if transport.x is None or transport.y is None:
            transport_cord = None, None

        process_wialon(uNumber, transport_cord, disable_virtual_operator, in_parser_1c, ignored_storages)

    end_time = time.time()
    print("\nОбработка завершена:", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    print(f"Время обработки: {end_time - start_time:.2f} секунд")


# Расписание задач
schedule.every(5).minutes.do(process_transports)  # Выполнять process_transports() каждые 5 минут

if __name__ == "__main__":
    print("Начинаю работу и запускаю первый прогон")
    process_transports()
    print("Запуск планировщика задач...")
    while True:
        schedule.run_pending()
        time.sleep(1)  # Задержка, чтобы не перегружать процессор

