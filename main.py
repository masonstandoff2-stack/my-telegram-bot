import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from telegram.ext import MessageHandler, filters

# Настройки бота
BOT_TOKEN = "8356262671:AAGMULNdJhuMQNJV-w8GTnf1SlqDetTYfKc"
CHANNEL_INVITE_LINK = "https://t.me/+cF3j8j5m4jBkMGEy"
CHANNEL_CHAT_ID = "-1003204433403"
CHANNEL_2_USERNAME = "@HataMasona"
CHANNEL_2_CHAT_ID = "-1002510814806"
CHANNEL_3_USERNAME = "@HolidollaModz"
CHANNEL_3_CHAT_ID = "-1002371853221"
SUPPORT_USERNAME = "@Mano_Masu"
APK_URL = "https://t.me/mammq123"

# Название файла
FILE_NAME = "Mansory Holidolla V2.0"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def get_main_keyboard():
    """Создает плавающую клавиатуру меню"""
    keyboard = [
        [InlineKeyboardButton("🎁 Получить APK", callback_data="get_apk")],
        [InlineKeyboardButton("📢 Наши каналы", callback_data="our_channels")],
        [InlineKeyboardButton("ℹ️ Помощь", callback_data="help_info")],
        [InlineKeyboardButton("💬 Поддержка", callback_data="support_info")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def check_subscriptions(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> dict:
    """Проверяет подписку на все каналы"""
    subscriptions = {}

    channels = [
        ("Основной канал", CHANNEL_CHAT_ID),
        (CHANNEL_2_USERNAME, CHANNEL_2_CHAT_ID),
        (CHANNEL_3_USERNAME, CHANNEL_3_CHAT_ID)
    ]

    for channel_name, channel_id in channels:
        try:
            chat_member = await context.bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            subscriptions[channel_name] = chat_member.status in ['member', 'administrator', 'creator']
        except Exception as e:
            logger.error(f"Ошибка при проверке канала {channel_name}: {e}")
            subscriptions[channel_name] = False

    return subscriptions


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    try:
        user = update.effective_user

        welcome_text = f"""
👋 <b>Добро пожаловать, {user.first_name}!</b>

🤖 <b>Mansory Holidolla</b> - премиум мод для вашего устройства!

⭐ <b>Преимущества:</b>
• 🚀 Улучшенная производительность
• 👑 Расширенные возможности  
• 🛡️ Стабильная работа
• 🎁 Эксклюзивные функции

💬 <b>Поддержка:</b> {SUPPORT_USERNAME}

👇 <b>Выберите действие из меню ниже:</b>
        """

        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка в команде /start: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    try:
        await update.message.reply_text(
            "👇 <b>Выберите действие из меню:</b>",
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий на инлайн-кнопки"""
    try:
        query = update.callback_query
        user_id = query.from_user.id

        await query.answer()

        if query.data == "get_apk":
            await query.edit_message_text("🔄 <b>Проверяем подписки...</b>", parse_mode='HTML')

            subscriptions = await check_subscriptions(user_id, context)
            all_subscribed = all(subscriptions.values())

            if all_subscribed:
                keyboard = [
                    [InlineKeyboardButton(f"📥 Скачать {FILE_NAME}", url=APK_URL)],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                success_text = f"""
✅ <b>Доступ открыт!</b>

🚀 <b>{FILE_NAME}</b> готов к скачиванию!

🎉 <b>Спасибо за подписку на все каналы!</b>

📥 Нажмите кнопку ниже для скачивания
                """

                await query.edit_message_text(
                    success_text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
            else:
                # Создаем кнопки "Подписаться" как на скриншоте
                keyboard = [
                    [InlineKeyboardButton("📢 Подписаться", url=CHANNEL_INVITE_LINK)],
                    [InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_2_USERNAME[1:]}")],
                    [InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_3_USERNAME[1:]}")],
                    [InlineKeyboardButton("✅ Я подписался", callback_data="get_apk")],
                    [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)

                await query.edit_message_text(
                    "❌ <b>Требуется подписка на все каналы!</b>\n\n"
                    "🔒 <b>Для получения доступа необходимо подписаться:</b>\n\n"
                    "📢 <b>Основной канал</b>\n"
                    "📢 <b>Hata Masona</b>\n"  
                    "📢 <b>Holidolla Modz</b>\n\n"
                    "📥 <b>Как получить доступ:</b>\n"
                    "1. Нажмите на кнопки 'Подписаться' ниже\n"
                    "2. Подпишитесь на ВСЕ каналы\n"
                    "3. Вернитесь и нажмите 'Я подписался'",
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )

        elif query.data == "our_channels":
            keyboard = [
                [InlineKeyboardButton("📢 Подписаться", url=CHANNEL_INVITE_LINK)],
                [InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_2_USERNAME[1:]}")],
                [InlineKeyboardButton("📢 Подписаться", url=f"https://t.me/{CHANNEL_3_USERNAME[1:]}")],
                [InlineKeyboardButton("🎁 Получить APK", callback_data="get_apk")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            channels_text = """
📢 <b>Наши каналы</b>

⭐ <b>Обязательные для подписки:</b>

📢 <b>Основной канал</b>
• Основные обновления
• Новости проекта

📢 <b>Hata Masona</b>
• Эксклюзивный контент
• Дополнительные материалы

📢 <b>Holidolla Modz</b>
• Эксклюзивный контент  
• Дополнительные материалы

⚠️ <i>Подпишитесь на ВСЕ каналы для доступа к APK</i>
            """

            await query.edit_message_text(
                channels_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

        elif query.data == "help_info":
            help_text = f"""
ℹ️ <b>Центр помощи</b>

📦 <b>Доступная версия:</b>
🚀 {FILE_NAME}

🔒 <b>Требования для доступа:</b>
📢 Подписка на каналы:
• Основной канал
• Hata Masona
• Holidolla Modz

💬 <b>Поддержка:</b> {SUPPORT_USERNAME}

⚠️ <b>Частые вопросы:</b>
• Не скачивается файл - проверьте интернет
• Не устанавливается - разрешите установку из неизвестных источников
• Не видит подписку - отпишитесь и подпишитесь заново
            """

            keyboard = [
                [InlineKeyboardButton("🎁 Получить APK", callback_data="get_apk")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.edit_message_text(
                help_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

        elif query.data == "support_info":
            keyboard = [
                [InlineKeyboardButton(f"💬 Написать в поддержку", url=f"https://t.me/{SUPPORT_USERNAME[1:]}")],
                [InlineKeyboardButton("🎁 Получить APK", callback_data="get_apk")],
                [InlineKeyboardButton("🔙 Назад", callback_data="back_to_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            support_text = f"""
💬 <b>Техническая поддержка</b>

🔥 <b>Служба поддержки:</b>
{SUPPORT_USERNAME}

⏰ <b>Режим работы:</b> 24/7

⚠️ <b>Перед обращением проверьте:</b>
• Подписку на все каналы
• Стабильность интернет-соединения  
• Достаточно места на устройстве
            """

            await query.edit_message_text(
                support_text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )

        elif query.data == "back_to_menu":
            await query.edit_message_text(
                "👇 <b>Выберите действие из меню:</b>",
                reply_markup=get_main_keyboard(),
                parse_mode='HTML'
            )

    except Exception as e:
        logger.error(f"Ошибка в обработчике кнопок: {e}")
        try:
            await query.edit_message_text(
                "❌ Произошла ошибка. Попробуйте еще раз.",
                reply_markup=get_main_keyboard()
            )
        except:
            pass


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /menu"""
    try:
        await update.message.reply_text(
            "👇 <b>Выберите действие из меню:</b>",
            reply_markup=get_main_keyboard(),
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"Ошибка в команде /menu: {e}")


def main():
    """Основная функция запуска бота"""
    try:
        application = Application.builder().token(BOT_TOKEN).build()

        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("menu", menu_command))
        application.add_handler(CommandHandler("help", menu_command))

        # Обработчики callback'ов
        application.add_handler(CallbackQueryHandler(button_handler))

        # Обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        print("🤖 Бот запущен и готов к работе!")
        print(f"📦 Файл: {FILE_NAME}")
        print(f"📢 Основной канал: {CHANNEL_INVITE_LINK}")
        print(f"📢 Дополнительные каналы: Hata Masona, Holidolla Modz")
        print(f"💬 Поддержка: {SUPPORT_USERNAME}")
        print("⚡ Бот работает...")

        application.run_polling()

    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")


if __name__ == "__main__":

    main()
