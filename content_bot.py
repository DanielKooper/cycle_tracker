import os
import json
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import requests
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

logger.info("=== content_bot.py загружается ===")
# ═══════════ НАСТРОЙКИ ═══════════
BOT_TOKEN = os.environ.get('CONTENT_BOT_TOKEN')
CHANNEL_ID = os.environ.get('CHANNEL_ID')
POST_TIMES = ['09:00', '14:00', '20:00']

# ═══════════ БИБЛИОТЕКА КОНТЕНТА ═══════════
CONTENT_LIBRARY = [
    {
        "id": "edu_001",
        "category": "education",
        "text": "🌸 Цикл состоит из 4 фаз: менструация, фолликулярная, овуляция, лютеиновая. Каждая фаза влияет на энергию, настроение и либидо. Понимание фаз помогает планировать жизнь."
    },
    {
        "id": "edu_002",
        "category": "education",
        "text": "📅 Длина цикла 21-35 дней — это норма. 28 дней — среднее значение, но у каждой женщины свой ритм. Отслеживай минимум 3 цикла, чтобы понять свой паттерн."
    },
    {
        "id": "partner_001",
        "category": "partner",
        "text": "💞 Совет партнёру: в лютеиновую фазу (за 5-7 дней до менструации) прогестерон растёт, энергия падает. Ей нужны: тепло, вкусное, объятия. Не спорь по мелочам."
    },
    {
        "id": "partner_002",
        "category": "partner",
        "text": "🔥 Совет партнёру: в овуляцию (пик цикла) эстроген на максимуме, либидо высокое. Это лучшее время для романтики, свиданий и важных разговоров."
    },
    # Добавь остальные посты...
]

# ═══════════ ОТПРАВКА В КАНАЛ ═══════════
def send_to_channel():
    """Отправляет следующий пост в канал"""
    try:
        # Читаем состояние
        state_file = 'channel_state.json'
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
        else:
            state = {'sent_ids': []}
        
        # Находим следующий пост
        next_post = None
        for post in CONTENT_LIBRARY:
            if post['id'] not in state['sent_ids']:
                next_post = post
                break
        
        if not next_post:
            # Все посты отправлены, сбрасываем
            state['sent_ids'] = []
            next_post = CONTENT_LIBRARY[0]
        
        # Отправляем
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
        payload = {
            'chat_id': CHANNEL_ID,
            'text': next_post['text'],
            'parse_mode': 'HTML'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"✅ Отправлено: {next_post['id']}")
            state['sent_ids'].append(next_post['id'])
            state['last_sent'] = datetime.now().isoformat()
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        else:
            print(f"❌ Ошибка отправки: {response.status_code} - {response.text}")
    
    except Exception as e:
        print(f"❌ Исключение в send_to_channel: {e}")

# ═══════════ ЗАПУСК ═══════════
def main():
    scheduler = BackgroundScheduler()
    
    # Добавляем задачи на каждое время
    for post_time in POST_TIMES:
        hour, minute = map(int, post_time.split(':'))
        scheduler.add_job(
            send_to_channel,
            CronTrigger(hour=hour, minute=minute),
            id=f'auto_publish_{post_time}',
            replace_existing=True
        )
    
    scheduler.start()
    print(f"🚀 Контент-бот запущен. Расписание: {POST_TIMES}")
    
    # Держим процесс живым
    try:
        while True:
            time.sleep(60)  # Спим 60 секунд, потом снова
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("🛑 Контент-бот остановлен")

if __name__ == '__main__':
    main()