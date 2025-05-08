import requests
import os
from dotenv import load_dotenv
import time

load_dotenv()

# Загрузка API-ключа из переменных окружения
API_KEY = os.getenv("SMS_ACTIVATE_API_KEY")  # Убедитесь, что ключ API добавлен в .env файл

if not API_KEY:
    print("❌ API-ключ не найден. Убедитесь, что он указан в файле .env.")
    exit(1)

BASE_URL = "https://sms-activate.org/stubs/handler_api.php"

def get_phone_number(service="go", country=6):
    """
    Получение номера телефона через SMS-активацию.

    :param service: Код сервиса (например, 'go' для Google)
    :param country: Код страны (6 для Индонезии)
    :return: Кортеж (id активации, номер телефона) или None в случае ошибки
    """
    try:
        response = requests.get(
            BASE_URL,
            params={
                "api_key": API_KEY,
                "action": "getNumber",
                "service": service,
                "country": country
            }
        )
        if response.status_code == 200:
            result = response.text
            print(f"👉 Ответ от SMS-активации: {result}")

            if result.startswith("ACCESS_NUMBER"):
                parts = result.split(":")
                activation_id = parts[1]
                phone_number = parts[2]
                print(f"✅ Получен номер: {phone_number}, ID активации: {activation_id}")
                return activation_id, phone_number
            elif result.startswith("NO_NUMBERS"):
                print("❌ Нет доступных номеров.")
            elif result.startswith("NO_BALANCE"):
                print("❌ Недостаточно средств на балансе.")
            else:
                print(f"❌ Неизвестная ошибка: {result}")
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка при получении номера: {e}")
    return None

def set_status(activation_id, status):
    """
    Установка статуса активации.

    :param activation_id: ID активации
    :param status: Статус (1 - готов, 3 - отмена, 6 - завершено)
    :return: True, если статус успешно установлен, иначе False
    """
    try:
        response = requests.get(
            BASE_URL,
            params={
                "api_key": API_KEY,
                "action": "setStatus",
                "id": activation_id,
                "status": status
            }
        )
        if response.status_code == 200:
            result = response.text
            print(f"👉 Ответ на установку статуса: {result}")
            if result == "ACCESS_READY" or result == "ACCESS_CANCEL" or result == "ACCESS_ACTIVATION":
                print(f"✅ Статус успешно установлен: {status}")
                return True
            else:
                print(f"❌ Ошибка при установке статуса: {result}")
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка при установке статуса: {e}")
    return False

def acquire_phone(service="go", country=6):
    """
    Получает номер телефона и подтверждает его готовность к приёму SMS.

    :param service: Код сервиса (например, 'go' для Google)
    :param country: Код страны (например, 6 — Индонезия)
    :return: Кортеж (activation_id, phone_number) или None в случае ошибки
    """
    result = get_phone_number(service=service, country=country)
    if result:
        activation_id, phone_number = result
        success = set_status(activation_id, 1)  # Установка статуса "Готов"
        if success:
            return activation_id, phone_number
        else:
            print("⚠️ Не удалось установить статус. Отменяем активацию...")
            set_status(activation_id, 3)  # Отмена
    return None

def get_sms_code(activation_id, timeout=150):
    """
    Ожидание получения SMS-кода для активации.

    :param activation_id: ID активации, полученный при запросе номера
    :param timeout: Время ожидания в секундах (по умолчанию 2.5 минуты)
    :return: Код подтверждения или None, если код не был получен
    """
    print(f"👉 Ожидание SMS-кода для активации ID: {activation_id} (до {timeout} секунд)...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(
                BASE_URL,
                params={
                    "api_key": API_KEY,
                    "action": "getStatus",
                    "id": activation_id
                }
            )
            if response.status_code == 200:
                result = response.text
                print(f"👉 Ответ от SMS-активации: {result}")

                if result.startswith("STATUS_OK"):
                    # Код успешно получен
                    sms_code = result.split(":")[1]
                    print(f"✅ Получен SMS-код: {sms_code}")
                    return sms_code
                elif result == "STATUS_WAIT_CODE":
                    # Код ещё не получен, продолжаем ожидание
                    print("⏳ Ожидание SMS-кода...")
                elif result == "STATUS_CANCEL":
                    # Активация отменена
                    print("❌ Активация отменена.")
                    break
                elif result == "STATUS_ERROR":
                    # Ошибка активации
                    print("❌ Ошибка активации.")
                    break
            else:
                print(f"❌ Ошибка HTTP: {response.status_code}")
        except Exception as e:
            print(f"❌ Ошибка при запросе SMS-кода: {e}")

        # Ожидание перед следующим запросом
        time.sleep(5)

    # Если время ожидания истекло, отменяем активацию
    print("❌ Время ожидания истекло. Код не был получен.")
    print("👉 Отказ от номера...")
    set_status(activation_id, 3)  # Отмена активации
    return None