# ══════════════════════════════════════════════════════════════
#  main.py — Bloom 🌸
#  WebApp + покупки Stars внутри приложения + команды бота + канал
#  Railway Start Command: gunicorn -w 1 -b 0.0.0.0:$PORT main:app
# ══════════════════════════════════════════════════════════════
import os
import json
import hmac
import time
import hashlib
import threading
import urllib.request
import urllib.parse

from flask import Flask, request, jsonify, send_from_directory, abort

BOT_TOKEN   = os.environ.get("BOT_TOKEN", "")
WEBAPP_URL  = os.environ.get("WEBAPP_URL", "")
HOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "bloom-hook")
CHANNEL_URL = os.environ.get("CHANNEL_URL", "")
DATA_DIR    = os.environ.get("DATA_DIR", ".")

STORE_PATH = os.path.join(DATA_DIR, "purchases.json")
PREFS_PATH = os.path.join(DATA_DIR, "prefs.json")

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

LANGS = {
    "ru": "Русский",
    "en": "English",
    "uk": "Українська",
}

TEXT = {
    "ru": {
        "start": (
            "Привет! Я <b>Bloom</b> 🌸\n"
            "Твой личный трекер цикла и заботы.\n\n"
            "Всё хранится только на твоём устройстве.\n"
            "Нажми кнопку ниже, чтобы открыть приложение 👇"
        ),
        "help": (
            "🌸 <b>Команды Bloom</b>\n\n"
            "/start — открыть приложение\n"
            "/plus — дополнения за звёзды ⭐\n"
            "/care — советы партнёру\n"
            "/balance — баланс звёзд бота\n"
            "/transactions — последние операции\n"
            "/refund — возврат последней покупки\n"
            "/language — язык бота\n"
            "/privacy — приватность\n\n"
            "Bloom не заменяет консультацию врача."
        ),
        "plus": (
            "👑 <b>Bloom Plus</b>\n\n"
            "Дополнения покупаются прямо в приложении за Telegram Stars ⭐\n"
            "Нажми на нужный товар — счёт откроется поверх WebApp."
        ),
        "care": (
            "💞 <b>Как поддержать партнёршу</b>\n\n"
            "• Спроси: «Чем помочь?» вместо «Что случилось?»\n"
            "• В менструацию — тепло, отдых, вкусное, меньше нагрузки.\n"
            "• В фолликулярную фазу — свидания, идеи, активность.\n"
            "• В овуляцию — романтика и важные разговоры.\n"
            "• В лютеиновую фазу — терпение, еда, объятия, без споров.\n"
            "• При задержке — не нагнетай, будь рядом и предложи помощь.\n\n"
            "В приложении советы точнее: они зависят от фазы цикла."
        ),
        "privacy": (
            "🔒 <b>Приватность Bloom</b>\n\n"
            "• Записи цикла хранятся на устройстве пользователя.\n"
            "• Партнёр получает только ту код-ссылку, которую отправили вручную.\n"
            "• В код-ссылке нет заметок и симптомов, только снимок цикла.\n"
            "• Покупки привязаны к Telegram-аккаунту.\n\n"
            "Bloom — справочный трекер, не медицинский сервис."
        ),
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
        "start": (
            "Hi! I'm <b>Bloom</b> 🌸\n"
            "Your personal cycle and care tracker.\n\n"
            "Everything stays on your device.\n"
            "Tap below to open the app 👇"
        ),
        "help": (
            "🌸 <b>Bloom commands</b>\n\n"
            "/start — open the app\n"
            "/plus — optional Star upgrades ⭐\n"
            "/care — partner support tips\n"
            "/balance — bot Stars balance\n"
            "/transactions — recent transactions\n"
            "/refund — refund last purchase\n"
            "/language — bot language\n"
            "/privacy — privacy\n\n"
            "Bloom is not a substitute for medical advice."
        ),
        "plus": (
            "👑 <b>Bloom Plus</b>\n\n"
            "Optional upgrades are purchased inside the app with Telegram Stars ⭐\n"
            "Tap a product — the invoice opens right over the WebApp."
        ),
        "care": (
            "💞 <b>How to support your partner</b>\n\n"
            "• Ask \"How can I help?\" instead of \"What happened?\"\n"
            "• During period: warmth, rest, treats, less load.\n"
            "• Follicular phase: dates, ideas, activity.\n"
            "• Ovulation: romance and important talks.\n"
            "• Luteal phase: patience, food, hugs, no arguments.\n"
            "• If late: don't panic, stay close, offer help.\n\n"
            "The app gives more precise phase-based tips."
        ),
        "privacy": (
            "🔒 <b>Bloom privacy</b>\n\n"
            "• Cycle logs stay on the user's device.\n"
            "• A partner only gets the share-link you send manually.\n"
            "• The share-link contains a cycle snapshot, not notes or symptoms.\n"
            "• Purchases are tied to the Telegram account.\n\n"
            "Bloom is a reference tracker, not a medical service."
        ),
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
        "start": (
            "Привіт! Я <b>Bloom</b> 🌸\n"
            "Твій особистий трекер циклу та турботи.\n\n"
            "Усе зберігається лише на твоєму пристрої.\n"
            "Натисни кнопку нижче, щоб відкрити застосунок 👇"
        ),
        "help": (
            "🌸 <b>Команди Bloom</b>\n\n"
            "/start — відкрити застосунок\n"
            "/plus — доповнення за зірки ⭐\n"
            "/care — поради партнеру\n"
            "/balance — баланс зірок бота\n"
            "/transactions — останні операції\n"
            "/refund — повернення останньої покупки\n"
            "/language — мова бота\n"
            "/privacy — приватність\n\n"
            "Bloom не замінює консультацію лікаря."
        ),
        "plus": (
            "👑 <b>Bloom Plus</b>\n\n"
            "Доповнення купуються прямо в застосунку за Telegram Stars ⭐\n"
            "Натисни на потрібний товар — рахунок відкриється поверх WebApp."
        ),
        "care": (
            "💞 <b>Як підтримати партнерку</b>\n\n"
            "• Запитай: «Чим допомогти?» замість «Що сталося?»\n"
            "• Під час менструації — тепло, відпочинок, смачне, менше навантаження.\n"
            "• У фолікулярну фазу — побачення, ідеї, активність.\n"
            "• В овуляцію — романтика й важливі розмови.\n"
            "• У лютеїнову фазу — терпіння, їжа, обійми, без суперечок.\n"
            "• При затримці — не нагнітай, будь поруч і запропонуй допомогу.\n\n"
            "У застосунку поради точніші: вони залежать від фази циклу."
        ),
        "privacy": (
            "🔒 <b>Приватність Bloom</b>\n\n"
            "• Записи циклу зберігаються на пристрої користувача.\n"
            "• Партнер отримує лише те посилання-код, яке надіслали вручну.\n"
            "• У посиланні-коді немає нотаток і симптомів, лише знімок циклу.\n"
            "• Покупки прив'язані до Telegram-акаунта.\n\n"
            "Bloom — довідковий трекер, не медичний сервіс."
        ),
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
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())


def verify(init_data):
    if not init_data or not BOT_TOKEN:
        return None
    try:
        data = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
        got = data.pop("hash", "")
        check = "\n".join("%s=%s" % (k, data[k]) for k in sorted(data))
        secret = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, got):
            return None
        if abs(time.time() - int(data.get("auth_date", "0"))) > 86400:
            return None
        return json.loads(data.get("user", "{}"))
    except Exception:
        return None


