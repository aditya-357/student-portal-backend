# import psycopg2 # type: ignore
# from config import DB_CONFIG

# def get_connection():
#     return psycopg2.connect(**DB_CONFIG)

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    conn = psycopg2.connect(
        os.getenv("DATABASE_URL")
    )
    return conn