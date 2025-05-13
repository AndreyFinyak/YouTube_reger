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
from selenium.common.exceptions import StaleElementReferenceException
from sms.sms_activate import acquire_phone
from sms.sms_activate import get_sms_code
from helpers.ui_utils import start_stylus_watcher
from helpers.ui_utils import wipe_data_and_launch_emulator
from helpers.ui_utils import start_appium_server

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
def swipe_up(driver, duration=1000):
    """
    Выполняет умеренный свайп вверх: от чуть ниже центра до верха экрана.
    :param driver: Экземпляр драйвера Appium.
    :param duration: Длительность свайпа (по умолчанию 1000 мс).
    """
    window_size = driver.get_window_size()
    start_x = window_size['width'] // 2
    start_y = int(window_size['height'] * 0.65)
    end_y = int(window_size['height'] * 0.15)

    driver.swipe(start_x, start_y, start_x, end_y, duration)
    print("👉 Свайп вверх выполнен.")


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
        "noReset": True,
        "newCommandTimeout": 500
    })

    try:
        driver = webdriver.Remote("http://localhost:4723", options=options)
        return driver
    except Exception as e:
        print(f"❌ Ошибка при создании драйвера: {e}")
        return None


def start_google_account_creation():
    """Запуск процесса регистрации Google аккаунтов."""
    # Получаем аккаунты из базы данных
    start_appium_server()
    accounts = get_pending_accounts()
    if not accounts:
        print("❌ Нет аккаунтов для регистрации.")
        return

    for account in accounts:
        print(f"🔄 Начинаем регистрацию аккаунта: {account.username}")

        wipe_data_and_launch_emulator()  # Запуск эмулятора с очисткой данных

        driver = get_google_account_flow_driver()
        if not driver:
            print("❌ Драйвер не создан. Пропускаем аккаунт.")
            update_account_status(account.id, StatusEnum.INACTIVE)
            return  # Завершаем выполнение скрипта

        try:
            # Инициализация потока для отслеживания окна "Try out your stylus"
            stop_event, watcher_thread = start_stylus_watcher(driver)

            # Переход в настройки Android
            print("👉 Переход в настройки Android...")

            swipe_up(driver)


            random_sleep(1, 2)

            safe_click(
                driver,
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiScrollable(new UiSelector().scrollable(true)).setAsVerticalList().scrollIntoView(new UiSelector().text("Settings"))',
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
                create_account_button = WebDriverWait(driver, 200).until(
                    EC.presence_of_element_located((AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("Create account")'))
                )
                random_sleep()
                print("✅ Кнопка 'Create account' найдена.")
                random_sleep(5, 6)
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
            birth_month = random.randint(1, 7)  # Случайный месяц
            birth_day = random.randint(1, 28)  # Случайный день

            birth_month_name = MONTHS[birth_month]  # Получение названия месяца из словаря

            print(f"👉 Дата рождения: {birth_day:02d}/{birth_month_name}/{birth_year}")
            try:
                # Поиск всех спиннеров
                print("👉 Поиск всех спиннеров...")
                spinners = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.Spinner")
                print(f"🔍 Найдено {len(spinners)} спиннеров.")

                if len(spinners) >= 2:
                    # Выбор месяца
                    print("👉 Выбор месяца...")
                    month_spinner = spinners[0]  # Первый спиннер для месяца
                    month_spinner.click()
                    random_sleep()

                    print(f"👉 Выбор месяца: {birth_month_name}")
                    safe_click(
                        driver,
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        f'new UiScrollable(new UiSelector().scrollable(true)).scrollIntoView('
                        f'new UiSelector().text("{birth_month_name}"))',
                        "Месяц"
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

                    # Выбор пола
                    print("👉 Поиск спиннера для выбора пола...")
                    gender_spinner = spinners[1]  # Второй спиннер для пола
                    gender_spinner.click()
                    random_sleep()

                    print("👉 Выбор пола: Female")
                    safe_click(
                        driver,
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().text("Female")',
                        "Пол Female"
                    )

                else:
                    print("❌ Не найдено достаточно спиннеров для ввода даты и пола.")

            except Exception as e:
                print(f"❌ Ошибка при вводе даты рождения или пола: {e}")

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
                    random_sleep(1, 2)
                    # Если кнопки нет, вводим email до домена
                    input_fields = WebDriverWait(driver, 10).until(
                        EC.presence_of_all_elements_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
                    )
                    print(f"👉 Ввод email без домена: {email_without_domain}")
                    input_fields[0].send_keys(email_without_domain)

                random_sleep()

                # Нажатие на "Next"
                print("👉 Нажатие на 'Next'...")
                next_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().textContains("Next")'
                    ))
                )
                next_button.click()
                print("✅ Email успешно введён и подтверждён.")
            except Exception as e:
                print(f"❌ Ошибка при вводе email: {e}")
                raise
            random_sleep()
            # Ввод Password
            try:
                print("👉 Ввод Password...")
                for attempt in range(3):  # Попробовать до 3 раз
                    try:
                        input_fields = WebDriverWait(driver, 20).until(
                            EC.presence_of_all_elements_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
                        )
                        if len(input_fields) > 0:  # Проверяем, что поле найдено
                            print(f"✅ Поле для ввода пароля найдено. Попытка {attempt + 1}")
                            input_fields[0].clear()  # Очистка поля перед вводом
                            input_fields[0].send_keys(account.password)  # Ввод Password
                            random_sleep()
                            break  # Если успешно, выйти из цикла
                        else:
                            print("❌ Поле для ввода пароля не найдено.")
                            raise Exception("Поле для ввода пароля отсутствует.")
                    except StaleElementReferenceException:
                        print("⚠️ Элемент устарел. Повторяем попытку...")
                        time.sleep(1)  # Небольшая пауза перед повторной попыткой
                    except Exception as e:
                        print(f"❌ Ошибка при вводе пароля: {e}")
                        if attempt == 2:  # Если это последняя попытка
                            raise
            except Exception as e:
                print(f"❌ Ошибка при вводе Password: {e}")
                raise


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
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((
                    AppiumBy.ANDROID_UIAUTOMATOR,
                    'new UiSelector().textContains("Next")'
                ))
            )
            next_button.click()

                        # Ввод номера из sms-activate
            print("👉 Ввод номера из sms-activate...")
            max_attempts = 5  # Максимальное количество попыток
            attempt = 0
            recent_number = ""
            recent_id_number = ""

            while attempt < max_attempts:
                random_sleep(1, 2)
                try:
                    print(f"🔄 Попытка {attempt + 1} из {max_attempts}...")
                    # Получение номера через sms-activate
                    recent_id_number, recent_number = acquire_phone(service="go", country=6)  # Первое — ID активации, второе — номер
                    if not recent_id_number or not recent_number:
                        raise Exception("Не удалось получить номер телефона.")
                    print(f"👉 Получен номер: {recent_number} (ID: {recent_id_number})")
                    random_sleep(1, 2)
                    # Ввод номера
                    phone_field = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
                    )

                    phone_field.click()
                    phone_field.clear()
                    phone_field.send_keys(f'+{recent_number}')

                    print("✅ Номер телефона введён.")
                    random_sleep()

                    # Нажатие на "Next"
                    print("👉 Нажатие на 'Next'...")
                    safe_click(
                        driver,
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().textContains("Next")',
                        "Кнопка 'Next'"
                    )

                    # Проверка, перешло ли на следующую страницу
                    try:
                        code_input_fields = WebDriverWait(driver, 10).until(
                            EC.presence_of_all_elements_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
                        )

                        # Проверяем, есть ли среди них пустое поле
                        empty_code_fields = [field for field in code_input_fields if field.text.strip() == ""]

                        if empty_code_fields:
                            print("✅ Обнаружено пустое поле для ввода кода подтверждения. Переход завершён.")
                            break
                        else:
                            raise Exception("Поле найдено, но не пустое — возможно, это не нужная страница.")
                    except Exception:
                        print("❌ Номер не принят. Очищаем поле и пробуем снова.")
                        input_fields[0].clear()  # Очистка поля ввода номера
                        attempt += 1  # Увеличиваем счётчик попыток

                except Exception as e:
                    print(f"❌ Ошибка при вводе номера: {e}")
                    attempt += 1
                    if recent_id_number:
                        print("👉 Отказ от текущего номера...")
                        update_account_status(recent_id_number, StatusEnum.CANCELLED)  # Статус CANCELLED — отмена активации
                    if attempt >= max_attempts:
                        print("❌ Превышено количество попыток ввода номера.")
                        raise Exception("Ошибка: Не удалось ввести номер.")

            # Ожидание SMS-кода
            print("👉 Ожидание SMS-кода...")
            attempt = 0
            random_sleep(1, 2)
            while attempt < max_attempts:
                try:
                    sms_code = get_sms_code(recent_id_number)
                    if not sms_code:
                        print("❌ Не удалось получить SMS-код. Пробуем новый номер.")
                        # Отказ от текущего номера
                        if recent_id_number:
                            print("👉 Отказ от текущего номера...")
                            update_account_status(recent_id_number, StatusEnum.CANCELLED)  # Статус CANCELLED — отмена активации
                        attempt += 1
                        if attempt >= max_attempts:
                            print("❌ Превышено количество попыток получения SMS-кода.")
                            raise Exception("Ошибка: Не удалось получить SMS-код.")
                        continue

                    # Ввод SMS-кода
                    print(f"👉 Ввод SMS-кода: {sms_code}")
                    sms_input_field = WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((AppiumBy.CLASS_NAME, "android.widget.EditText"))
                    )
                    if sms_input_field:
                        sms_input_field.send_keys(sms_code)
                        random_sleep()
                    else:
                        print("❌ Поле для ввода SMS-кода не найдено.")
                        raise Exception("Поле для ввода SMS-кода отсутствует.")

                    print("👉 Нажатие на 'Next'...")
                    safe_click(
                        driver,
                        AppiumBy.ANDROID_UIAUTOMATOR,
                        'new UiSelector().textContains("Next")',
                        "Кнопка 'Next'"
                    )
                    print("✅ SMS-код успешно введён.")
                    break  # Выходим из цикла, если SMS-код успешно введён

                except Exception as e:
                    print(f"❌ Ошибка при обработке SMS-кода: {e}")
                    attempt += 1
                    if recent_id_number:
                        print("👉 Отказ от текущего номера...")
                        update_account_status(recent_id_number, StatusEnum.CANCELLED)  # Статус CANCELLED — отмена активации
                    if attempt >= max_attempts:
                        print("❌ Превышено количество попыток получения SMS-кода.")
                        raise Exception("Ошибка: Превышено количество попыток получения SMS-кода.")


                        # Нажатие на "Next"
            print("👉 Нажатие на 'Next'...")
            safe_click(
                driver,
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiSelector().textContains("Next")',
                "Кнопка 'Next'"
            )

            safe_click(
                driver,
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiScrollable(new UiSelector()).scrollIntoView(new UiSelector().textContains("I agree"))',
                "Элемент с подстрокой 'I agree'"
            )

            buttons = driver.find_elements(AppiumBy.CLASS_NAME, "android.widget.Button")
            for button in buttons:
                if button.text.strip().lower() == "confirm":
                    print("👉 Найдена кнопка Confirm, пробуем нажать...")
                    button.click()
                    break
            else:
                print("❌ Кнопка Confirm не найдена среди кнопок.")

            random_sleep(4,5)

            driver.press_keycode(3) # Переход пр кнопке HOME
            print("👉 Переход на главный экран...")

            print("👉 Переход в Google...")
            safe_click(
                driver,
                AppiumBy.ANDROID_UIAUTOMATOR,
                'new UiScrollable(new UiSelector()).scrollIntoView(text("Google"))',
                "Вкладка 'Google'"
            )

            print(f"✅ Успешная регистрация аккаунта: {account.username}")
            update_account_status(account.id, StatusEnum.ACTIVE)

            time.sleep(1000)  # Ожидание перед завершением сессии

        except Exception as e:
            print(f"❌ Ошибка при регистрации аккаунта {account.username}: {e}")
            random_sleep(1000, 2000)

        finally:
            # Завершаем поток отслеживания окна "Try out your stylus"
            if 'stop_event' in locals() and 'watcher_thread' in locals():
                stop_event.set()
                watcher_thread.join()

            # Закрываем драйвер только если он существует
            if driver:
                try:
                    print("👉 Завершаем сессию Appium...")
                    driver.quit()
                except Exception as e:
                    print(f"⚠️ Ошибка при завершении сессии драйвера: {e}")

    print("✅ Регистрация аккаунтов завершена.")