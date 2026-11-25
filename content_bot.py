# -*- coding: utf-8 -*-
# content_bot.py — автопубликация постов + админ-команды.
# Свой токен (CONTENT_BOT_TOKEN), поэтому polling не конфликтует
# с вебхуком основного бота из main.py.

import os
import sys
import json
import time
import threading
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
TZ_NAME = os.environ.get("TZ_NAME", "Europe/Moscow").strip()

ADMIN_IDS = set()
for _part in os.environ.get("ADMIN_IDS", "").replace(";", ",").split(","):
    _part = _part.strip()
    if _part.isdigit():
        ADMIN_IDS.add(int(_part))

POST_TIMES = ["09:00", "14:00", "20:00"]
STATE_FILE = os.path.join(DATA_DIR, "content_state.json")
API = "https://api.telegram.org/bot%s/%s"
_lock = threading.Lock()

# ─────────── БИБЛИОТЕКА ПОСТОВ ───────────
CONTENT_LIBRARY = [
    {"id": "edu_001", "text": (
        "🌸 Цикл состоит из 4 фаз: менструация, фолликулярная, овуляция, лютеиновая.\n\n"
        "Каждая влияет на энергию, настроение и либидо. Понимание фаз помогает "
        "планировать жизнь, а не бороться с собой.\n\n"
        "Отслеживать свой ритм → @bloomcalendarbot")},
    {"id": "edu_002", "text": (
        "📅 Длина цикла 21–35 дней — это норма.\n\n"
        "28 дней — среднее из учебника, а не обязательный стандарт. "
        "Отметь минимум 3 цикла, чтобы увидеть свой настоящий ритм.\n\n"
        "Отслеживать → @bloomcalendarbot")},
    {"id": "partner_001", "text": (
        "💞 Совет партнёру: за 5–7 дней до менструации прогестерон растёт, энергия падает.\n\n"
        "Что нужно ей: тепло, вкусное, объятия, меньше нагрузки.\n"
        "Что не нужно: споры по мелочам и фраза «у тебя ПМС?».\n\n"
        "Режим заботы подскажет больше → @bloomcalendarbot")},
    {"id": "partner_002", "text": (
        "✨ Овуляция — пик цикла: эстроген на максимуме, энергии и обаяния больше всего.\n\n"
        "Лучшее время для свиданий, романтики и важных разговоров. "
        "Не откладывай их на «потом».\n\n"
        "Подключить партнёра → @bloomcalendarbot")},
    {"id": "edu_003", "text": (
        "🍂 ПМС — это не капризы, это биохимия.\n\n"
        "Серотонин падает, магний расходуется быстрее, вода задерживается. "
        "Раздражительность и тяга к сладкому — физиология, а не слабость.\n\n"
        "Помогает: магний, сон, тёплая ванна, меньше кофеина после 14:00.\n\n"
        "Отмечать симптомы → @bloomcalendarbot")},
    {"id": "partner_003", "text": (
        "🛍️ Чек-лист для партнёра на дни менструации:\n\n"
        "• Тёмный шоколад и бананы\n"
        "• Имбирный чай\n"
        "• Обезболивающее, если попросит\n"
        "• Тёплая грелка и плед\n"
        "• Взять на себя посуду и готовку\n\n"
        "И просто обнять. Без слов.\n\n"
        "Полные подсказки по фазам → @bloomcalendarbot")},
]


# ─────────── СОСТОЯНИЕ ───────────
def load_state():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("bad state")
        data.setdefault("sent_ids", [])
        data.setdefault("paused", False)
        data.setdefault("last_sent", None)
        return data
    except Exception:
        return {"sent_ids": [], "paused": False, "last_sent": None}


def save_state(state):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        log.error("Не удалось сохранить состояние: %s", e)


def tg(method, payload=None, timeout=30):
    try:
        r = requests.post(API % (BOT_TOKEN, method), json=payload or {}, timeout=timeout)
        try:
            return r.json()
        except Exception:
            return {"ok": False, "description": r.text}
    except Exception as e:
        return {"ok": False, "description": str(e)}


