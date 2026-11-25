# content_bot.py — бот автопостинга контента в канал
import os
import json
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler, filters
)
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from content_library import POSTS, WEEKLY_SCHEDULE, POST_TIMES

# ═══════════ НАСТРОЙКИ ═══════════
BOT_TOKEN = os.environ.get("CONTENT_BOT_TOKEN", "5472255249:AAEeOOaIiEDS88EUPMjuN_A9kmn5A8TvO7w")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@bloomcalendar")
ADMIN_IDS = set(map(int, os.environ.get("ADMIN_IDS", "632982978").split(",")))

STATE_FILE = "content_bot_state.json"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("content_bot")

# ═══════════ СОСТОЯНИЕ ═══════════
def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "published": [],
            "paused": False,
            "stats": {"posts": 0, "polls": 0}
        }

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

state = load_state()

# ═══════════ ПОИСК КОНТЕНТА ═══════════
def get_next_post(category=None):
    """Находит следующий неопубликованный пост (с учётом категории)."""
    published = set(state["published"])
    for post in POSTS:
        if post["id"] in published:
            continue
        if category and post["category"] != category:
            continue
        return post
    return None

def mark_published(post_id):
    state["published"].append(post_id)
    state["stats"]["posts"] += 1
    save_state(state)

def get_category_for_today():
    """Возвращает категорию на сегодня по расписанию."""
    today = datetime.now().weekday()  # 0=Пн
    categories = WEEKLY_SCHEDULE.get(today, ["education"])
    return categories[0] if categories else "education"

# ═══════════ ОТПРАВКА В КАНАЛ ═══════════
async def send_to_channel(context: ContextTypes.DEFAULT_TYPE, post=None):
    """Основная функция отправки поста в канал."""
    if state["paused"]:
        logger.info("⏸ Пауза включена, пост пропущен.")
        return

    category = get_category_for_today()
    post = post or get_next_post(category)

    if not post:
        logger.info("ℹ️ Контент для категории '%s' закончился.", category)
        return

    chat_id = CHANNEL_ID

    try:
        # Опрос
        if post.get("type") == "poll":
            await context.bot.send_poll(
                chat_id=chat_id,
                question=post["question"],
                options=post["options"],
                is_anonymous=False,
                allows_multiple_answers=False,
            )
            state["stats"]["polls"] += 1
            mark_published(post["id"])
            logger.info("✅ Опрос опубликован: %s", post["question"][:50])
            return

        # Обычный пост с кнопками
        text = post.get("text", "")
        title = post.get("title", "")
        full_text = f"<b>{title}</b>\n\n{text}" if title else text

        keyboard = None
        if post.get("buttons"):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(b["text"], url=b["url"])]
                for b in post["buttons"]
            ])

        await context.bot.send_message(
            chat_id=chat_id,
            text=full_text,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )
        mark_published(post["id"])
        logger.info("✅ Пост опубликован: %s", post["id"])

    except Exception as e:
        logger.error("❌ Ошибка отправки поста %s: %s", post.get("id"), e)

# ═══════════ АДМИН-КОМАНДЫ ═══════════
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Доступ только для администраторов.")
        return
    await update.message.reply_text(
        "🤖 <b>Контент-бот Bloom</b>\n\n"
        "Команды:\n"
        "/publish — опубликовать следующий пост сейчас\n"
        "/schedule — показать расписание на сегодня\n"
        "/stats — статистика публикаций\n"
        "/pause — приостановить автопостинг\n"
        "/resume — возобновить автопостинг\n"
        "/preview — показать следующий пост без отправки",
        parse_mode="HTML"
    )

async def cmd_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    await send_to_channel(context)
    await update.message.reply_text("✅ Публикация запущена. Проверь канал.")

async def cmd_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    today = datetime.now()
    weekday = today.weekday()
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    text = f"📅 <b>Расписание на сегодня ({days[weekday]})</b>\n\n"
    text += f"Категория: <b>{get_category_for_today()}</b>\n"
    text += f"Время публикаций: {', '.join(POST_TIMES)}\n\n"

    # Показать следующий пост
    next_post = get_next_post(get_category_for_today())
    if next_post:
        text += f"Следующий пост: <b>{next_post['id']}</b>\n"
        text += f"Категория: {next_post['category']}\n"
        if next_post.get("title"):
            text += f"Заголовок: {next_post['title']}"
    else:
        text += "⚠️ Контент закончился."

    await update.message.reply_text(text, parse_mode="HTML")

async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    s = state["stats"]
    total = len(POSTS)
    published = len(state["published"])
    text = (
        f"📊 <b>Статистика</b>\n\n"
        f"Всего постов в библиотеке: {total}\n"
        f"Опубликовано: {published}\n"
        f"Осталось: {total - published}\n"
        f"Опросов опубликовано: {s['polls']}\n\n"
        f"Статус: {'⏸ Пауза' if state['paused'] else '▶️ Работает'}"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def cmd_pause(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    state["paused"] = True
    save_state(state)
    await update.message.reply_text("⏸ Автопостинг приостановлен. /resume — возобновить.")

async def cmd_resume(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    state["paused"] = False
    save_state(state)
    await update.message.reply_text("▶️ Автопостинг возобновлён.")

async def cmd_preview(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    post = get_next_post(get_category_for_today())
    if not post:
        await update.message.reply_text("⚠️ Контент закончился.")
        return
    text = post.get("text", "")
    title = post.get("title", "")
    full = f"<b>{title}</b>\n\n{text}" if title else text
    if post.get("type") == "poll":
        full = f"📊 Опрос: {post['question']}\nВарианты: {', '.join(post['options'])}"
    await update.message.reply_text(
        f"👀 Предпросмотр следующего поста ({post['id']}):\n\n{full}",
        parse_mode="HTML"
    )

# ═══════════ ЗАПУСК ═══════════
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Админ-команды
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("publish", cmd_publish))
    app.add_handler(CommandHandler("schedule", cmd_schedule))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("pause", cmd_pause))
    app.add_handler(CommandHandler("resume", cmd_resume))
    app.add_handler(CommandHandler("preview", cmd_preview))

    # Планировщик
    scheduler = AsyncIOScheduler()

    # Публикация в 09:00, 14:00, 20:00 каждый день
    for post_time in POST_TIMES:
        hour, minute = map(int, post_time.split(":"))
        scheduler.add_job(
            send_to_channel,
            trigger=CronTrigger(hour=hour, minute=minute),
            args=[app],
            id=f"post_{post_time.replace(':', '_')}",
            replace_existing=True,
        )

    scheduler.start()
    logger.info("🚀 Контент-бот запущен. Расписание: %s", POST_TIMES)

    app.run_polling()

if __name__ == "__main__":
    main()