def get_lang(uid):
    prefs = _load(PREFS_PATH)
    return prefs.get(str(uid), "ru")


def set_lang(uid, lang):
    if lang not in LANGS:
        return
    with _lock:
        prefs = _load(PREFS_PATH)
        prefs[str(uid)] = lang
        _save(PREFS_PATH, prefs)


def tr(uid, key, **kwargs):
    lang = get_lang(uid)
    text = TEXT.get(lang, TEXT["ru"]).get(key, TEXT["ru"].get(key, key))
    return text.format(**kwargs) if kwargs else text


def app_url_from_request():
    if WEBAPP_URL:
        return WEBAPP_URL.rstrip("/")
    host = request.headers.get("X-Forwarded-Host") or request.host
    return "https://" + host.rstrip("/")


def open_kb(uid):
    rows = [
        [{"text": tr(uid, "open"), "web_app": {"url": app_url_from_request()}}],
        [{"text": tr(uid, "plus_btn"), "callback_data": "plus_menu"}],
    ]
    if CHANNEL_URL:
        rows.append([{"text": tr(uid, "channel_btn"), "url": CHANNEL_URL}])
    return {"inline_keyboard": rows}


@app.get("/")
def index():
    return send_from_directory("webapp", "index.html")


@app.get("/<path:p>")
def statics(p):
    if p.startswith("api/"):
        abort(404)
    return send_from_directory("webapp", p)


@app.post("/api/invoice")
def api_invoice():
    body = request.get_json(silent=True) or {}
    user = verify(body.get("initData", ""))
    if not user:
        return jsonify(ok=False, error="auth"), 401
    key = body.get("pack")
    pack = PACKS.get(key)
    if not pack:
        return jsonify(ok=False, error="pack"), 400
    try:
        res = tg("createInvoiceLink", {
            "title": "Bloom Plus · " + pack["title"],
            "description": pack["desc"],
            "payload": json.dumps({"p": key, "u": user["id"]}, separators=(",", ":")),
            "provider_token": "",
            "currency": "XTR",
            "prices": [{"label": pack["title"], "amount": pack["stars"]}],
        })
    except Exception as e:
        app.logger.error("createInvoiceLink: %s", e)
        return jsonify(ok=False, error="telegram"), 502
    if not res.get("ok"):
        return jsonify(ok=False, error="telegram"), 502
    return jsonify(ok=True, link=res["result"], stars=pack["stars"])


