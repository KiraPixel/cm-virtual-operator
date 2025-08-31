
import time

import schedule

from app.processor import process_transports, check_status

# Расписание задач
schedule.every(5).minutes.do(process_transports)  # Выполнять process_transports() каждые 5 минут


if __name__ == "__main__":
    print("Запуск планировщика задач...")
    while True:
        if check_status() == 0:
            print('Модуль отключен. Ожидание 100 секунд')
            time.sleep(100)
        else:
            process_transports()
            time.sleep(2)
