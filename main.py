# ══════════════════════════════════════════════════════════════
#  main.py — Bloom 🌸  сервер: WebApp + покупки Stars внутри приложения
#  Railway Start Command:  gunicorn -w 1 -b 0.0.0.0:$PORT main:app
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
DATA_DIR    = os.environ.get("DATA_DIR", ".")
STORE_PATH  = os.path.join(DATA_DIR, "purchases.json")

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

app = Flask(__name__, static_folder="webapp", static_url_path="")
_lock = threading.Lock()


# ── хранилище покупок ──
def _load():
    try:
        with open(STORE_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save(d):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = STORE_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False)
    os.replace(tmp, STORE_PATH)


# ── Bot API ──
def tg(method, payload):
    req = urllib.request.Request(
        "https://api.telegram.org/bot%s/%s" % (BOT_TOKEN, method),
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read())


# ── проверка подписи Telegram WebApp initData ──
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


# ── статика WebApp ──
@app.get("/")
def index():
    return send_from_directory("webapp", "index.html")


@app.get("/<path:p>")
def statics(p):
    if p.startswith("api/"):
        abort(404)
    return send_from_directory("webapp", p)


# ── создание счёта для оплаты внутри WebApp ──
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


# ── купленные пакеты пользователя ──
@app.get("/api/me")
def api_me():
    user = verify(request.args.get("initData", ""))
    if not user:
        return jsonify(ok=False, error="auth"), 401
    with _lock:
        store = _load()
    packs = sorted({i["p"] for i in store.get(str(user["id"]), [])})
    return jsonify(ok=True, packs=packs)


# ── вебхук Telegram: платежи и команды ──
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


def handle_update(u):
    # 1. подтверждение платежа (нужно ответить быстро)
    if "pre_checkout_query" in u:
        q = u["pre_checkout_query"]
        ok = False
        try:
            ok = json.loads(q["invoice_payload"])["p"] in PACKS
        except Exception:
            ok = False
        tg("answerPreCheckoutQuery", {
            "pre_checkout_query_id": q["id"], "ok": ok,
            **({} if ok else {"error_message": "Неизвестный товар 🤔"}),
        })
        return

    msg = u.get("message") or {}
    if not msg:
        return
    chat = msg["chat"]["id"]

    # 2. успешная оплата
    if "successful_payment" in msg:
        sp = msg["successful_payment"]
        data = json.loads(sp["invoice_payload"])
        uid, key = str(data["u"]), data["p"]
        with _lock:
            store = _load()
            store.setdefault(uid, []).append({
                "p": key,
                "c": sp["telegram_payment_charge_id"],
                "t": int(time.time()),
            })
            _save(store)
        pack = PACKS.get(key, {})
        tg("sendMessage", {
            "chat_id": chat,
            "text": "✅ <b>Оплата получена!</b> Спасибо 💗\n\n"
                    "%s <b>%s</b> уже открыт в приложении — вернись в Bloom и пользуйся 👑"
                    % (pack.get("emoji", "👑"), pack.get("title", "Bloom Plus")),
            "parse_mode": "HTML",
        })
        return

    text = (msg.get("text") or "").strip()

    # 3. возврат последней покупки
    if text.startswith("/refund"):
        uid = str(msg["from"]["id"])
        with _lock:
            store = _load()
            items = store.get(uid) or []
            if not items:
                tg("sendMessage", {"chat_id": chat, "text": "У тебя нет покупок для возврата 🤍"})
                return
            last = items[-1]
            try:
                res = tg("refundStarPayment", {
                    "user_id": int(uid),
                    "telegram_payment_charge_id": last["c"],
                })
                if not res.get("ok"):
                    raise RuntimeError(res)
            except Exception:
                tg("sendMessage", {"chat_id": chat, "text": "Не удалось оформить возврат 😔 Попробуй позже."})
                return
            items.pop()
            _save(store)
        tg("sendMessage", {"chat_id": chat, "text": "✅ Возврат оформлен — звёзды вернулись на баланс ⭐"})
        return

    # 4. каталог Plus
    if text.startswith("/plus"):
        lines = ["👑 <b>Bloom Plus</b> — дополнения за звёзды ⭐\n"]
        for p in PACKS.values():
            lines.append("%s <b>%s</b> — %s ⭐\n<i>%s</i>" % (p["emoji"], p["title"], p["stars"], p["desc"]))
        lines.append("\nПокупка в один тап прямо в приложении 👇")
        tg("sendMessage", {
            "chat_id": chat, "text": "\n".join(lines), "parse_mode": "HTML",
            "reply_markup": {"inline_keyboard": [[
                {"text": "🌸 Открыть Bloom", "web_app": {"url": WEBAPP_URL}}]]},
        })
        return

    # 5. старт
    if text.startswith("/start"):
        tg("sendMessage", {
            "chat_id": chat,
            "text": "Привет! Я <b>Bloom</b> 🌸\nТвой личный трекер цикла.\n\n"
                    "Все данные хранятся только на твоём устройстве.\n"
                    "Нажми кнопку ниже, чтобы открыть приложение 👇",
            "parse_mode": "HTML",
            "reply_markup": {"inline_keyboard": [
                [{"text": "🌸 Открыть Bloom", "web_app": {"url": WEBAPP_URL}}],
                [{"text": "👑 Bloom Plus · за ⭐", "callback_data": "noop"}],
            ]},
        })
        return


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
