
import os
from dotenv import load_dotenv
import random


# Загрузка переменных окружения из файла .env
load_dotenv()

# Получение списка прокси из .env
proxy_list = os.getenv('PROXY_LIST')  # Прокси в формате: "host1:port1,host2:port2,host3:port3"
if not proxy_list:
    raise Exception("❌ Список прокси (PROXY_LIST) не найден в .env.")

# Разбиваем список прокси на отдельные элементы
proxies = proxy_list.split()


def get_next_proxy():
    """
    Возвращает следующий прокси из списка.
    """
    proxies = proxy_list.split()
    proxy = random.choice(proxies)
    print(f"[DEBUG] Получен прокси: {proxy}")
    return proxy
