# content_bot.py — бот автопостинга (БЕЗ polling, только scheduler)
import os
import json
import logging
from datetime import datetime
from threading import Lock
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot
from content_library import POSTS

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = os.environ.get('CONTENT_BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID', '@bloom_channel')
POST_TIMES = ["09:00", "14:00", "20:00"]

# Хранилище
DATA_FILE = 'content_data.json'
lock = Lock()

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'published': [], 'stats': {}}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

def auto_publish():
    """Автоматическая публикация поста в канал"""
    try:
        data = load_data()
        published_ids = set(data['published'])
        
        # Находим первый неопубликованный пост
        for post in POSTS:
            if post['id'] not in published_ids:
                # Публикуем
                with lock:
                    data['published'].append(post['id'])
                    data['stats'][post['id']] = {
                        'date': datetime.now().isoformat(),
                        'category': post['category']
                    }
                    save_data(data)
                
                # Отправляем в канал
                bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=post['text']
                )
                
                logger.info(f'✅ Опубликовано: {post["id"]}')
                return
        
        logger.info('Все посты уже опубликованы')
        
    except Exception as e:
        logger.error(f'Ошибка автопубликации: {e}')

def init_scheduler():
    """Инициализация планировщика"""
    scheduler = BackgroundScheduler()
    
    # Добавляем задачи на каждое время из POST_TIMES
    for post_time in POST_TIMES:
        hour, minute = map(int, post_time.split(':'))
        scheduler.add_job(
            auto_publish,
            CronTrigger(hour=hour, minute=minute),
            id=f'auto_publish_{post_time}',
            replace_existing=True
        )
    
    scheduler.start()
    logger.info(f'🚀 Контент-бот запущен. Расписание: {POST_TIMES}')
    
    # Держим процесс живым
    try:
        while True:
            import time
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info('Контент-бот остановлен')

if __name__ == '__main__':
    init_scheduler()