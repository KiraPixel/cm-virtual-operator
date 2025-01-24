import requests

# Отправляем GET-запрос
url = 'https://cm.lk-sp.ru/api/health'
response = requests.get(url, headers={'accept': 'application/json'})


def get_cm_health():
    # Проверяем, что запрос успешен
    if response.status_code == 200:
        data = response.json()

        # Проверяем все статусы
        all_status_ok = True
        for module, info in data.items():
            status = info.get('status')
            if status != 1:
                all_status_ok = False
                break
        return all_status_ok
    else:
        return False



