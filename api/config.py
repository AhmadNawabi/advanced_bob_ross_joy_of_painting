import os
import logging
from logging.handlers import RotatingFileHandler

# DB config
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = "advanced_bob_ross_joy_of_painting"

# Auth
API_SECRET_KEY = os.getenv('API_SECRET_KEY', 'dev-secret-change-in-prod')

# Logger
logger = logging.getLogger("joy_of_painting_api")
logger.setLevel(logging.INFO)

console = logging.StreamHandler()
console.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(console)
