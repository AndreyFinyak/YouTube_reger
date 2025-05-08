from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy
from selenium.common.exceptions import NoSuchElementException
import time
import random
import requests
import datetime
from db.crud import get_pending_accounts, update_account_status
from db.database import StatusEnum
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sms.sms_activate import acquire_phone
from sms.sms_activate import get_sms_code
from helpers.ui_utils import start_stylus_watcher

                # Словарь для сопоставления названий месяцев с их номерами
MONTHS = {
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December"
        }

def random_sleep(min_seconds=3, max_seconds=5):
    """Рандомное ожидание для имитации человеческого поведения."""
    sleep_time = random.uniform(min_seconds, max_seconds)
    print(f"⏳ Ожидание {sleep_time:.2f} секунд...")
    time.sleep(sleep_time)


def safe_click(driver, by, value, description=""):
    """Безопасное нажатие на элемент."""
    try:
        print(f"👉 Пытаемся нажать на: {description or value}")
        driver.find_element(by, value).click()
        random_sleep()
    except NoSuchElementException:
        print(f"❌ Элемент не найден: {description or value}")
    except Exception as e:
        print(f"⚠️ Ошибка при попытке нажать на элемент {description or value}: {e}")


def check_appium_server():
    """Проверка доступности Appium сервера."""
    try:
        response = requests.get("http://localhost:4723/status")
        if response.status_code == 200:
            print("✅ Appium сервер доступен.")
        else:
            print("⚠️ Appium сервер недоступен.")
    except Exception as e:
        print(f"❌ Ошибка подключения к Appium серверу: {e}")


def get_google_account_flow_driver():
    """Создание драйвера для работы с Google аккаунтами."""
    options = UiAutomator2Options().load_capabilities({
        "platformName": "Android",
        "deviceName": "emulator-5554",
        "automationName": "UiAutomator2",
        "appPackage": "com.android.settings",
        "appActivity": ".Settings",
        "noReset": True
    })

    try:
        driver = webdriver.Remote("http://localhost:4723", options=options)
        return driver
    except Exception as e:
        print(f"❌ Ошибка при создании драйвера: {e}")
        return None


