# webhook.py — включение вебхука Bloom (запускать на своём компьютере)
import json
import urllib.request
import urllib.error


def api(token, method, params=None):
    url = "https://api.telegram.org/bot%s/%s" % (token, method)
    data = json.dumps(params).encode() if params is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
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


HINTS = [
    ("https url expected", "Адрес должен начинаться с https:// и быть без порта"),
    ("failed to resolve host", "Домен не найден — скопируй его из Railway → Settings → Networking"),
    ("ports", "Убери порт из адреса, нужен просто https://домен"),
    ("404", "На сервере нет /api/telegram — задеплой новый main.py"),
    ("403", "Секрет не совпадает с WEBHOOK_SECRET в Railway → Variables"),
    ("500", "Ошибка внутри сервера — открой Railway → Deployments → View logs"),
    ("ssl", "Проблема сертификата — используй домен вида *.up.railway.app"),
    ("wrong response", "Сервер ответил не то — проверь, что деплой свежий и приложение не крашится"),
]


def explain(desc):
    d = (desc or "").lower()
    for key, hint in HINTS:
        if key in d:
            print("   👉 " + hint)
            return
    print("   👉 Открой Railway → Deployments → View logs и пришли мне текст ошибки")


print("=== Bloom · включение вебхука ===\n")
token = clean(input("1) Токен бота от BotFather: "))
domain = clean(input("2) Домен Railway (например cycle.up.railway.app): "))
secret = clean(input("3) WEBHOOK_SECRET (точно как в Railway → Variables): "))

domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
if ":" in domain:
    domain = domain.split(":")[0]
hook_url = "https://%s/api/telegram" % domain

print("\nАдрес вебхука: " + hook_url)

print("\n[1/4] Проверяю сервер…")
try:
    with urllib.request.urlopen("https://%s/api/me" % domain, timeout=20) as r:
        print("   Сервер отвечает: %s" % r.status)
except urllib.error.HTTPError as e:
    if e.code == 401:
        print("   ✅ Новый main.py на месте (401 без авторизации — так и должно быть)")
    elif e.code == 404:
        print("   ❌ 404 — на сервере СТАРЫЙ main.py. Закоммить новый и дождаться деплоя.")
    else:
        print("   ⚠️ Ответ сервера: %s" % e.code)
except Exception as e:
    print("   ❌ Сервер недоступен: %s" % e)
    print("   👉 Проверь, что деплой в Railway зелёный и домен сгенерирован")

print("\n[2/4] Снимаю старый вебхук…")
r = api(token, "deleteWebhook", {"drop_pending_updates": True})
print("   " + ("ok" if r.get("ok") else str(r.get("description"))))

print("\n[3/4] Ставлю новый вебхук…")
r = api(token, "setWebhook", {
    "url": hook_url,
    "secret_token": secret,
    "allowed_updates": ["message", "pre_checkout_query"],
    "drop_pending_updates": True,
})
if r.get("ok"):
    print("   ✅ Вебхук установлен")
else:
    print("   ❌ " + str(r.get("description")))
    explain(r.get("description"))

print("\n[4/4] Проверяю статус…")
r = api(token, "getWebhookInfo")
if r.get("ok"):
    info = r["result"]
    print("   URL: " + (info.get("url") or "—"))
    print("   Ожидают обработки: %s" % info.get("pending_update_count"))
    err = info.get("last_error_message")
    if err:
        print("   ⚠️ Последняя ошибка: " + err)
        explain(err)
    else:
        print("   ✅ Ошибок нет — всё работает!")
else:
    print("   ❌ " + str(r.get("description")))

print("\nГотово. Останови локальный bot.py (Ctrl+C) и напиши боту /start 🌸")
input("\nНажми Enter, чтобы закрыть окно…")