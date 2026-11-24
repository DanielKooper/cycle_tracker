# ══════════════════════════════════════════════════════════════
#  main.py — Bloom 🌸
#  WebApp + покупки Stars + команды бота + канал + диагностика
#  Railway Start Command: gunicorn -w 1 -b 0.0.0.0:$PORT main:app
# ══════════════════════════════════════════════════════════════
import os
import json
import hmac
import time
import hashlib
import threading
import urllib.request
import urllib.error
import urllib.parse

from flask import Flask, request, jsonify, send_from_directory, abort

BOT_TOKEN   = os.environ.get("BOT_TOKEN", "").strip()
WEBAPP_URL  = os.environ.get("WEBAPP_URL", "").strip()
HOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "bloom-hook")
CHANNEL_URL = os.environ.get("CHANNEL_URL", "").strip()
DATA_DIR    = os.environ.get("DATA_DIR", ".")

STORE_PATH = os.path.join(DATA_DIR, "purchases.json")
PREFS_PATH = os.path.join(DATA_DIR, "prefs.json")

LAST_ERROR = {"time": 0, "method": "", "description": ""}

PACKS = {
    "analytics": {"emoji": "📊", "title": "Глубокая аналитика",
                  "desc": "ПМС-окно, фазы цикла и разброс", "stars": 50},
    "care":      {"emoji": "💞", "title": "Забота+",
                  "desc": "Расширенные советы партнёру", "stars": 75},
    "pdf":       {"emoji": "📥", "title": "PDF-отчёт",
                  "desc": "Красивый отчёт для врача", "stars": 30},
    "all":       {"emoji": "👑", "title": "Всё навсегда",
                  "desc": "Все функции Bloom Plus сразу", "stars": 149},
}

LANGS = {"ru": "Русский", "en": "English", "uk": "Українська"}

