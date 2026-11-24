# ══════════════════════════════════════════════
#  bot.py — Bloom 🌸  (WebApp + оплата Stars)
#  Запуск: python bot.py
# ══════════════════════════════════════════════
import base64
import json
import logging
import urllib.request
from datetime import datetime, timezone

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                          PreCheckoutQueryHandler, MessageHandler, ContextTypes, filters)

# ── ЗАПОЛНИ ЭТИ ДВЕ СТРОКИ ──
BOT_TOKEN = "5472255249:AAFVtNYCNgTDZ7GiiGOqh5NJpJKL7sasDa4"
WEBAPP_URL = "cycletracker-production-370cc7a4.up.railway.app"   # ссылка из Railway → Settings → Domains
# ────────────────────────────

STORE = "purchases.json"
PACKS = {
    "analytics": ("📊 Глубокая аналитика", "ПМС-окно, фазы цикла и разброс", 50),
    "care":      ("💞 Забота+", "Расширенные советы партнёру", 75),
    "pdf":       ("📥 PDF-отчёт", "Красивый отчёт для врача", 30),
    "all":       ("👑 Всё навсегда", "Все функции Bloom Plus", 149),
}

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("bloom")


def load_store():
    try:
        with open(STORE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_store(s):
    with open(STORE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)


def make_code(uid, pkg, charge):
    raw = json.dumps({"u": uid, "p": pkg, "c": charge}, separators=(",", ":")).encode()
    return "PLUS-" + base64.urlsafe_b64encode(raw).decode().rstrip("=")


def menu_text():
    lines = ["👑 <b>Bloom Plus</b> — необязательные дополнения за звёзды ⭐\n"]
    for name, desc, stars in PACKS.values():
        lines.append(f"{name} — <b>{stars} ⭐</b>\n<i>{desc}</i>")
    lines.append("\nБазовое приложение всегда бесплатно 💗")
    return "\n".join(lines)


def menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"{v[0]} · {v[2]}⭐", callback_data=f"buy_{k}")]
        for k, v in PACKS.items()
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0] == "plus":
        await update.message.reply_text(menu_text(), reply_markup=menu_kb(), parse_mode="HTML")
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌸 Открыть Bloom", web_app={"url": WEBAPP_URL})],
        [InlineKeyboardButton("👑 Bloom Plus · за ⭐", callback_data="plus_menu")],
    ])
    await update.message.reply_text(
        "Привет! Я <b>Bloom</b> 🌸\nТвой личный трекер цикла.\n\n"
        "Нажми кнопку ниже, чтобы открыть приложение 👇",
        reply_markup=kb, parse_mode="HTML")


async def plus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(menu_text(), reply_markup=menu_kb(), parse_mode="HTML")


async def plus_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.reply_text(menu_text(), reply_markup=menu_kb(), parse_mode="HTML")


async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    pkg = q.data.replace("buy_", "")
    if pkg not in PACKS:
        return
    name, desc, stars = PACKS[pkg]
    await q.message.reply_invoice(
        title=f"Bloom Plus: {name}",
        description=desc,
        payload=json.dumps({"p": pkg, "u": q.from_user.id}),
        provider_token="",                      # для Stars всегда пусто
        currency="XTR",                         # валюта — звёзды Telegram
        prices=[LabeledPrice(name, stars)],     # ЦЕЛЫЕ звёзды, без ×100!
    )


async def precheckout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.pre_checkout_query
    try:
        ok = json.loads(q.invoice_payload)["p"] in PACKS
    except Exception:
        ok = False
    await q.answer(ok=ok, error_message=None if ok else "Неизвестный товар 🤔")


async def success(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sp = update.message.successful_payment
    data = json.loads(sp.invoice_payload)
    uid, pkg = data["u"], data["p"]
    charge = sp.telegram_payment_charge_id
    store = load_store()
    store.setdefault(str(uid), []).append(
        {"p": pkg, "c": charge, "t": datetime.now(timezone.utc).isoformat()})
    save_store(store)
    code = make_code(uid, pkg, charge)
    log.info("PAY ok uid=%s pkg=%s stars=%s", uid, pkg, sp.total_amount)
    await update.message.reply_text(
        "✅ <b>Оплата получена!</b> Спасибо 💗\n\n"
        "Твой код активации (нажми на него — скопируется):\n"
        f"<code>{code}</code>\n\n"
        "📲 Вставь его в приложении:\n"
        "⚙️ <b>Настройки → Bloom Plus → Активировать</b>",
        parse_mode="HTML")


async def refund(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Возврат последней покупки — Telegram поддерживает возврат Stars."""
    uid = str(update.effective_user.id)
    store = load_store()
    items = store.get(uid) or []
    if not items:
        await update.message.reply_text("У тебя нет покупок для возврата 🤍")
        return
    last = items[-1]
    try:
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{BOT_TOKEN}/refundStarPayment",
            data=json.dumps({"user_id": int(uid),
                             "telegram_payment_charge_id": last["c"]}).encode(),
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            res = json.loads(r.read())
        if not res.get("ok"):
            raise RuntimeError(res)
    except Exception as e:
        log.error("refund fail: %s", e)
        await update.message.reply_text("Не удалось оформить возврат 😔 Попробуй позже.")
        return
    items.pop()
    save_store(store)
    await update.message.reply_text("✅ Возврат оформлен — звёзды вернулись на баланс ⭐")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("plus", plus_cmd))
    app.add_handler(CommandHandler("refund", refund))
    app.add_handler(CallbackQueryHandler(plus_menu, pattern="^plus_menu$"))
    app.add_handler(CallbackQueryHandler(buy, pattern="^buy_"))
    app.add_handler(PreCheckoutQueryHandler(precheckout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, success))
    print("✅ Bloom-бот запущен! Платежи Stars активны ⭐")
    app.run_polling()


if __name__ == "__main__":
    main()
