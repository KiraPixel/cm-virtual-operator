import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import requests
import os

BASE_URL = os.getenv('CM_API_URL', '')
CM_API_KEY = os.getenv('CM_API_KEY', '')
HEADERS = {
    'accept': 'application/json',
    'X-API-KEY': CM_API_KEY
}
response = requests.get(f"{BASE_URL}health", headers=HEADERS, verify=False)


def get_cm_health():
    try:
        if response.status_code == 200:
            data = response.json()
            # Проверяем статус всех модулей, кроме voperator_module
            return all(
                info.get('status') == 1
                for module, info in data.items()
                if module != "voperator_module"
            )
        return False
    except Exception as e:
        print(f"Ошибка при проверке статуса: {e}")
        return False


def add_new_car(uNumber, model_id, storage_id, VIN, year, customer, manager, x=0, y=0, parser_1c=0):
    payload = {
        "uNumber": uNumber,
        "model_id": model_id,
        "storage_id": storage_id,
        "VIN": VIN,
        "year": year,
        "customer": customer,
        "manager": manager,
        "x": x,
        "y": y,
        "parser_1c": parser_1c
    }

    try:
        response = requests.post(f"{BASE_URL}parser/add_new_car", json=payload, headers=HEADERS)
        if response.status_code == 200:
            return "ok"
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"