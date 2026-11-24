# setup_bot.py — описание, команды и кнопка меню Bloom
import json
import urllib.request
import urllib.error


def api(token, method, params):
    req = urllib.request.Request(
        "https://api.telegram.org/bot%s/%s" % (token, method),
        data=json.dumps(params).encode(),
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
    return s.strip().replace("<", "").replace(">", "")


print("=== Bloom · настройка бота ===\n")
token = clean(input("Токен бота: "))
webapp = clean(input("Ссылка WebApp (https://...up.railway.app): ")).rstrip("/")

DESCRIPTIONS = {
    "ru": (
        "Bloom 🌸 — приватный трекер цикла и заботы.\n\n"
        "• Календарь, прогнозы и фазы цикла\n"
        "• Советы по самочувствию\n"
        "• Режим заботы для партнёра\n"
        "• Данные только на твоём устройстве\n"
        "• Plus за Telegram Stars ⭐\n\n"
        "Открой приложение и начни с последней менструации.\n"
        "Bloom не заменяет консультацию врача."
    ),
    "en": (
        "Bloom 🌸 — a private cycle and care tracker.\n\n"
        "• Calendar, predictions and cycle phases\n"
        "• Well-being tips\n"
        "• Partner care mode\n"
        "• Data stays on your device\n"
        "• Plus with Telegram Stars ⭐\n\n"
        "Open the app and start with your last period.\n"
        "Bloom is not a substitute for medical advice."
    ),
    "uk": (
        "Bloom 🌸 — приватний трекер циклу та турботи.\n\n"
        "• Календар, прогнози та фази циклу\n"
        "• Поради щодо самопочуття\n"
        "• Режим турботи для партнера\n"
        "• Дані лише на твоєму пристрої\n"
        "• Plus за Telegram Stars ⭐\n\n"
        "Відкрий застосунок і почни з останньої менструації.\n"
        "Bloom не замінює консультацію лікаря."
    ),
}

SHORT = {
    "ru": "Bloom 🌸 — трекер цикла, прогнозы и режим заботы для партнёра. Приватно и красиво.",
    "en": "Bloom 🌸 — cycle tracker, predictions and partner care mode. Private and beautiful.",
    "uk": "Bloom 🌸 — трекер циклу, прогнози та режим турботи для партнера. Приватно й красиво.",
}

COMMANDS = {
    "ru": [
        {"command": "start", "description": "Открыть приложение"},
        {"command": "plus", "description": "Дополнения за звёзды"},
        {"command": "care", "description": "Советы партнёру"},
        {"command": "balance", "description": "Баланс звёзд бота"},
        {"command": "transactions", "description": "Последние операции"},
        {"command": "refund", "description": "Возврат последней покупки"},
        {"command": "language", "description": "Язык бота"},
        {"command": "privacy", "description": "Приватность"},
        {"command": "help", "description": "Все команды"},
    ],
    "en": [
        {"command": "start", "description": "Open the app"},
        {"command": "plus", "description": "Star upgrades"},
        {"command": "care", "description": "Partner support tips"},
        {"command": "balance", "description": "Bot Stars balance"},
        {"command": "transactions", "description": "Recent transactions"},
        {"command": "refund", "description": "Refund last purchase"},
        {"command": "language", "description": "Bot language"},
        {"command": "privacy", "description": "Privacy"},
        {"command": "help", "description": "All commands"},
    ],
    "uk": [
        {"command": "start", "description": "Відкрити застосунок"},
        {"command": "plus", "description": "Доповнення за зірки"},
        {"command": "care", "description": "Поради партнеру"},
        {"command": "balance", "description": "Баланс зірок бота"},
        {"command": "transactions", "description": "Останні операції"},
        {"command": "refund", "description": "Повернення покупки"},
        {"command": "language", "description": "Мова бота"},
        {"command": "privacy", "description": "Приватність"},
        {"command": "help", "description": "Усі команди"},
    ],
}

for lang in ["ru", "en", "uk"]:
    print("\n语言:", lang)
    r = api(token, "setMyDescription", {"description": DESCRIPTIONS[lang], "language_code": lang})
    print("description:", r.get("ok"), r.get("description", ""))
    r = api(token, "setMyShortDescription", {"short_description": SHORT[lang], "language_code": lang})
    print("short:", r.get("ok"), r.get("description", ""))
    r = api(token, "setMyCommands", {"commands": COMMANDS[lang], "language_code": lang})
    print("commands:", r.get("ok"), r.get("description", ""))

r = api(token, "setMyCommands", {"commands": COMMANDS["ru"]})
print("default commands:", r.get("ok"), r.get("description", ""))

r = api(token, "setChatMenuButton", {
    "menu_button": {
        "type": "web_app",
        "text": "🌸 Bloom",
        "web_app": {"url": webapp},
    }
})
print("menu button:", r.get("ok"), r.get("description", ""))

print("\nГотово. Если лого ещё нет: @BotFather → /mybots → твой бот → Edit Bot → Edit Botpic.")
input("\nEnter для выхода…")
