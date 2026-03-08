import random
import string
from datetime import datetime, timedelta

def generate_random_password(length=8):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def generate_otp():
    return str(random.randint(100000, 999999))

def otp_expiry_time(minutes=10):
    return datetime.now() + timedelta(minutes=minutes)
