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

# Старые/альтернативные имена товаров → текущие ключи.
# Спасает, если фронтенд из кэша шлёт прежние идентификаторы.
PACK_ALIAS = {
    "stats": "analytics", "premium_stats": "analytics",
    "ai": "analytics", "premium_ai": "analytics",
    "partners": "care", "premium_partners": "care",
    "export": "pdf", "premium_export": "pdf",
    "plus": "all", "premium_all": "all", "everything": "all",
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
        LAST_ERROR["description"] = "AUTH: не удалось разобрать initData: %s" % e
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
    url = WEBAPP_URL
    if not url:
        url = request.headers.get("X-Forwarded-Host") or request.host
    url = url.strip().rstrip("/")
    if url.startswith("http://"):
        url = "https://" + url[len("http://"):]
    elif not url.startswith("https://"):
        url = "https://" + url
    return url


def open_kb(uid):
    rows = [
        [{"text": tr(uid, "open"), "web_app": {"url": app_url_from_request()}}],
        [{"text": tr(uid, "plus_btn"), "callback_data": "plus_menu"}],
    ]
    if CHANNEL_URL.startswith("https://t.me/") or CHANNEL_URL.startswith("https://telegram.me/"):
        rows.append([{"text": tr(uid, "channel_btn"), "url": CHANNEL_URL}])
    elif CHANNEL_URL:
        app.logger.error("CHANNEL_URL invalid, skipped: %s", CHANNEL_URL)
    return {"inline_keyboard": rows}


@app.get("/")
def index():
    return send_from_directory("webapp", "index.html")


@app.get("/<path:p>")
def statics(p):
    if p.startswith("api/"):
        abort(404)
    return send_from_directory("webapp", p)


@app.after_request
def no_cache(resp):
    p = request.path
    if p == "/" or p.endswith(".html") or p.endswith(".js") or p.endswith(".css"):
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
    return resp


@app.post("/api/invoice")
def api_invoice():
    body = request.get_json(silent=True) or {}
    user = verify(body.get("initData", ""))
    if not user:
        return jsonify(ok=False, error="auth", detail=LAST_ERROR["description"]), 401

    raw = str(body.get("pack") or "").strip()
    key = PACK_ALIAS.get(raw, raw)
    pack = PACKS.get(key)
    if not pack:
        known = ", ".join(sorted(PACKS))
        app.logger.error("Unknown pack '%s' — server knows: %s", raw, known)
        detail = ("Приложение прислало товар «%s», сервер знает только: %s. "
                  "Закрой и открой приложение заново (сброс кэша)." % (raw or "пусто", known))
        return jsonify(ok=False, error="pack", got=raw, have=sorted(PACKS), detail=detail), 400

    res = tg("createInvoiceLink", {
        "title": "Bloom Plus · " + pack["title"],
        "description": pack["desc"],
        "payload": json.dumps({"p": key, "u": user["id"]}, separators=(",", ":")),
        "provider_token": "",
        "currency": "XTR",
        "prices": [{"label": pack["title"], "amount": pack["stars"]}],
    })
    if not res.get("ok"):
        return jsonify(ok=False, error="telegram", detail=res.get("description")), 502
    return jsonify(ok=True, link=res["result"], stars=pack["stars"])


@app.get("/api/me")
def api_me():
    user = verify(request.args.get("initData", ""))
    if not user:
        return jsonify(ok=False, error="auth", detail=LAST_ERROR["description"]), 401
    with _lock:
        store = _load(STORE_PATH)
    packs = sorted({i["p"] for i in store.get(str(user["id"]), [])})
    return jsonify(ok=True, packs=packs, lang=get_lang(user["id"]))


@app.get("/api/config")
def api_config():
    return jsonify(ok=True, channel=CHANNEL_URL)


@app.get("/api/lasterror")
def api_lasterror():
    return jsonify(ok=True, last_error=LAST_ERROR)


@app.get("/api/whoami")
def api_whoami():
    res = tg("getMe")
    if res.get("ok"):
        return jsonify(ok=True, username=res["result"].get("username"), id=res["result"].get("id"))
    return jsonify(ok=False, detail=res.get("description"))


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
    res = tg("sendMessage", payload)
    if not res.get("ok"):
        app.logger.error("sendMessage rejected: %s", res.get("description"))
    return res


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
            set_lang(uid, data.replace("lang_", ""))
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
            store.setdefault(buyer, []).append(
                {"p": key, "c": sp["telegram_payment_charge_id"], "t": int(time.time())})
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
        res = tg("getMyStarBalance")
        if res.get("ok"):
            amount = res.get("result", {}).get("amount", 0)
            send(chat, tr(uid, "balance", amount=amount) if amount else tr(uid, "balance_empty"))
        else:
            send(chat, tr(uid, "balance_err"))
        return
    if text.startswith("/transactions"):
        res = tg("getStarTransactions", {"offset": 0, "limit": 5})
        if not res.get("ok"):
            send(chat, tr(uid, "transactions_err"))
            return
        items = res.get("result", {}).get("transactions", [])
        if not items:
            send(chat, tr(uid, "transactions_empty"))
            return
        lines = ["🧾 <b>Recent transactions</b>\n"]
        for t in items:
            date = t.get("date", 0)
            day = time.strftime("%Y-%m-%d", time.gmtime(date)) if date else "?"
            lines.append("• %s: <b>%s ⭐</b>" % (day, t.get("amount", "?")))
        send(chat, "\n".join(lines))
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
            res = tg("refundStarPayment", {"user_id": int(buyer), "telegram_payment_charge_id": last["c"]})
            if not res.get("ok"):
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