TEXT = {
    "ru": {
        "start": ("Привет! Я <b>Bloom</b> 🌸\nТвой личный трекер цикла и заботы.\n\n"
                  "Всё хранится только на твоём устройстве.\nНажми кнопку ниже, чтобы открыть приложение 👇"),
        "help": ("🌸 <b>Команды Bloom</b>\n\n/start — открыть приложение\n/plus — дополнения за звёзды ⭐\n"
                 "/care — советы партнёру\n/balance — баланс звёзд бота\n/transactions — последние операции\n"
                 "/refund — возврат последней покупки\n/language — язык бота\n/privacy — приватность\n\n"
                 "Bloom не заменяет консультацию врача."),
        "plus": ("👑 <b>Bloom Plus</b>\n\nДополнения покупаются прямо в приложении за Telegram Stars ⭐\n"
                 "Нажми на нужный товар — счёт откроется поверх WebApp."),
        "care": ("💞 <b>Как поддержать партнёршу</b>\n\n• Спроси: «Чем помочь?» вместо «Что случилось?»\n"
                 "• В менструацию — тепло, отдых, вкусное, меньше нагрузки.\n"
                 "• В фолликулярную фазу — свидания, идеи, активность.\n"
                 "• В овуляцию — романтика и важные разговоры.\n"
                 "• В лютеиновую фазу — терпение, еда, объятия, без споров.\n"
                 "• При задержке — не нагнетай, будь рядом и предложи помощь.\n\n"
                 "В приложении советы точнее: они зависят от фазы цикла."),
        "privacy": ("🔒 <b>Приватность Bloom</b>\n\n• Записи цикла хранятся на устройстве пользователя.\n"
                    "• Партнёр получает только ту код-ссылку, которую отправили вручную.\n"
                    "• В код-ссылке нет заметок и симптомов, только снимок цикла.\n"
                    "• Покупки привязаны к Telegram-аккаунту.\n\nBloom — справочный трекер, не медицинский сервис."),
        "language": "Выбери язык бота:",
        "lang_set": "Язык изменён 🌸",
        "balance_empty": "Пока нет звёзд на балансе 🤍",
        "balance": "⭐ Баланс бота: <b>{amount}</b> Stars",
        "balance_err": "Не удалось получить баланс 😔 Возможно, метод ещё недоступен для этого бота.",
        "transactions_empty": "Операций пока нет 🤍",
        "transactions_err": "Не удалось получить операции 😔",
        "refund_none": "У тебя нет покупок для возврата 🤍",
        "refund_ok": "✅ Возврат оформлен — звёзды вернулись на баланс ⭐",
        "refund_err": "Не удалось оформить возврат 😔 Попробуй позже.",
        "paid": "✅ <b>Оплата получена!</b> Спасибо 💗\n\n{emoji} <b>{title}</b> уже открыт в приложении — вернись в Bloom и пользуйся 👑",
        "open": "🌸 Открыть Bloom",
        "plus_btn": "👑 Bloom Plus · за ⭐",
        "channel_btn": "📣 Наш канал",
        "unknown": "Я пока не знаю такой команды 🤍 Напиши /help",
    },
    "en": {
        "start": ("Hi! I'm <b>Bloom</b> 🌸\nYour personal cycle and care tracker.\n\n"
                  "Everything stays on your device.\nTap below to open the app 👇"),
        "help": ("🌸 <b>Bloom commands</b>\n\n/start — open the app\n/plus — optional Star upgrades ⭐\n"
                 "/care — partner support tips\n/balance — bot Stars balance\n/transactions — recent transactions\n"
                 "/refund — refund last purchase\n/language — bot language\n/privacy — privacy\n\n"
                 "Bloom is not a substitute for medical advice."),
        "plus": ("👑 <b>Bloom Plus</b>\n\nOptional upgrades are purchased inside the app with Telegram Stars ⭐\n"
                 "Tap a product — the invoice opens right over the WebApp."),
        "care": ("💞 <b>How to support your partner</b>\n\n• Ask \"How can I help?\" instead of \"What happened?\"\n"
                 "• During period: warmth, rest, treats, less load.\n• Follicular phase: dates, ideas, activity.\n"
                 "• Ovulation: romance and important talks.\n• Luteal phase: patience, food, hugs, no arguments.\n"
                 "• If late: don't panic, stay close, offer help.\n\nThe app gives more precise phase-based tips."),
        "privacy": ("🔒 <b>Bloom privacy</b>\n\n• Cycle logs stay on the user's device.\n"
                    "• A partner only gets the share-link you send manually.\n"
                    "• The share-link contains a cycle snapshot, not notes or symptoms.\n"
                    "• Purchases are tied to the Telegram account.\n\nBloom is a reference tracker, not a medical service."),
        "language": "Choose bot language:",
        "lang_set": "Language updated 🌸",
        "balance_empty": "No Stars yet 🤍",
        "balance": "⭐ Bot balance: <b>{amount}</b> Stars",
        "balance_err": "Couldn't fetch balance 😔 The method may not be available for this bot yet.",
        "transactions_empty": "No transactions yet 🤍",
        "transactions_err": "Couldn't fetch transactions 😔",
        "refund_none": "No purchases to refund 🤍",
        "refund_ok": "✅ Refund completed — Stars are back ⭐",
        "refund_err": "Couldn't process refund 😔 Try later.",
        "paid": "✅ <b>Payment received!</b> Thank you 💗\n\n{emoji} <b>{title}</b> is unlocked in the app — return to Bloom 👑",
        "open": "🌸 Open Bloom",
        "plus_btn": "👑 Bloom Plus · Stars ⭐",
        "channel_btn": "📣 Our channel",
        "unknown": "I don't know that command yet 🤍 Try /help",
    },
    "uk": {
        "start": ("Привіт! Я <b>Bloom</b> 🌸\nТвій особистий трекер циклу та турботи.\n\n"
                  "Усе зберігається лише на твоєму пристрої.\nНатисни кнопку нижче, щоб відкрити застосунок 👇"),
        "help": ("🌸 <b>Команди Bloom</b>\n\n/start — відкрити застосунок\n/plus — доповнення за зірки ⭐\n"
                 "/care — поради партнеру\n/balance — баланс зірок бота\n/transactions — останні операції\n"
                 "/refund — повернення останньої покупки\n/language — мова бота\n/privacy — приватність\n\n"
                 "Bloom не замінює консультацію лікаря."),
        "plus": ("👑 <b>Bloom Plus</b>\n\nДоповнення купуються прямо в застосунку за Telegram Stars ⭐\n"
                 "Натисни на потрібний товар — рахунок відкриється поверх WebApp."),
        "care": ("💞 <b>Як підтримати партнерку</b>\n\n• Запитай: «Чим допомогти?» замість «Що сталося?»\n"
                 "• Під час менструації — тепло, відпочинок, смачне, менше навантаження.\n"
                 "• У фолікулярну фазу — побачення, ідеї, активність.\n"
                 "• В овуляцію — романтика й важливі розмови.\n"
                 "• У лютеїнову фазу — терпіння, їжа, обійми, без суперечок.\n"
                 "• При затримці — не нагнітай, будь поруч і запропонуй допомогу.\n\n"
                 "У застосунку поради точніші: вони залежать від фази циклу."),
        "privacy": ("🔒 <b>Приватність Bloom</b>\n\n• Записи циклу зберігаються на пристрої користувача.\n"
                    "• Партнер отримує лише те посилання-код, яке надіслали вручну.\n"
                    "• У посиланні-коді немає нотаток і симптомів, лише знімок циклу.\n"
                    "• Покупки прив'язані до Telegram-акаунта.\n\nBloom — довідковий трекер, не медичний сервіс."),
        "language": "Обери мову бота:",
        "lang_set": "Мову змінено 🌸",
        "balance_empty": "Поки немає зірок на балансі 🤍",
        "balance": "⭐ Баланс бота: <b>{amount}</b> Stars",
        "balance_err": "Не вдалося отримати баланс 😔 Можливо, метод ще недоступний для цього бота.",
        "transactions_empty": "Операцій поки немає 🤍",
        "transactions_err": "Не вдалося отримати операції 😔",
        "refund_none": "У тебе немає покупок для повернення 🤍",
        "refund_ok": "✅ Повернення оформлено — зірки повернулися на баланс ⭐",
        "refund_err": "Не вдалося оформити повернення 😔 Спробуй пізніше.",
        "paid": "✅ <b>Оплату отримано!</b> Дякую 💗\n\n{emoji} <b>{title}</b> уже відкрито в застосунку — повернися в Bloom 👑",
        "open": "🌸 Відкрити Bloom",
        "plus_btn": "👑 Bloom Plus · за ⭐",
        "channel_btn": "📣 Наш канал",
        "unknown": "Я поки не знаю такої команди 🤍 Напиши /help",
    },
}

