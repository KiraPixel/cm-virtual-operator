import requests

url = 'http://192.168.201.140:5000/api/health'

# Делаем запрос с отключенной проверкой SSL
response = requests.get(url, headers={'accept': 'application/json'})

def get_cm_health():
    if response.status_code == 200:
        data = response.json()
        all_status_ok = True
        for module, info in data.items():
            status = info.get('status')
            print(f"Статус {module}: {status}")
            if status != 1:
                all_status_ok = False
                break
        return all_status_ok
    else:
        print(f"Ошибка запроса: {response.status_code}")
        return False