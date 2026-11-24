# fix_buttons.py — чиним вебхук, кнопки и меню Bloom
import json
import urllib.request
import urllib.error


def api(token, method, params=None):
    req = urllib.request.Request(
        "https://api.telegram.org/bot%s/%s" % (token, method),
        data=json.dumps(params or {}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return json.loads(e.read())
        except Exception:
            return {"ok": False, "description": str(e)}
    except Exception as e:
        return {"ok": False, "description": str(e)}


def clean(s):
    return s.strip().replace("<", "").replace(">", "").replace('"', "").replace("'", "")


print("=== Bloom · починка кнопок ===\n")
token = clean(input("1) Токен бота: "))
domain = clean(input("2) Домен Railway (без https://): "))
secret = clean(input("3) WEBHOOK_SECRET из Railway → Variables: "))
myid = clean(input("4) Твой Telegram ID для теста (можно пропустить, Enter): "))

domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
if ":" in domain:
    domain = domain.split(":")[0]
webapp = "https://" + domain
hook = webapp + "/api/telegram"

print("\n[1/5] Проверяю сервер…")
r = api(token, "getWebhookInfo")
print(json.dumps(r, ensure_ascii=False, indent=1))

print("\n[2/5] Ставлю вебхук с ПРАВИЛЬНЫМИ allowed_updates…")
r = api(token, "setWebhook", {
    "url": hook,
    "secret_token": secret,
    "allowed_updates": ["message", "callback_query", "pre_checkout_query"],
    "drop_pending_updates": True,
})
print(r)
if not r.get("ok"):
    print("👉 Если ошибка про secret/https — проверь домен и секрет.")

print("\n[3/5] Ставлю кнопку меню у поля ввода…")
r = api(token, "setChatMenuButton", {
    "menu_button": {"type": "web_app", "text": "🌸 Bloom", "web_app": {"url": webapp}}
})
print(r)

print("\n[4/5] Проверяю кнопку меню…")
r = api(token, "getChatMenuButton")
print(json.dumps(r, ensure_ascii=False, indent=1))

if myid:
    print("\n[5/5] Отправляю тебе тестовое сообщение с кнопками…")
    r = api(token, "sendMessage", {
        "chat_id": int(myid),
        "text": "Тест кнопок Bloom 🌸 Если видишь кнопки ниже — всё работает.",
        "reply_markup": {
            "inline_keyboard": [
                [{"text": "🌸 Открыть Bloom", "web_app": {"url": webapp}}],
                [{"text": "👑 Bloom Plus", "callback_data": "plus_menu"}],
            ]
        },
    })
    print(json.dumps(r, ensure_ascii=False, indent=1))
    if not r.get("ok"):
        print("👉 Пришли мне описание ошибки выше — по нему сразу поймём причину.")
else:
    print("\n[5/5] Тест пропущен.")

print("\nГотово. Теперь напиши боту /start заново.")
print("Если кнопки всё равно не видны — открой Railway → Deployments → View Logs,")
print("напиши боту /start и пришли строку, где есть 'webhook:' или 'ERROR'.")
input("\nEnter для выхода…")