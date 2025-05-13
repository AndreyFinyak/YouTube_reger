import time
import random
import threading
import os
import string
from appium.webdriver.common.appiumby import AppiumBy
import subprocess
from proxy_config.proxy_conf import get_next_proxy


def start_stylus_watcher(driver):
    """
    Запускает фоновый поток, который проверяет появление окна
    'Try out your stylus' и нажимает 'Cancel', если оно появилось.
    """
    stop_event = threading.Event()

    def stylus_watcher():
        while not stop_event.is_set():
            try:
                cancel_button = driver.find_element(
                    AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Cancel")'
                )
                cancel_button.click()
                print("🖊️ Окно 'Try out your stylus' обнаружено и закрыто.")
                stop_event.set()
            except:
                time.sleep(2)

    thread = threading.Thread(target=stylus_watcher)
    thread.daemon = True
    thread.start()
    return stop_event, thread

def list_avds():
    """Получает список доступных AVD."""
    result = subprocess.run(["emulator", "-list-avds"], capture_output=True, text=True)
    avds = result.stdout.strip().split("\n")
    return avds

def random_hex(length=16):
    return ''.join(random.choices('0123456789abcdef', k=length))

def generate_android_properties():
    """Генерирует случайные значения для антидетекта"""
    return {
        "android_id": random_hex(16),
        "gsf_id": str(random.randint(10**18, 10**19 - 1)),
        "serial": ''.join(random.choices(string.ascii_uppercase + string.digits, k=12)),
    }

def generate_random_fingerprint():
    '''
    Генерирует случайный fingerprint для Android устройства.
    '''
    brands = ["google", "samsung", "xiaomi", "huawei"]
    models = ["pixel_4", "galaxy_s21", "mi_11", "p40_pro"]
    versions = ["10", "11", "12"]

    brand = random.choice(brands)
    model = random.choice(models)
    version = random.choice(versions)

    fingerprint = f"{brand}/{model}/{model}:{version}/QS1A.200205.001/{random.randint(1000000, 9999999)}:user/release-keys"
    return fingerprint


def patch_avd_config(avd_name: str, fingerprint: str):
    avd_path = os.path.expanduser(f"~/.android/avd/{avd_name}.avd/config.ini")
    if not os.path.exists(avd_path):
        print(f"[ERROR] config.ini не найден по пути {avd_path}")
        return
    with open(avd_path, "a") as f:
        f.write(f"\nhw.build.fingerprint={fingerprint}\n")
    print(f"[INFO] Пропатчен hw.build.fingerprint в config.ini: {fingerprint}")

def wipe_data_and_launch_emulator(avd_name='Pixel_7_Pro', boot_wait: int = 55):
    """
    Выполняет Wipe Data и перезапускает эмулятор с указанным именем AVD, используя Privoxy.

    :param avd_name: Название виртуального устройства (AVD)
    :param boot_wait: Секунды ожидания после запуска (по умолчанию 60)
    """

    print(f"[INFO] Выполняем Wipe Data для AVD: {avd_name}...")

    # Проверяем, доступен ли AVD
    avds = list_avds()
    if avd_name not in avds:
        print(f"[ERROR] Устройство {avd_name} не найдено. Доступные устройства: {', '.join(avds)}")
        return

    try:
        # Завершаем все запущенные эмуляторы
        subprocess.run(["adb", "emu", "kill"], check=False)
        time.sleep(5)
        patch_avd_config(avd_name, generate_random_fingerprint())
        host, port, login, password = get_next_proxy().split(":")
        proxy = f'http://{login}:{password}@{host}:{port}'
        # Генерация антидетект данных
        props = generate_android_properties()
        # Запускаем эмулятор с параметром -http-proxy
        process = subprocess.Popen([
            "/Users/karavan/Library/Android/sdk/emulator/emulator",
            "-avd", avd_name,
            "-wipe-data",
            "-no-snapshot-save",
            "-http-proxy", proxy,
            "-prop", f"persist.sys.android_id={props['android_id']}",
            "-prop", f"ro.serialno={props['serial']}",
            "-prop", f"ro.com.google.gsf.id={props['gsf_id']}",
            "-prop", f"ro.build.fingerprint={generate_random_fingerprint()}",
        ])
        # print(f"[INFO] Эмулятор {avd_name} запущен с прокси {proxy_url}. Ожидание {boot_wait} секунд...")
        time.sleep(boot_wait)
        print(f"[SUCCESS] Эмулятор {avd_name} готов к работе.")
    except Exception as e:
        print(f"[ERROR] Не удалось выполнить Wipe Data или запустить эмулятор: {e}")

def close_emulator():
    """
    Закрывает запущенный эмулятор.
    """
    try:
        print("[INFO] Закрываем запущенный эмулятор...")
        result = subprocess.run(["adb", "emu", "kill"], capture_output=True, text=True)
        if result.returncode == 0:
            print("[SUCCESS] Эмулятор успешно закрыт.")
        else:
            print(f"[ERROR] Не удалось закрыть эмулятор. Ошибка: {result.stderr.strip()}")
    except Exception as e:
        print(f"[ERROR] Произошла ошибка при попытке закрыть эмулятор: {e}")


def start_appium_server():
    """
    Запускает Appium сервер.
    """
    try:
        print("👉 Запуск Appium сервера...")
        process = subprocess.Popen(["appium"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(5)  # Даем серверу время для запуска
        print("✅ Appium сервер запущен.")
        return process
    except Exception as e:
        print(f"❌ Ошибка при запуске Appium сервера: {e}")
        return None

