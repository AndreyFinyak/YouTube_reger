import time
import threading
from appium.webdriver.common.appiumby import AppiumBy

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