@app.get("/api/me")
def api_me():
    user = verify(request.args.get("initData", ""))
    if not user:
        return jsonify(ok=False, error="auth"), 401
    with _lock:
        store = _load(STORE_PATH)
    packs = sorted({i["p"] for i in store.get(str(user["id"]), [])})
    return jsonify(ok=True, packs=packs, lang=get_lang(user["id"]))


@app.get("/api/config")
def api_config():
    return jsonify(ok=True, channel=CHANNEL_URL)


@app.post("/api/telegram")
def api_telegram():
    if request.headers.get("X-Telegram-Bot-Api-Secret-Token") != HOOK_SECRET:
        return "forbidden", 403
    update = request.get_json(silent=True) or {}
    try:
        handle_update(update)
    except Exception as e:
        app.logger.error("webhook: %s", e)
    return "ok"


def send(chat_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return tg("sendMessage", payload)


def handle_update(u):
    if "pre_checkout_query" in u:
        q = u["pre_checkout_query"]
        ok = False
        try:
            ok = json.loads(q["invoice_payload"])["p"] in PACKS
        except Exception:
            ok = False
        tg("answerPreCheckoutQuery", {
            "pre_checkout_query_id": q["id"],
            "ok": ok,
            **({} if ok else {"error_message": "Unknown product 🤔"}),
        })
        return

    if "callback_query" in u:
        q = u["callback_query"]
        uid = q["from"]["id"]
        chat = q["message"]["chat"]["id"]
        data = q.get("data", "")
        tg("answerCallbackQuery", {"callback_query_id": q["id"]})

        if data == "plus_menu":
            send(chat, tr(uid, "plus"), open_kb(uid))
            return

        if data.startswith("lang_"):
            lang = data.replace("lang_", "")
            set_lang(uid, lang)
            send(chat, tr(uid, "lang_set"), open_kb(uid))
            return

        return

    msg = u.get("message") or {}
    if not msg:
        return
    chat = msg["chat"]["id"]
    uid = msg.get("from", {}).get("id", chat)
    text = (msg.get("text") or "").strip()

    if "successful_payment" in msg:
        sp = msg["successful_payment"]
        data = json.loads(sp["invoice_payload"])
        buyer, key = str(data["u"]), data["p"]
        with _lock:
            store = _load(STORE_PATH)
            store.setdefault(buyer, []).append({
                "p": key,
                "c": sp["telegram_payment_charge_id"],
                "t": int(time.time()),
            })
            _save(STORE_PATH, store)
        pack = PACKS.get(key, {})
        send(chat, tr(uid, "paid", emoji=pack.get("emoji", "👑"), title=pack.get("title", "Bloom Plus")))
        return

    if text.startswith("/start"):
        send(chat, tr(uid, "start"), open_kb(uid))
        return

    if text.startswith("/help"):
        send(chat, tr(uid, "help"), open_kb(uid))
        return

    if text.startswith("/plus"):
        send(chat, tr(uid, "plus"), open_kb(uid))
        return

    if text.startswith("/care"):
        send(chat, tr(uid, "care"), open_kb(uid))
        return

    if text.startswith("/privacy"):
        send(chat, tr(uid, "privacy"), open_kb(uid))
        return

    if text.startswith("/language"):
        kb = {"inline_keyboard": [[{"text": name, "callback_data": "lang_" + code}] for code, name in LANGS.items()]}
        send(chat, tr(uid, "language"), kb)
        return

    if text.startswith("/balance"):
        try:
            res = tg("getMyStarBalance")
            amount = res.get("result", {}).get("amount", 0)
            if amount:
                send(chat, tr(uid, "balance", amount=amount))
            else:
                send(chat, tr(uid, "balance_empty"))
        except Exception:
            send(chat, tr(uid, "balance_err"))
        return

    if text.startswith("/transactions"):
        try:
            res = tg("getStarTransactions", {"offset": 0, "limit": 5})
            items = res.get("result", {}).get("transactions", [])
            if not items:
                send(chat, tr(uid, "transactions_empty"))
                return
            lines = ["🧾 <b>Recent transactions</b>\n"]
            for t in items:
                amount = t.get("amount", "?")
                date = t.get("date", 0)
                day = time.strftime("%Y-%m-%d", time.gmtime(date)) if date else "?"
                lines.append("• %s: <b>%s ⭐</b>" % (day, amount))
            send(chat, "\n".join(lines))
        except Exception:
            send(chat, tr(uid, "transactions_err"))
        return

    if text.startswith("/refund"):
        buyer = str(uid)
        with _lock:
            store = _load(STORE_PATH)
            items = store.get(buyer) or []
            if not items:
                send(chat, tr(uid, "refund_none"))
                return
            last = items[-1]
            try:
                res = tg("refundStarPayment", {
                    "user_id": int(buyer),
                    "telegram_payment_charge_id": last["c"],
                })
                if not res.get("ok"):
                    raise RuntimeError(res)
            except Exception:
                send(chat, tr(uid, "refund_err"))
                return
            items.pop()
            _save(STORE_PATH, store)
        send(chat, tr(uid, "refund_ok"))
        return

    if text:
        send(chat, tr(uid, "unknown"), open_kb(uid))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
