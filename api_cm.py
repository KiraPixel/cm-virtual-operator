import requests
import os

BASE_URL = os.getenv('CM_API_URL', '')
CM_API_KEY = os.getenv('CM_API_KEY', '')

HEALTH_URL = f"{BASE_URL}health"
ADD_CAR_URL = f"{BASE_URL}parser/add_new_car"

HEADERS = {
    'accept': 'application/json',
    'X-API-KEY': CM_API_KEY
}

response = requests.get(HEALTH_URL, headers=HEADERS)


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


def add_new_car(uNumber, model_id, storage_id, VIN, year, customer, manager, x=0, y=0, disable_virtual_operator=0):
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
        "disable_virtual_operator": disable_virtual_operator
    }

    try:
        response = requests.post(ADD_CAR_URL, json=payload, headers=HEADERS)
        if response.status_code == 200:
            return "ok"
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"