def start_google_account_creation():
    """Запуск процесса регистрации Google аккаунтов."""
    check_appium_server()
    stop_event, watcher_thread = start_stylus_watcher(driver) # Запуск потока для отслеживания окна "Try out your stylus"

    # Получаем аккаунты из базы данных
    accounts = get_pending_accounts()
    if not accounts:
        print("❌ Нет аккаунтов для регистрации.")
        return

    for account in accounts:
        print(f"🔄 Начинаем регистрацию аккаунта: {account.username}")
        driver = get_google_account_flow_driver()
        if not driver:
            print("❌ Драйвер не создан. Пропускаем аккаунт.")
            update_account_status(account.id, StatusEnum.INACTIVE)
            return  # Завершаем выполнение скрипта

        try:
            # Переход в настройки Android
            print("👉 Переход в настройки Android...")
            safe_click(
                driver,
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiScrollable(new UiSelector()).scrollIntoView(text("Settings"))',
                "Вкладка 'Settings'"
            )
            safe_click(
                driver,
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiScrollable(new UiSelector()).scrollIntoView(new UiSelector().textContains("Password"))',
                "Элемент с подстрокой 'Password'"
            )

            # Нажатие на "Add account"
            safe_click(
                driver,
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("Add account")',
                "Кнопка 'Add account'"
            )

            # Нажатие на "Sign in"
            print("👉 Нажатие на 'Sign in'...")
            safe_click(
                driver,
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("Google")',
                "Кнопка 'Sign in'"
            )
            # Ожидание появления следующего окна
            try:
                print("⏳ Ожидание загрузки следующего окна...")
                create_account_button = WebDriverWait(driver, 30).until(
                    EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Create account")'))
                )
                random_sleep()
                print("✅ Кнопка 'Create account' найдена.")
            except Exception as e:
                print(f"❌ Ошибка при ожидании кнопки 'Create account': {e}")
                raise


            # Нажатие на "Create account"
            print("👉 Нажатие на 'Create account'...")
            safe_click(
                driver,
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("Create account")',
                "Кнопка 'Create account'"
            )

            # "For my personal use" — если есть
            if driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("For my personal use")'):
                print("👉 Нажатие на 'For my personal use'...")
                safe_click(
                    driver,
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().textContains("For my personal use")',
                    "Кнопка 'For my personal use'"
                )

            # Ввод First name
            print(f"👉 Ввод имени: {account.username}")
            try:
                input_fields = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
                )
                if len(input_fields) >= 1:
                    input_fields[0].send_keys(account.username)
                    random_sleep()
                else:
                    print("❌ Поле для ввода имени не найдено.")
                    raise Exception("Поле ввода имени не найдено.")
            except Exception as e:
                print(f"❌ Ошибка при вводе имени: {e}")
                raise

            # Нажатие на "Next"
            print("👉 Нажатие на 'Next'...")
            safe_click(
                driver,
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("Next")',
                "Кнопка 'Next'"
            )
                        # Генерация случайной даты рождения
            print("👉 Генерация случайной даты рождения...")
            current_year = datetime.datetime.now().year
            birth_year = random.randint(current_year - 30, current_year - 18)  # Случайный год от 18 до 30 лет назад
            birth_month = random.randint(1, 12)  # Случайный месяц
            birth_day = random.randint(1, 28)  # Случайный день

            birth_month_name = MONTHS[birth_month]  # Получение названия месяца из словаря
            print(f"👉 Дата рождения: {birth_day:02d}/{birth_month_name}/{birth_year}")
            try:
                # Ввод месяца
                print("👉 Ввод месяца...")
                month_field = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Mon")'))
                )
                month_field.click()  # Открытие выпадающего списка
                random_sleep()

                # Выбор месяца из выпадающего списка
                print(f"👉 Выбор месяца: {birth_month_name}")
                safe_click(
                    driver,
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    f'new UiSelector().textContains("{birth_month_name}")',  # Используем первые 3 буквы месяца
                    f"Месяц {birth_month_name}"
                )

                # Ввод дня
                print("👉 Ввод дня...")
                input_fields = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
                )
                input_fields[0].send_keys(str(birth_day))  # Ввод дня вручную
                random_sleep()

                # Ввод года
                print("👉 Ввод года...")
                input_fields[1].send_keys(str(birth_year))  # Ввод года вручную
                random_sleep()

                # Выбор пола (Gender)
                print("👉 Выбор пола: Female")

                # Ожидание появления элемента Gender
                gender_field = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().resourceId("gender")'))
                )
                gender_field.click()  # Открытие выпадающего списка
                random_sleep()

                # Выбор Female из выпадающего списка
                safe_click(
                    driver,
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().text("Female")',
                    "Пол Female"
                )
            except Exception as e:
                print(f"❌ Ошибка при вводе даты рождения или пола: {e}")
                raise

                        # Нажатие на "Next"
            print("👉 Нажатие на 'Next'...")
            safe_click(
                driver,
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("Next")',
                "Кнопка 'Next'"
            )

            # Ввод Email
            print("👉 Ввод Email...")
            try:
                # Проверяем наличие кнопки "Create your own Gmail address"
                create_gmail_button = driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Create your own Gmail address")')
                email_without_domain = account.email.split("@")[0]  # Извлекаем часть email до домена
                if create_gmail_button:
                    print("👉 Нажатие на 'Create your own Gmail address'...")
                    safe_click(
                        driver,
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().textContains("Create your own Gmail address")',
                        "Кнопка 'Create your own Gmail address'"
                    )
                    # Ввод email до домена
                    input_fields = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
                    )
                    print(f"👉 Ввод email без домена: {email_without_domain}")
                    input_fields[0].send_keys(email_without_domain)
                else:
                    # Если кнопки нет, вводим email до домена
                    input_fields = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
                    )
                    print(f"👉 Ввод email без домена: {email_without_domain}")
                    input_fields[0].send_keys(email_without_domain)

                random_sleep()

                # Нажатие на "Next"
                print("👉 Нажатие на 'Next'...")
                safe_click(
                    driver,
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().textContains("Next")',
                    "Кнопка 'Next'"
                )
                print("✅ Email успешно введён и подтверждён.")
            except Exception as e:
                print(f"❌ Ошибка при вводе email: {e}")
                raise

            # Ввод Password
            print("👉 Ввод Password...")
            input_fields = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
            )
            input_fields[0].send_keys(account.password)  # Ввод Password
            random_sleep()

            # Подтверждение Password если требуется
            if driver.find_elements(AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Confirm Password")'):
                print("👉 Нажатие на 'Confirm Password'...")
                safe_click(
                    driver,
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().textContains("Confirm Password")',
                    "Кнопка 'Confirm Password'"
                )
                print("👉 Подтверждение Password...")
                input_fields = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
                )
                input_fields[1].send_keys(account.password)  # Подтверждение Password
                random_sleep()

                        # Нажатие на "Next"
            print("👉 Нажатие на 'Next'...")
            safe_click(
                driver,
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("Next")',
                "Кнопка 'Next'"
            )

            # Ввод номера из sms-activate
            print("👉 Ввод номера из sms-activate...")
            max_attempts = 5  # Максимальное количество попыток
            attempt = 0
            recent_number = ""
            recent_id_number = ""
            while attempt < max_attempts:
                try:
                    print(f"🔄 Попытка {attempt + 1} из {max_attempts}...")
                    # Получение номера через sms-activate
                    recent_id_number, recent_number = acquire_phone(service="go", country=6)  # Первое — ID активации, второе — номер
                    if not recent_id_number or not recent_number:
                        raise Exception("Не удалось получить номер телефона.")

                    # Ожидание появления поля для ввода номера
                    input_fields = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
                    )

                    # Ввод номера
                    print(f"👉 Ввод номера: {recent_number}")
                    input_fields[0].send_keys(recent_number)
                    random_sleep()

                    # Нажатие на "Next"
                    print("👉 Нажатие на 'Next'...")
                    safe_click(
                        driver,
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().textContains("Next")',
                        "Кнопка 'Next'"
                    )

                    # Если номер успешно введён, выходим из цикла
                    print("✅ Номер успешно введён.")
                    break

                except Exception as e:
                    print(f"❌ Ошибка при вводе номера: {e}")
                    attempt += 1

                    # Отказ от текущего номера, если он был получен
                    if recent_id_number:
                        print("👉 Отказ от текущего номера...")
                        update_account_status(recent_id_number, StatusEnum.CANCELLED)  # Статус CANCELLED — отмена активации

                    # Если достигнуто максимальное количество попыток
                    if attempt == max_attempts:
                        print("❌ Превышено количество попыток. Возможно, проблема с прокси-сервером.")
                        raise Exception("Ошибка: Проблема с прокси-сервером. Проверьте настройки.")

            # Ввод SMS-кода
            print("👉 Ввод SMS-кода...")
            try:
                sms_code = get_sms_code(recent_id_number)
                if not sms_code:
                    print("❌ Не удалось получить SMS-код. Прерывание регистрации.")
                    raise Exception("Ошибка: SMS-код не получен.")

                sms_input_field = WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
                )
                print(f"👉 Ввод SMS-кода: {sms_code}")
                sms_input_field.send_keys(sms_code)
                random_sleep()

                print("👉 Нажатие на 'Next'...")
                safe_click(
                    driver,
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().textContains("Next")',
                    "Кнопка 'Next'"
                )
                print("✅ SMS-код успешно введён.")
            except Exception as e:
                print(f"❌ Ошибка при вводе SMS-кода: {e}")
                raise


            stop_event.set()
            watcher_thread.join() # Завершаем поток отслеживания окна "Try out your stylus"
        except Exception as e:
            print(f"❌ Ошибка при регистрации аккаунта {account.username}: {e}")
            update_account_status(account.id, StatusEnum.INACTIVE)
            stop_event.set()
            watcher_thread.join() # Завершаем поток отслеживания окна "Try out your stylus"
            return  # Завершаем выполнение скрипта при ошибке

        finally:
            driver.quit()