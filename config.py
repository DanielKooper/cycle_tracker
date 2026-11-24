# cycle_tracker/config.py
import os

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN', '5472255249:AAFVtNYCNgTDZ7GiiGOqh5NJpJKL7sasDa4')

# Database
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///cycle_tracker.db')

# WebApp URL
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://your-domain.com/webapp')

# Secret key for partner codes
SECRET_KEY = os.getenv('SECRET_KEY', '2582')