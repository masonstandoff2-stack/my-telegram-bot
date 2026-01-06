import telebot
from telebot import types
from datetime import datetime

# токен
bot = telebot.TeleBot("8062397299:AAG8BeqkWMCHu081iWJ9-F_9Sx4U2GD8dak")

# id основного админа (ты)
MAIN_ADMIN_ID = 8281448580

# Список админов (добавляй сюда ID друзей)
admins = [5012040224, 8281448580]

# id чата tg в котором work
WORK_CHAT_ID = -1003503164893

data = {}
user_data = {}
collecting_info = False
list_message_id = None
pinned_message_id = None

# Словарь городов
city_mapping = {
    "Норильск": "🎁 Норильск ",
    "Череповец": "👮‍♂Череповец ",
    "Магадан": "🐀Магадан ",
    "Подольск": "🏰 ᴘᴏᴅᴏʟsᴋ ",
    "Сургут": "🏙 sᴜʀɢᴜᴛ ",
    "Ижевск": "🏍 ɪᴢʜᴇᴠsᴋ ",
    "Томск": "🎄 ᴛᴏᴍsᴋ ",
    "Тверь": "🐿 ᴛᴠᴇʀ ",
    "Вологда": "🐦‍🔥 ᴠᴏʟᴏɢᴅᴀ ",
    "Таганрог": "🦁 ᴛᴀɢᴀɴʀᴏɢ ",
    "Новгород": "🌼 ɴᴏᴠɢᴏʀᴏᴅ ",
    "Калуга": "🫐 ᴋᴀʟᴜɢᴀ ",
    "Владимир": "😹 ᴠʟᴀᴅɪᴍɪʀ ",
    "Кострома": "🐲 ᴋᴏsᴛʀᴏᴍᴀ ",
    "Чита": "🦎 ᴄʜɪᴛᴀ ",
    "Астрахань": "🧣 ᴀsᴛʀᴀᴋʜᴀɴ ",
    "Братск": "👜 ʙʀᴀᴛsᴋ ",
    "Тамбов": "🥐 ᴛᴀᴍʙᴏᴡ ",
    "Якутск": "🥽 ʏᴀᴋᴜᴛsᴋ ",
    "Ульяна": "🍭 ᴜʟʏᴀɴᴏᴠsᴋ ",
    "Липецк": "🎈 ʟɪᴘᴇᴛsᴋ ",
    "Барнаул": "💦 ʙᴀʀɴᴀᴜʟ ",
    "Яро": "🏛 ʏᴀʀᴏsʟᴀᴠʟ ",
    "Орел": "🦅 ᴏʀᴇʟ ",
    "Брянск": "🧸 ʙʀʏᴀɴsᴋ ",
    "Псков": "🪭 ᴘsᴋᴏᴡ ",
    "Смола": "🫚 sᴍᴏʟᴇɴsᴋ ",
    "Ставрополь": "🪼 sᴛᴀᴠʀᴏᴘᴏʟ ",
    "Иваново": "🪅 ɪᴠᴀɴᴏᴠᴏ ",
    "Тольятти": "🪸 ᴛᴏʟʏᴀᴛᴛɪ ",
    "Тюмень": "🐋 ᴛʏᴜᴍᴇɴ ",
    "Кемерово": "🌺 ᴋᴇᴍᴇʀᴏᴠᴏ ",
    "Киров": "🔫 ᴋɪʀᴏᴠ ",
    "Орена": "🍖 ᴏʀᴇɴʙᴜʀɢ ",
    "Арха": "🥋 ᴀʀᴋʜᴀɴɢᴇʟsᴋ ",
    "Курск": "🃏 ᴋᴜʀsᴋ ",
    "Мурма": "🎳 ᴍᴜʀᴍᴀɴsᴋ ",
    "Пенза": "🎷 ᴘᴇɴᴢᴀ ",
    "Рязань": "🎭 ʀʏᴀᴢᴀɴ ",
    "Тула": "⛳ ᴛᴜʟᴀ ",
    "Пермь": "🏟 ᴘᴇʀᴍ ",
    "Хаба": "🐨 ᴋʜᴀʙᴀʀᴏᴠsᴋ ",
    "Чебы": "🪄 ᴄʜᴇʙᴏᴋsᴀʀ ",
    "Красно": "🖇 ᴋʀᴀsɴᴏʏᴀʀsᴋ ",
    "Челяба": "🕊 ᴄʜᴇʟʏᴀʙɪɴsᴋ ",
    "Калина": "👒 ᴋᴀʟɪɴɪɴɢʀᴀᴅ ",
    "Восток": "🧶 ᴠʟᴀᴅɪᴠᴏsᴛᴏᴋ ",
    "Кавказ": "🌂 ᴠʟᴀᴅɪᴋᴀᴠᴋᴀᴢ ",
    "Махачкала": "⛑️ ᴍᴀᴋʜᴀᴄʜᴋᴀʟᴀ ",
    "Белга": "🎓 ʙᴇʟɢᴏʀᴏᴅ ",
    "Воронеж": "👑 ᴠᴏʀᴏɴᴇᴢʜ ",
    "Волгоград": "🎒 ᴠᴏʟɢᴏɢʀᴀᴅ ",
    "Иркутск": "🌪 ɪʀᴋᴜᴛsᴋ ",
    "Омск": "🪙 ᴏᴍsᴋ ",
    "Саратов": "🐉 sᴀʀᴀᴛᴏᴡ ",
    "Грозный": "🍙 ɢʀᴏᴢɴʏ ",
    "Новосиб": "🍃 ɴᴏᴠᴏsɪʙ ",
    "Арзамас": "🪿 ᴀʀᴢᴀᴍᴀs ",
    "Краснодар": "🪻 ᴋʀᴀsɴ ᴅᴀʀ ",
    "Екб": "📗 ᴇᴋʙ ",
    "Анапа": "🪺 ᴀɴᴀᴘᴀ ",
    "Ростов": "🍺 ʀᴏsᴛᴏᴠ ",
    "Самара": "🎧 sᴀᴍᴀʀᴀ ",
    "Казань": "🏛 ᴋᴀᴢᴀɴ ",
    "Сочи": "🌊 sᴏᴄʜɪ ",
    "Уфа": "🌪 ᴜғᴀ ",
    "Спб": "🌉 sᴘʙ ",
    "Москва": "🌇 ᴍᴏsᴄᴏᴡ ",
    "Чоко": "🤎 ᴄʜᴏᴄᴏ ",
    "Чили": "📕 ᴄʜɪʟʟɪ ",
    "Айс": "❄ ɪᴄᴇ ",
    "Грей": "📓 ɢʀᴀʏ ",
    "Аква": "📘 ᴀǫᴜᴀ ",
    "Плат": "🩶 ᴘʟᴀᴛɪɴᴜᴍ ",
    "Азур": "💙 ᴀᴢᴜʀᴇ ",
    "Голд": "💛 ɢᴏʟᴅ ",
    "Кримсон": "❤‍🔥 ᴄʀɪᴍsᴏɴ ",
    "Магента": "🩷 ᴍᴀɢᴇɴᴛᴀ ",
    "Вайт": "🤍 ᴡʜɪᴛᴇ ",
    "Индиго": "💜 ɪɴᴅɪɢᴏ ",
    "Блек": "🖤 ʙʟᴀᴄᴋ ",
    "Чери": "🍒 ᴄʜᴇʀʀʏ ",
    "Пинк": "💕 ᴘɪɴᴋ ",
    "Лайм": "🍋 ʟɪᴍᴇ ",
    "Пурпл": "💜 ᴘᴜʀᴘʟᴇ ",
    "Оранж": "🧡 ᴏʀᴀɴɢᴇ ",
    "Елоу": "💛 ʏᴇʟʟᴏᴡ ",
    "Блу": "💙 ʙʟᴜᴇ ",
    "Грин": "💚 ɢʀᴇᴇɴ ",
    "Ред": "❤‍🩹 ʀᴇᴅ "
}


