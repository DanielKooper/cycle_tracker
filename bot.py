# cycle_tracker/bot.py - добавить обработчики платежей

from telegram import Update, LabeledPrice, ShippingOption
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, PreCheckoutQueryHandler, MessageHandler, filters

# ... существующий код ...

async def premium_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню премиум функций"""
    keyboard = [
        [InlineKeyboardButton("📊 Расширенная статистика - 50⭐", callback_data="premium_stats")],
        [InlineKeyboardButton("👥 Циклы партнёров - 100⭐", callback_data="premium_partners")],
        [InlineKeyboardButton("🤖 AI прогнозы - 75⭐", callback_data="premium_ai")],
        [InlineKeyboardButton("📥 Экспорт данных - 30⭐", callback_data="premium_export")],
        [InlineKeyboardButton("💎 ВСЁ включено - 200⭐", callback_data="premium_all")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⭐ <b>Премиум функции</b>\n\n"
        "Выберите пакет для разблокировки:",
        reply_markup=reply_markup,
        parse_mode='HTML'
    )

async def handle_premium_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора премиум пакета"""
    query = update.callback_query
    await query.answer()
    
    package_prices = {
        'premium_stats': {'name': 'Расширенная статистика', 'price': 50},
        'premium_partners': {'name': 'Циклы партнёров', 'price': 100},
        'premium_ai': {'name': 'AI прогнозы', 'price': 75},
        'premium_export': {'name': 'Экспорт данных', 'price': 30},
        'premium_all': {'name': 'Все функции', 'price': 200}
    }
    
    package = query.data
    if package in package_prices:
        info = package_prices[package]
        
        # Создаём инвойс для Telegram Stars
        prices = [LabeledPrice(label=info['name'], amount=info['price'] * 100)]
        
        await query.message.reply_invoice(
            title=f"Премиум: {info['name']}",
            description=f"Разблокировка функции '{info['name']}' за {info['price']} звёзд",
            payload=json.dumps({
                'type': 'premium',
                'package': package,
                'user_id': query.from_user.id
            }),
            currency='XTR',  # Telegram Stars
            prices=prices
        )

async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка предварительной проверки платежа"""
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка успешного платежа"""
    from database import Session, get_user_by_telegram_id
    
    payment = update.message.successful_payment
    payload = json.loads(payment.invoice_payload)
    
    # Активируем премиум для пользователя
    with Session() as session:
        user = get_user_by_telegram_id(session, update.effective_user.id)
        if user:
            # Здесь должна быть логика активации премиума в БД
            # Например, добавить запись в таблицу premium_subscriptions
            pass
    
    await update.message.reply_text(
        "✅ <b>Оплата прошла успешно!</b>\n\n"
        "Премиум функции теперь доступны в WebApp.\n"
        "Перезагрузите приложение для применения изменений.",
        parse_mode='HTML'
    )

def main():
    """Запуск бота"""
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # Существующие handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(help_callback, pattern="^help$"))
    application.add_handler(CallbackQueryHandler(show_my_code, pattern="^my_code$"))
    application.add_handler(CommandHandler("code", show_my_code))
    application.add_handler(CommandHandler("add_partner", handle_partner_code))
    
    # Новые handlers для премиум
    application.add_handler(CommandHandler("premium", premium_menu))
    application.add_handler(CallbackQueryHandler(handle_premium_selection, pattern="^premium_"))
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))
    
    logger.info("Бот запущен!")
    application.run_polling()