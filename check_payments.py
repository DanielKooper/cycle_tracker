# check_payments.py — точная диагностика оплаты Stars
import json
import urllib.request
import urllib.error


def call(url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {"ok": False, "description": str(e)}
    except Exception as e:
        return 0, {"ok": False, "description": str(e)}


def tg(token, method, payload=None):
    return call("https://api.telegram.org/bot%s/%s" % (token, method), payload or {})


def clean(s):
    return s.strip().replace("<", "").replace(">", "").strip('"').strip("'")


print("=== Bloom · диагностика оплаты ===\n")
token = clean(input("1) BOT_TOKEN (точно как в Railway → Variables): "))
domain = clean(input("2) Домен Railway (без https://): "))
domain = domain.replace("https://", "").replace("http://", "").rstrip("/")
if ":" in domain:
    domain = domain.split(":")[0]
base = "https://" + domain

print("\n[1/5] Кто владеет этим токеном?")
st, r = tg(token, "getMe")
if r.get("ok"):
    print("   ✅ Бот: @" + r["result"].get("username", "?") + "  (id " + str(r["result"]["id"]) + ")")
    print("   👉 Открывать Bloom нужно ИМЕННО из этого бота.")
else:
    print("   ❌ " + str(r.get("description")))
    print("   👉 Токен неверный/отозван. Обнови BOT_TOKEN в Railway.")

print("\n[2/5] Вебхук")
st, r = tg(token, "getWebhookInfo")
if r.get("ok"):
    i = r["result"]
    print("   URL: " + (i.get("url") or "—"))
    print("   Ошибка: " + str(i.get("last_error_message") or "нет"))
    print("   allowed_updates: " + str(i.get("allowed_updates")))

print("\n[3/5] ГЛАВНОЕ: пробую создать счёт на 1⭐ напрямую в Telegram")
st, r = tg(token, "createInvoiceLink", {
    "title": "Bloom test",
    "description": "Проверка создания счёта",
    "payload": "diag",
    "provider_token": "",
    "currency": "XTR",
    "prices": [{"label": "Test", "amount": 1}],
})
if r.get("ok"):
    print("   ✅ Telegram создаёт счета для этого бота — проблема на стороне сервера/подписи.")
else:
    print("   ❌ HTTP " + str(st) + " → " + str(r.get("description")))
    print("   👉 Пришли мне эту строку — она объясняет всё.")

print("\n[4/5] Есть ли эндпоинт /api/invoice на сервере?")
st, r = call(base + "/api/invoice", {"pack": "pdf", "initData": ""})
print("   HTTP " + str(st) + " → " + json.dumps(r, ensure_ascii=False))
if st == 404:
    print("   👉 На сервере СТАРЫЙ main.py. Задеплой новый.")
elif st == 401:
    print("   ✅ Эндпоинт на месте (401 без подписи — так и должно быть).")

print("\n[5/5] Последняя ошибка сервера")
st, r = call(base + "/api/lasterror")
print("   " + json.dumps(r, ensure_ascii=False))

print("\nГотово. Пришли мне вывод шагов [1/5], [3/5] и [4/5].")
input("\nEnter для выхода…")