def is_admin(user_id):
    """Проверка является ли пользователь админом"""
    return user_id in admins


def update_list_text():
    today = datetime.now().strftime("%d.%m.%y")
    header = f"📋 Лист by \"Чекеры Kornycod\"\n[Дата: {today}]\n\n"

    list_items = []
    for city_key, city_display in city_mapping.items():
        status = data.get(city_key, "")
        list_items.append(f"{city_display}{status}")

    list_text = header + "\n".join(list_items)
    return list_text


def send_or_update_list():
    global list_message_id, pinned_message_id

    try:
        list_text = update_list_text()

        if list_message_id:
            try:
                # Пытаемся отредактировать существующее сообщение
                bot.edit_message_text(
                    chat_id=WORK_CHAT_ID,
                    message_id=list_message_id,
                    text=list_text,
                    parse_mode='HTML'
                )
            except Exception as e:
                print(f"Ошибка редактирования: {e}")
                # Если не удалось отредактировать, отправляем новое
                msg = bot.send_message(WORK_CHAT_ID, list_text)
                list_message_id = msg.message_id

                # Пытаемся закрепить новое сообщение
                if not pinned_message_id:
                    try:
                        bot.pin_chat_message(WORK_CHAT_ID, list_message_id, disable_notification=True)
                        pinned_message_id = list_message_id
                    except Exception as e:
                        print(f"Ошибка закрепления: {e}")
        else:
            # Первое сообщение - отправляем и закрепляем
            msg = bot.send_message(WORK_CHAT_ID, list_text)
            list_message_id = msg.message_id

            try:
                # Пытаемся закрепить сообщение
                bot.pin_chat_message(WORK_CHAT_ID, list_message_id, disable_notification=True)
                pinned_message_id = list_message_id
                print(f"Сообщение закреплено: {list_message_id}")
            except Exception as e:
                print(f"Не удалось закрепить сообщение: {e}")
                print("Убедитесь, что бот имеет права администратора в чате!")
    except Exception as e:
        print(f"Общая ошибка: {e}")


