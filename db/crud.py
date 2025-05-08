from sqlalchemy.exc import SQLAlchemyError
from .database import SessionLocal, Account, StatusEnum


def get_all_accounts():
    '''Возвращает список всех аккаунтов'''

    session = SessionLocal()
    try:
        return session.query(Account).all()
    finally:
        session.close()


def get_pending_accounts():
    '''Возвращает список аккаунтов, ожидающих подтверждения'''

    session = SessionLocal()
    try:
        return session.query(Account).filter(Account.status == None).all()
    finally:
        session.close()


def add_account(username: str, email: str, password: str, recovery_email: str, recovery_password: str):
    '''Добавляет аккаунт в БД'''

    session = SessionLocal()
    try:
        new_acc = Account(
            username=username,
            email=email,
            password=password,
            recovery_email=recovery_email,
            recovery_password=recovery_password,
            status=None
        )
        session.add(new_acc)
        session.commit()
        print(f"[DB] Аккаунт {username} добавлен.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"[DB ERROR] {e}")
    finally:
        session.close()

def update_account_status(account_id: int, new_status: StatusEnum):
    '''Обновляет статус аккаунта (успешная регистрация или нет)'''

    session = SessionLocal()
    try:
        account = session.query(Account).filter_by(id=account_id).first()
        if account:
            account.status = new_status
            session.commit()
            print(f"[DB] Статус аккаунта {account.username} обновлён на {new_status.value}")
        else:
            print("[DB] Аккаунт не найден.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"[DB ERROR] {e}")
    finally:
        session.close()
