import logging
import os
import time

import schedule

from app.processor import process_transports, check_status

# Расписание задач
schedule.every(5).minutes.do(process_transports)  # Выполнять process_transports() каждые 5 минут

int_level=logging.INFO
if os.getenv('DEV', '0') == '1':
    int_level = logging.DEBUG

logging.basicConfig(
    level=int_level,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('cm_virtual_operator')

if __name__ == "__main__":
    logger.info("Запуск планировщика задач...")
    logger.debug("ВНИМАНИЕ! ЗАПУСК В DEBUG РЕЖИМЕ!")
    while True:
        if check_status() == 0:
            logger.warning('Модуль отключен. Ожидание 100 секунд')
            time.sleep(100)
        else:
            process_transports()
            time.sleep(2)