def next_post(state):
    sent = set(state["sent_ids"])
    for item in CONTENT_LIBRARY:
        if item["id"] not in sent:
            return item
    return None


# ─────────── ПУБЛИКАЦИЯ ───────────
def publish(force=False):
    if not BOT_TOKEN:
        log.error("CONTENT_BOT_TOKEN не задан")
        return False, "Токен не задан в Railway Variables"
    if not CHANNEL_ID:
        log.error("CHANNEL_ID не задан")
        return False, "Канал не задан в Railway Variables"

    with _lock:
        state = load_state()
        if state["paused"] and not force:
            log.info("Пауза — публикация пропущена")
            return False, "Автопостинг на паузе (/resume)"

        post = next_post(state)
        if post is None:
            log.info("Все посты опубликованы — начинаю новый круг")
            state["sent_ids"] = []
            post = CONTENT_LIBRARY[0]

        res = tg("sendMessage", {"chat_id": CHANNEL_ID, "text": post["text"]})
        if res.get("ok"):
            state["sent_ids"].append(post["id"])
            state["last_sent"] = datetime.now().isoformat(timespec="seconds")
            save_state(state)
            log.info("Опубликовано: %s", post["id"])
            return True, post["id"]

        log.error("Telegram отклонил пост: %s", res.get("description"))
        return False, str(res.get("description"))


def reply(chat_id, text):
    for i in range(0, len(text), 3800):
        tg("sendMessage", {"chat_id": chat_id, "text": text[i:i + 3800]})


# ─────────── КОМАНДЫ ───────────
HELP = (
    "🤖 Контент-бот Bloom\n\n"
    "/publish — опубликовать следующий пост сейчас\n"
    "/preview — показать следующий пост без публикации\n"
    "/list — список постов и их статус\n"
    "/stats — статистика и расписание\n"
    "/pause — остановить автопостинг\n"
    "/resume — возобновить автопостинг\n"
    "/reset — начать библиотеку с первого поста\n"
    "/help — эта справка"
)


def handle_message(msg):
    chat = (msg.get("chat") or {}).get("id")
    uid = (msg.get("from") or {}).get("id")
    text = (msg.get("text") or "").strip()
    if not chat or not text.startswith("/"):
        return

    cmd = text.split()[0].split("@")[0].lower()
    write_cmds = ("/publish", "/pause", "/resume", "/reset")

    if cmd in write_cmds and uid not in ADMIN_IDS:
        reply(chat,
              "⛔ Эта команда только для администратора.\n\n"
              "Добавь свой Telegram ID в переменную ADMIN_IDS в Railway "
              "и перезапусти сервис. Узнать ID: @userinfobot")
        return

    if cmd in ("/start", "/help"):
        reply(chat, HELP)
        return

    if cmd == "/publish":
        ok, info = publish(force=True)
        reply(chat, ("✅ Опубликовано: " + info) if ok else ("❌ Не опубликовано: " + info))
        return

    if cmd == "/preview":
        with _lock:
            state = load_state()
        post = next_post(state)
        if post is None:
            reply(chat, "Все посты опубликованы. /reset — начать заново.")
        else:
            reply(chat, "👀 Следующий пост (" + post["id"] + "):\n\n" + post["text"])
        return

    if cmd == "/list":
        with _lock:
            state = load_state()
        sent = set(state["sent_ids"])
        lines = ["📝 Библиотека постов:\n"]
        for item in CONTENT_LIBRARY:
            mark = "✅" if item["id"] in sent else "⏳"
            first = item["text"].split("\n")[0]
            if len(first) > 60:
                first = first[:60] + "…"
            lines.append(mark + " " + item["id"] + " — " + first)
        reply(chat, "\n".join(lines))
        return

    if cmd == "/stats":
        with _lock:
            state = load_state()
        total = len(CONTENT_LIBRARY)
        done = len(state["sent_ids"])
        status = "⏸ на паузе" if state["paused"] else "▶️ работает"
        reply(chat,
              "📊 Статистика\n\n"
              "Канал: " + (CHANNEL_ID or "не задан") + "\n"
              "Постов в библиотеке: " + str(total) + "\n"
              "Опубликовано: " + str(done) + "\n"
              "Осталось: " + str(max(0, total - done)) + "\n"
              "Последний пост: " + str(state["last_sent"] or "—") + "\n"
              "Расписание: " + ", ".join(POST_TIMES) + " (" + TZ_NAME + ")\n"
              "Статус: " + status)
        return

    if cmd == "/pause":
        with _lock:
            state = load_state()
            state["paused"] = True
            save_state(state)
        reply(chat, "⏸ Автопостинг остановлен. /resume — возобновить.")
        return

    if cmd == "/resume":
        with _lock:
            state = load_state()
            state["paused"] = False
            save_state(state)
        reply(chat, "▶️ Автопостинг возобновлён.")
        return

    if cmd == "/reset":
        with _lock:
            state = load_state()
            state["sent_ids"] = []
            save_state(state)
        reply(chat, "↩️ Список сброшен. Следующим уйдёт первый пост библиотеки.")
        return

    reply(chat, "Не знаю такой команды 🤍\n\n" + HELP)


