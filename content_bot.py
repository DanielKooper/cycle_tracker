# -*- coding: utf-8 -*-
# content_bot.py — автопубликация постов в канал Bloom
# Работает как отдельный процесс (worker). НЕ использует polling,
# поэтому не конфликтует с вебхуком основного бота в main.py.

import os
import sys
import json
import time
import logging
from datetime import datetime

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("content")

# ─────────── НАСТРОЙКИ ───────────
BOT_TOKEN = os.environ.get("CONTENT_BOT_TOKEN", "").strip()
CHANNEL_ID = os.environ.get("CHANNEL_ID", "").strip()
DATA_DIR = os.environ.get("DATA_DIR", ".").strip()
PUBLISH_ON_START = os.environ.get("PUBLISH_ON_START", "0").strip() == "1"
POST_TIMES = ["09:00", "14:00", "20:00"]
STATE_FILE = os.path.join(DATA_DIR, "content_state.json")

# ─────────── БИБЛИОТЕКА ПОСТОВ ───────────
CONTENT_LIBRARY = [
    {
        "id": "edu_001",
        "text": (
            "🌸 Цикл состоит из 4 фаз: менструация, фолликулярная, овуляция, лютеиновая.\n\n"
            "Каждая фаза влияет на энергию, настроение и либидо. "
            "Понимание фаз помогает планировать жизнь, а не бороться с собой.\n\n"
            "Отслеживать свой ритм → @bloomcalendarbot"
        ),
    },
    {
        "id": "edu_002",
        "text": (
            "📅 Длина цикла 21–35 дней — это норма.\n\n"
            "28 дней — среднее из учебника, а не обязательный стандарт. "
            "Отметь минимум 3 цикла, чтобы увидеть свой настоящий ритм.\n\n"
            "Отслеживать → @bloomcalendarbot"
        ),
    },
    {
        "id": "partner_001",
        "text": (
            "💞 Совет партнёру: за 5–7 дней до менструации прогестерон растёт, энергия падает.\n\n"
            "Что нужно ей: тепло, вкусное, объятия, меньше нагрузки.\n"
            "Что не нужно: споры по мелочам и фраза «у тебя ПМС?».\n\n"
            "Режим заботы подскажет больше → @bloomcalendarbot"
        ),
    },
    {
        "id": "partner_002",
        "text": (
            "✨ Овуляция — пик цикла: эстроген на максимуме, энергии и обаяния больше всего.\n\n"
            "Лучшее время для свиданий, романтики и важных разговоров. "
            "Не откладывай их на «потом».\n\n"
            "Подключить партнёра → @bloomcalendarbot"
        ),
    },
    {
        "id": "edu_003",
        "text": (
            "🍂 ПМС — это не капризы, это биохимия.\n\n"
            "Серотонин падает, магний расходуется быстрее, вода задерживается. "
            "Раздражительность и тяга к сладкому — физиология, а не слабость.\n\n"
            "Что помогает: магний, сон, тёплая ванна, меньше кофеина после 14:00.\n\n"
            "Отмечать симптомы → @bloomcalendarbot"
        ),
    },
    {
        "id": "partner_003",
        "text": (
            "🛍️ Чек-лист для партнёра на дни менструации:\n\n"
            "• Тёмный шоколад и бананы\n"
            "• Имбирный чай\n"
            "• Обезболивающее (если попросит)\n"
            "• Тёплая грелка и плед\n"
            "• Взять на себя посуду и готовку\n\n"
            "И просто обнять. Без слов.\n\n"
            "Полные подсказки по фазам → @bloomcalendarbot"
        ),
    },
]


# ─────────── СОСТОЯНИЕ ───────────
def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {"sent_ids": [], "last_sent": None}
        data.setdefault("sent_ids", [])
        return data
    except Exception:
        return {"sent_ids": [], "last_sent": None}


def save_state(state):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        log.error("Не удалось сохранить состояние: %s", e)


# ─────────── ПУБЛИКАЦИЯ ───────────
def publish_once():
    if not BOT_TOKEN:
        log.error("CONTENT_BOT_TOKEN не задан в Railway Variables — публикация пропущена")
        return
    if not CHANNEL_ID:
        log.error("CHANNEL_ID не задан в Railway Variables — публикация пропущена")
        return
    if not CONTENT_LIBRARY:
        log.error("Библиотека постов пуста")
        return

    state = load_state()
    sent = set(state["sent_ids"])

    post = None
    for item in CONTENT_LIBRARY:
        if item["id"] not in sent:
            post = item
            break

    if post is None:
        log.info("Все посты опубликованы — начинаю новый круг")
        state["sent_ids"] = []
        post = CONTENT_LIBRARY[0]

    url = "https://api.telegram.org/bot%s/sendMessage" % BOT_TOKEN
    payload = {"chat_id": CHANNEL_ID, "text": post["text"]}

    try:
        r = requests.post(url, json=payload, timeout=20)
        try:
            body = r.json()
        except Exception:
            body = {"ok": False, "description": r.text}

        if r.status_code == 200 and body.get("ok"):
            state["sent_ids"].append(post["id"])
            state["last_sent"] = datetime.now().isoformat()
            save_state(state)
            log.info("Опубликовано: %s", post["id"])
        else:
            log.error("Telegram отклонил пост %s: %s", post["id"], body.get("description"))
    except Exception as e:
        log.error("Сеть недоступна при отправке: %s", e)


# ─────────── ЗАПУСК ───────────
def main():
    log.info("=== content_bot запускается ===")
    log.info("Канал: %s", CHANNEL_ID or "НЕ ЗАДАН")
    log.info("Токен: %s", ("***" + BOT_TOKEN[-6:]) if BOT_TOKEN else "НЕ ЗАДАН")
    log.info("Постов в библиотеке: %s", len(CONTENT_LIBRARY))
    log.info("Расписание: %s", POST_TIMES)

    if PUBLISH_ON_START:
        log.info("PUBLISH_ON_START=1 — публикую сразу для проверки")
        publish_once()

    scheduler = BackgroundScheduler(timezone="Europe/Moscow")
    for t in POST_TIMES:
        hour, minute = t.split(":")
        scheduler.add_job(
            publish_once,
            CronTrigger(hour=int(hour), minute=int(minute), timezone="Europe/Moscow"),
            id="publish_" + t.replace(":", "_"),
            replace_existing=True,
        )
    scheduler.start()
    log.info("Планировщик запущен, жду времени публикации")

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        log.info("content_bot остановлен")


if __name__ == "__main__":
    main()