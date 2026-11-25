# ══════════════════════════════════════════════════════════════
#  content_bot.py — автопубликация контента в канал Bloom
#  Работает как отдельный процесс (worker) на Railway
#  НЕ конфликтует с main.py (вебхук основного бота)
# ══════════════════════════════════════════════════════════════
import os
import json
import time
import logging
import requests
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# ═══════════════ НАСТРОЙКИ ═══════════════
BOT_TOKEN = os.environ.get("CONTENT_BOT_TOKEN", "").strip()
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()
POST_TIMES = ["09:00", "14:00", "20:00"]

# ═══════════════ БИБЛИОТЕКА КОНТЕНТА ═══════════════
# Полный набор из 200 постов — в файле content_library_extended.py
# Здесь короткая версия для проверки. Замени импорт, если есть.
CONTENT_LIBRARY = [
    {
        "id": "edu_001",
        "category": "education",
        "text": "🌸 Цикл состоит из 4 фаз: менструация, фолликулярная, овуляция, лютеиновая. Каждая фаза влияет на энергию, настроение и либидо. Понимание фаз помогает планировать жизнь.\n\nОтслеживай в Bloom → @bloomcalendarbot",
    },
    {
        "id": "edu_002",
        "category": "education",
        "text": "📅 Длина цикла 21–35 дней — это норма. 28 дней — среднее значение, но у каждой женщины свой ритм. Отслеживай минимум 3 цикла, чтобы понять свой паттерн.\n\nОтслеживай в Bloom → @bloomcalendarbot",
    },
    {
        "id": "partner_001",
        "category": "partner",
        "text": "💞 Совет партнёру: в лютеиновую фазу (за 5–7 дней до менструации) прогестерон растёт, энергия падает. Ей нужны: тепло, вкусное, объятия. Не спорь по мелочам.\n\nПодключи партнёра через Bloom → @bloomcalendarbot",
    },
    {
        "id": "partner_002",
        "category": "partner",
        "text": "🔥 Совет партнёру: в овуляцию (пик цикла) эстроген на максимуме, либидо высокое. Это лучшее время для романтики, свиданий и важных разговоров.\n\nПодключи партнёра через Bloom → @bloomcalendarbot",
    },
    {
        "id": "edu_003",
        "category": "education",
        "text": "📊 4 фазы цикла: менструация 🌸, фолликулярная 🌱, овуляция 💫, лютеиновая 🍂. Каждая со своей биохимией, энергией и задачами. Знание фаз = меньше тревоги и больше контроля.\n\nОтслеживай в Bloom → @bloomcalendarbot",
    },
    {
        "id": "partner_003",
        "category": "partner",
        "text": "🍂 ПМС — это не капризы, это прогестерон. Не говори «у тебя ПМС?». Скажи: «Я вижу, что тебе тяжело. Чем могу помочь прямо сейчас?»\n\nРежим заботы в Bloom подскажет больше → @bloomcalendarbot",
    },
]

# ═══════════════ СОСТОЯНИЕ ═══════════════
STATE_FILE = "content_state.json"


def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"sent_ids": [], "last_sent": None}


def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error("Не удалось сохранить состояние: %s", e)


# ═══════════════ ОТПРАВКА В КАНАЛ ═══════════════
def send_to_channel():
    """Отправляет следующий неопубликованный пост в канал."""
    if not BOT_TOKEN:
        logger.error("CONTENT_BOT_TOKEN не задан — публикация пропущена")
        return
    if not CHANNEL_ID:
        logger.error("CHANNEL_ID не задан — публикация пропущена")
        return

    state = load_state()
    sent_ids = set(state.get("sent_ids", []))

    # Находим следующий пост
    next_post = None
    for post in CONTENT_LIBRARY:
        if post["id"] not in sent_ids:
            next_post = post
            break

    # Все посты опубликованы — сбрасываем цикл
    if not next_post:
        logger.info("Все посты опубликованы, сбрасываю цикл")
        state["sent_ids"] = []
        next_post = CONTENT_LIBRARY[0]

    # Отправляем через Telegram API
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": next_post["text"]}

    try:
        response = requests.post(url, json=payload, timeout=15)
        if response.status_code == 200:
            logger.info("✅ Опубликовано: %s", next_post["id"])
            state["sent_ids"].append(next_post["id"])
            state["last_sent"] = datetime.now().isoformat()
            save_state(state)
        else:
            logger.error(
                "❌ Ошибка %s: %s",
                response.status_code,
                response.text,
            )
    except Exception as e:
        logger.error("❌ Исключение при отправке: %s", e)


# ═══════════════ ЗАПУСК ═══════════════
def main():
    logger.info("Запуск контент-бота…")
    logger.info("Канал: %s", CHANNEL_ID or "— не задан —")
    logger.info("Токен: %s", "***" + BOT_TOKEN[-6:] if BOT_TOKEN else "— не задан —")
    logger.info("Расписание: %s", POST_TIMES)

    scheduler = BackgroundScheduler()

    for post_time in POST_TIMES:
        hour, minute = map(int, post_time.split(":"))
        scheduler.add_job(
            send_to_channel,
            CronTrigger(hour=hour, minute=minute),
            id=f"auto_publish_{post_time}",
            replace_existing=True,
        )

    scheduler.start()
    logger.info("🚀 Контент-бот запущен. Расписание: %s", POST_TIMES)

    # Держим процесс живым
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("🛑 Контент-бот остановлен")


if __name__ == "__main__":
    main()