# ─────────── ПРИЁМ КОМАНД ───────────
def poll_loop():
    if not BOT_TOKEN:
        log.error("CONTENT_BOT_TOKEN не задан — команды работать не будут")
        return

    me = tg("getMe")
    if me.get("ok"):
        log.info("Контент-бот: @%s", me["result"].get("username"))
    else:
        log.error("Токен контент-бота невалиден: %s", me.get("description"))
        return

    # у этого бота не должно быть вебхука, иначе getUpdates вернёт конфликт
    tg("deleteWebhook", {"drop_pending_updates": False})

    offset = None
    log.info("Приём команд включён")
    while True:
        payload = {"timeout": 25, "allowed_updates": ["message"]}
        if offset is not None:
            payload["offset"] = offset
        res = tg("getUpdates", payload, timeout=40)
        if not res.get("ok"):
            desc = str(res.get("description"))
            log.error("getUpdates: %s", desc)
            time.sleep(10 if "Conflict" in desc else 5)
            continue
        for update in res.get("result", []):
            offset = update["update_id"] + 1
            try:
                handle_message(update.get("message") or {})
            except Exception as e:
                log.error("Ошибка обработчика: %s", e)


# ─────────── ЗАПУСК ───────────
def main():
    log.info("=== content_bot запускается ===")
    log.info("Канал: %s", CHANNEL_ID or "НЕ ЗАДАН")
    log.info("Токен: %s", ("***" + BOT_TOKEN[-6:]) if BOT_TOKEN else "НЕ ЗАДАН")
    log.info("Админы: %s", sorted(ADMIN_IDS) if ADMIN_IDS else "НЕ ЗАДАНЫ")
    log.info("Постов в библиотеке: %s", len(CONTENT_LIBRARY))

    if PUBLISH_ON_START:
        log.info("PUBLISH_ON_START=1 — публикую сразу")
        publish(force=True)

    scheduler = BackgroundScheduler(timezone=TZ_NAME)
    for t in POST_TIMES:
        hour, minute = t.split(":")
        scheduler.add_job(
            publish,
            CronTrigger(hour=int(hour), minute=int(minute), timezone=TZ_NAME),
            id="publish_" + t.replace(":", "_"),
            replace_existing=True,
        )
    scheduler.start()
    log.info("Планировщик запущен: %s (%s)", POST_TIMES, TZ_NAME)

    threading.Thread(target=poll_loop, daemon=True).start()

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        log.info("content_bot остановлен")


if __name__ == "__main__":
    main()