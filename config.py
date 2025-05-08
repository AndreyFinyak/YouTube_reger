from dotenv import load_dotenv
import os

load_dotenv()

DB_SETTINGS = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

SMS_API_KEY = os.getenv('SMS_ACTIVATE_API_KEY')