app = Flask(__name__, static_folder="webapp", static_url_path="")
_lock = threading.Lock()


def _load(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(path, data):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


def tg(method, payload=None):
    req = urllib.request.Request(
        "https://api.telegram.org/bot%s/%s" % (BOT_TOKEN, method),
        data=json.dumps(payload or {}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            body = json.loads(e.read())
        except Exception:
            body = {"ok": False, "description": str(e)}
        LAST_ERROR["time"] = int(time.time())
        LAST_ERROR["method"] = method
        LAST_ERROR["description"] = body.get("description", str(e))
        app.logger.error("TG %s failed: %s", method, LAST_ERROR["description"])
        return body
    except Exception as e:
        LAST_ERROR["time"] = int(time.time())
        LAST_ERROR["method"] = method
        LAST_ERROR["description"] = str(e)
        app.logger.error("TG %s failed: %s", method, e)
        return {"ok": False, "description": str(e)}


def verify(init_data):
    LAST_ERROR["time"] = int(time.time())
    LAST_ERROR["method"] = "verify"
    if not BOT_TOKEN:
        LAST_ERROR["description"] = "AUTH: BOT_TOKEN пустой на сервере"
        return None
    if not init_data:
        LAST_ERROR["description"] = "AUTH: initData не пришёл из приложения"
        return None
    try:
        data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        got = data.pop("hash", "")
        if not got:
            LAST_ERROR["description"] = "AUTH: в initData нет поля hash"
            return None
        check = "\n".join("%s=%s" % (k, data[k]) for k in sorted(data))
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, got):
            me = tg("getMe")
            uname = me.get("result", {}).get("username") if me.get("ok") else "ТОКЕН НЕВАЛИДЕН"
            LAST_ERROR["time"] = int(time.time())
            LAST_ERROR["method"] = "verify"
            LAST_ERROR["description"] = (
                "AUTH: подпись не совпала. Сервер работает от бота @%s. "
                "Открой Bloom именно из него, либо поправь BOT_TOKEN в Railway." % uname)
            return None
        age = int(time.time()) - int(data.get("auth_date", "0"))
        if age > 86400:
            LAST_ERROR["description"] = "AUTH: сессия устарела (%s сек). Закрой и открой Bloom заново." % age
            return None
        LAST_ERROR["description"] = "AUTH OK — подпись прошла"
        return json.loads(data.get("user", "{}"))
    except Exception as e:
        LAST_ERROR