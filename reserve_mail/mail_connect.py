import imaplib
from db.database import SessionLocal, Account

IMAP_SERVERS = {
    'gmail.com': 'imap.gmail.com',
    'yandex.ru': 'imap.yandex.ru',
    'mail.ru': 'imap.mail.ru',
    'outlook.com': 'imap-mail.outlook.com'
}


def get_imap_server(email):
    '''Берем IMAP-сервер'''
    domain = email.split('@')[-1]
    return IMAP_SERVERS.get(domain, f'imap.{domain}')


def check_recovery_emails():
    '''Берем данные резервной почты из БД'''

    accounts = SessionLocal.query(Account).all()

    for acc in accounts:
        email = acc.recovery_email
        password = acc.recovery_password
        imap_host = get_imap_server(email)

        if not imap_host:
            print(f"IMAP сервер не найден для {email}")
            continue

        try:
            print(f'Подключаюсь к {email} ...')
            mail = imaplib.IMAP4_SSL(get_imap_server(email))
            mail.login (email, password)
            mail.select ('inbox')
            result, data = mail.search(None, 'ALL')
            mail_ids = data[0].split()
            print(f'{email}: {len(mail_ids)} писем')
            mail.logout()

        except imaplib.IMAP4.error as e:
            print(f"Ошибка для {email}: {str(e)}")