@bot.message_handler(commands=['liststart'])
def start_collecting(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только админы могут использовать эту команду!")
        return

    global collecting_info, data, user_data, list_message_id, pinned_message_id

    collecting_info = True
    data = {}
    user_data = {}
    list_message_id = None
    pinned_message_id = None

    # Очистим предыдущие закрепленные сообщения
    try:
        # Получаем информацию о чате
        chat = bot.get_chat(WORK_CHAT_ID)
        if chat.pinned_message:
            try:
                bot.unpin_chat_message(WORK_CHAT_ID)
            except:
                pass
    except:
        pass

    # Отправляем и закрепляем новый лист
    send_or_update_list()

    # Проверяем, закрепилось ли
    if pinned_message_id:
        bot.reply_to(message, "✅ Сбор начат, список закреплен")
    else:
        bot.reply_to(message, "✅ Сбор начат, но не удалось закрепить сообщение. Проверьте права бота!")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_admin(message.from_user.id):
        bot.reply_to(message,
                     f"👨‍💼 Привет, админ!\n"
                     f"Твой ID: {message.from_user.id}\n\n"
                     "📋 Команды:\n"
                     "/liststart - начать сбор\n"
                     "/liststop - остановить сбор\n"
                     "/del город - удалить статус\n"
                     "/pd - полный сброс листа\n"
                     "/addadmin ID - добавить админа\n"
                     "/removeadmin ID - удалить админа\n"
                     "/admins - список админов\n"
                     "/zov - простой созов для участников\n\n"
                     "Пример: Москва Бб")
    else:
        bot.reply_to(message, "🤖 Бот для чекинга слётов")


@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    """Добавить нового админа (только главный админ)"""
    if message.from_user.id != MAIN_ADMIN_ID:
        bot.reply_to(message, "❌ Только главный админ может добавлять других админов!")
        return

    parts = message.text.split()
    if len(parts) >= 2:
        try:
            new_admin_id = int(parts[1])
            if new_admin_id not in admins:
                admins.append(new_admin_id)
                bot.reply_to(message, f"✅ Пользователь {new_admin_id} добавлен в админы!")
            else:
                bot.reply_to(message, f"⚠️ Пользователь {new_admin_id} уже админ!")
        except ValueError:
            bot.reply_to(message, "❌ Неверный ID! ID должен быть числом.")
    else:
        bot.reply_to(message, "📝 Использование: /addadmin ID_пользователя")


@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    """Удалить админа (только главный админ)"""
    if message.from_user.id != MAIN_ADMIN_ID:
        bot.reply_to(message, "❌ Только главный админ может удалять админов!")
        return

    parts = message.text.split()
    if len(parts) >= 2:
        try:
            admin_id = int(parts[1])
            if admin_id == MAIN_ADMIN_ID:
                bot.reply_to(message, "❌ Нельзя удалить главного админа!")
                return

            if admin_id in admins:
                admins.remove(admin_id)
                bot.reply_to(message, f"✅ Пользователь {admin_id} удален из админов!")
            else:
                bot.reply_to(message, f"⚠️ Пользователь {admin_id} не найден в списке админов!")
        except ValueError:
            bot.reply_to(message, "❌ Неверный ID! ID должен быть числом.")
    else:
        bot.reply_to(message, "📝 Использование: /removeadmin ID_админа")


@bot.message_handler(commands=['admins'])
def list_admins(message):
    """Показать список админов"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только админы могут просматривать этот список!")
        return

    admin_list = "\n".join([f"• {admin_id}" for admin_id in admins])
    bot.reply_to(message, f"📋 Список админов:\n{admin_list}")


@bot.message_handler(commands=['liststop'])
def stop_collecting(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только админы могут использовать эту команду!")
        return

    global collecting_info

    collecting_info = False
    if pinned_message_id:
        try:
            bot.unpin_chat_message(WORK_CHAT_ID, pinned_message_id)
        except:
            pass
    bot.reply_to(message, "⏸️ Сбор остановлен")


@bot.message_handler(commands=['del'])
def delete_status(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только админы могут использовать эту команду!")
        return

    parts = message.text.split()
    if len(parts) >= 2:
        city = parts[1].capitalize()
        if city in data:
            del data[city]
            if city in user_data:
                del user_data[city]
            bot.reply_to(message, f"✅ {city} удален")
            if collecting_info:
                send_or_update_list()
        else:
            bot.reply_to(message, f"❌ {city} не найден")


@bot.message_handler(commands=['pd'])
def reset_list(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только админы могут использовать эту команду!")
        return

    global data, user_data, list_message_id, pinned_message_id

    data = {}
    user_data = {}

    if pinned_message_id:
        try:
            bot.unpin_chat_message(WORK_CHAT_ID, pinned_message_id)
        except:
            pass

    if list_message_id:
        try:
            bot.delete_message(WORK_CHAT_ID, list_message_id)
        except:
            pass

        list_message_id = None
        pinned_message_id = None

    bot.reply_to(message, "♻️ Лист сброшен")

    if collecting_info:
        send_or_update_list()


@bot.message_handler(commands=['zov'])
def call_all_participants(message):
    """Простой созов для всех участников"""
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только админы могут использовать эту команду!")
        return

    # Простой созов с тегом всех
    zov_message = """
📢 <b>СОЗОВ ДЛЯ ВСЕХ УЧАСТНИКОВ!</b> 📢

@all

<b>Внимание всем участникам!</b>

Если вы еще не заполнили свой город - сделайте это сейчас!

<b>Формат:</b> Город Статус
<b>Пример:</b> Москва Бб

⚡ <i>Срочно заполняйте свои города!</i> ⚡
    """

    try:
        # Отправляем созов в рабочий чат
        bot.send_message(WORK_CHAT_ID, zov_message, parse_mode='HTML')
        bot.reply_to(message, "✅ Созов отправлен в чат!")
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка отправки: {e}")


@bot.message_handler(func=lambda message: message.chat.id == WORK_CHAT_ID and collecting_info)
def handle_message(message):
    if message.text.startswith('/'):
        return

    text = message.text.strip()
    if not text or ' ' not in text:
        return

    parts = text.split(' ', 1)
    city = parts[0].capitalize()
    status = parts[1]

    if city not in city_mapping:
        return

    # Проверяем не заполнен ли уже сервер другим человеком
    if city in user_data:
        existing_user_id = user_data[city]
        if existing_user_id != message.from_user.id:
            bot.reply_to(message, f"⚠️ Сервер {city} уже заполнен!")
            return

    # Создаем кнопки подтверждения
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_yes = types.InlineKeyboardButton("✅ Правильно", callback_data=f"confirm_{city}_{message.from_user.id}")
    btn_no = types.InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{city}_{message.from_user.id}")
    markup.add(btn_yes, btn_no)

    # Отправляем сообщение с подтверждением
    bot.send_message(
        WORK_CHAT_ID,
        f"Вы точно хотите добавить слёт?\n\nСервер: {city} {status}",
        reply_markup=markup,
        reply_to_message_id=message.message_id
    )


@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    try:
        parts = call.data.split('_')
        action, city, user_id = parts[0], parts[1], int(parts[2])

        if call.from_user.id != user_id:
            bot.answer_callback_query(call.id, "Не ваш слёт")
            return

        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

        if action == "confirm":
            if city in user_data and user_data[city] != user_id:
                bot.answer_callback_query(call.id, "Сервер уже заполнен")
                return

            msg_text = call.message.text
            status_text = msg_text.split(f"Сервер: {city} ")[1]

            username = call.from_user.username or call.from_user.first_name
            data[city] = f"{status_text} - @{username}"
            user_data[city] = user_id

            send_or_update_list()
            bot.answer_callback_query(call.id, "✅ Подтверждено")

        elif action == "reject":
            bot.answer_callback_query(call.id, "❌ Отклонено")

    except:
        bot.answer_callback_query(call.id, "Ошибка")


print("🤖 Бот запущен!")
print(f"📋 Главный админ: {MAIN_ADMIN_ID}")
print(f"👥 Всего админов: {len(admins)}")
bot.infinity_polling()
