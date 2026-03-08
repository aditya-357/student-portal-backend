import psycopg2 # type: ignore
from config import DB_CONFIG

def get_connection():
    return psycopg2.connect(**DB_CONFIG)
