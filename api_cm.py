import requests
import os

url = os.getenv('CM_INSIDE_HEALTH_URL', 'https://cm.lk-sp.ru/api/health')


# Делаем запрос с отключенной проверкой SSL
response = requests.get(url, headers={'accept': 'application/json'})

def get_cm_health():
    if response.status_code == 200:
        data = response.json()
        all_status_ok = True
        for module, info in data.items():
            if module == "voperator_module":  # Игнорируем сами себя
                continue
            status = info.get('status')
            if status != 1:
                all_status_ok = False
                break
        return all_status_ok
    else:
        print(f"Ошибка запроса: {response.status_code}")
        return False

# Пример использования
result = get_cm_health()
print("Все модули в порядке:", result)