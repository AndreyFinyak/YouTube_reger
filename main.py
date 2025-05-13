import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QFileDialog, QVBoxLayout, QMessageBox
)
from db.crud import add_account
from registration import start_google_account_creation  # Импорт функции регистрации


class AccountLoader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Reger")
        self.setGeometry(100, 100, 400, 300)

        self.layout = QVBoxLayout()

        self.label = QLabel("Файл не выбран")
        self.layout.addWidget(self.label)

        self.btn_browse = QPushButton("Выбрать файл")
        self.btn_browse.clicked.connect(self.browse_file)
        self.layout.addWidget(self.btn_browse)

        self.btn_start = QPushButton("Запустить добавление аккаунтов в БД")
        self.btn_start.clicked.connect(self.start_add_accaounts)
        self.layout.addWidget(self.btn_start)

        # Кнопка для регистрации аккаунта
        self.btn_register = QPushButton("Зарегистрировать аккаунт")
        self.btn_register.clicked.connect(self.register_account)
        self.layout.addWidget(self.btn_register)

        self.setLayout(self.layout)

        self.file_path = ""

    def browse_file(self):
        '''Подается txt файл с данными аккаунтов'''
        path, _ = QFileDialog.getOpenFileName(self, "Выбери файл", "", "Text Files (*.txt)")
        if path:
            self.file_path = path
            self.label.setText(f"Выбран: {path}")

    def read_file(self):
        """Чтение файла и возврат списка аккаунтов"""
        accounts = []
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                for line in file:
                    # Ожидается формат: username:email:password:recovery_email:recovery_password
                    parts = line.strip().split(":")
                    if len(parts) == 5:
                        accounts.append({
                            "username": parts[0],
                            "email": parts[1],
                            "password": parts[2],
                            "recovery_email": parts[3],
                            "recovery_password": parts[4],
                        })
                    else:
                        QMessageBox.warning(self, "Ошибка", f"Неверный формат строки: {line}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать файл: {e}")
        return accounts

    def start_add_accaounts(self):
        '''Добавление аккаунта в БД'''
        if not self.file_path:
            QMessageBox.warning(self, "Ошибка", "Сначала выбери файл.")
            return

        accounts = self.read_file()
        if not accounts:
            QMessageBox.warning(self, "Ошибка", "Файл пустой или содержит ошибки.")
            return

        # Добавление аккаунтов в базу данных
        for account in accounts:
            try:
                add_account(
                    username=account["username"],
                    email=account["email"],
                    password=account["password"],
                    recovery_email=account["recovery_email"],
                    recovery_password=account["recovery_password"]
                )
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось добавить аккаунт {account['username']}: {e}")

        QMessageBox.information(self, "Успех", f"Добавлено {len(accounts)} аккаунтов в базу данных.")

    def register_account(self):
        '''Запуск регистрации аккаунта через Appium'''
        try:
            start_google_account_creation()
            QMessageBox.information(self, "Успех", "Регистрация аккаунта завершена.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка при регистрации аккаунта: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AccountLoader()
    window.show()
    sys.exit(app.exec_())