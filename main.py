import telebot
from telebot import types
from datetime import datetime
import time as tm
import threading
from collections import defaultdict
import json

# =========== КРИТИЧЕСКИЙ ФИКС ДЛЯ ОШИБКИ ===========
# Патчим класс Story для игнорирования лишних полей
def patch_story_class():
    original_de_json = types.Story.de_json
    
    @staticmethod
    def fixed_de_json(obj):
        if obj is None:
            return None
        # Удаляем все лишние поля, которых нет в оригинальном классе
        allowed_keys = ['id', 'chat_id', 'from_user']
        filtered_obj = {k: v for k, v in obj.items() if k in allowed_keys}
        return original_de_json(filtered_obj) if filtered_obj else None
    
    types.Story.de_json = fixed_de_json

# Включаем фикс при импорте
patch_story_class()
# ====================================================

# токен
bot = telebot.TeleBot("8428311632:AAHG2voyPDqXoSYTYZykmt1I5ad1n7R7Tss")

# id основного админа (ты)
MAIN_ADMIN_ID = 8281448580

# Список админов (добавляй сюда ID друзей)
admins = [5012040224, 8426101180]

# id чата tg в котором work
WORK_CHAT_ID = -1003627161864

data = {}
user_data = {}
collecting_info = False
list_message_id = None
pinned_message_id = None
stats = defaultdict(int)

# Словарь для обработки ввода
city_input_map = {
    "норильск": "Норильск", "череповец": "Череповец", "магадан": "Магадан",
    "подольск": "Подольск", "сургут": "Сургут", "ижевск": "Ижевск",
    "томск": "Томск", "тверь": "Тверь", "вологда": "Вологда",
    "таганрог": "Таганрог", "новгород": "Новгород", "калуга": "Калуга",
    "владимир": "Владимир", "кострома": "Кострома", "чита": "Чита",
    "астрахань": "Астрахань", "братск": "Братск", "тамбов": "Тамбов",
    "якутск": "Якутск", "ульяновск": "Ульяновск", "липецк": "Липецк",
    "барнаул": "Барнаул", "ярославль": "Ярославль", "орел": "Орел",
    "брянск": "Брянск", "псков": "Псков", "смоленск": "Смоленск",
    "ставрополь": "Ставрополь", "иваново": "Иваново", "тольятти": "Тольятти",
    "тюмень": "Тюмень", "кемерово": "Кемерово", "киров": "Киров",
    "оренбург": "Оренбург", "архангельск": "Архангельск", "курск": "Курск",
    "мурманск": "Мурманск", "пенза": "Пенза", "рязань": "Рязань",
    "тула": "Тула", "пермь": "Пермь", "хабаровск": "Хабаровск",
    "чебоксары": "Чебоксары", "красноярск": "Красноярск", "челябинск": "Челябинск",
    "калининград": "Калининград", "владивосток": "Владивосток", "владикавказ": "Владикавказ",
    "махачкала": "Махачкала", "белгород": "Белгород", "воронеж": "Воронеж",
    "волгоград": "Волгоград", "иркутск": "Иркутск", "омск": "Омск",
    "саратов": "Саратов", "грозный": "Грозный", "новосибирск": "Новосибирск",
    "арзамас": "Арзамас", "краснодар": "Краснодар", "екатеринбург": "Екатеринбург",
    "анапа": "Анапа", "ростов": "Ростов", "самара": "Самара",
    "казань": "Казань", "сочи": "Сочи", "уфа": "Уфа",
    "санкт-петербург": "Спб", "спб": "Спб", "москва": "Москва",
    
    # Английские
    "norilsk": "Норильск", "cherepovets": "Череповец", "magadan": "Магадан",
    "podolsk": "Подольск", "surgut": "Сургут", "izhevsk": "Ижевск",
    "tomsk": "Томск", "tver": "Тверь", "vologda": "Вологда",
    "taganrog": "Таганрог", "novgorod": "Новгород", "kaluga": "Калуга",
    "vladimir": "Владимир", "kostroma": "Кострома", "chita": "Чита",
    "astrakhan": "Астрахань", "bratsk": "Братск", "tambov": "Тамбов",
    "yakutsk": "Якутск", "ulyanovsk": "Ульяновск", "lipetsk": "Липецк",
    "barnaul": "Барнаул", "yaroslavl": "Ярославль", "orel": "Орел",
    "bryansk": "Брянск", "pskov": "Псков", "smolensk": "Смоленск",
    "stavropol": "Ставрополь", "ivanovo": "Иваново", "tolyatti": "Тольятти",
    "tyumen": "Тюмень", "kemerovo": "Кемерово", "kirov": "Киров",
    "orenburg": "Оренбург", "arkhangelsk": "Архангельск", "kursk": "Курск",
    "murmansk": "Мурманск", "penza": "Пенза", "ryazan": "Рязань",
    "tula": "Тула", "perm": "Пермь", "khabarovsk": "Хабаровск",
    "cheboksary": "Чебоксары", "krasnoyarsk": "Красноярск", "chelyabinsk": "Челябинск",
    "kaliningrad": "Калининград", "vladivostok": "Владивосток", "vladikavkaz": "Владикавказ",
    "makhachkala": "Махачкала", "belgorod": "Белгород", "voronezh": "Воронеж",
    "volgograd": "Волгоград", "irkutsk": "Иркутск", "omsk": "Омск",
    "saratov": "Саратов", "grozny": "Грозный", "novosibirsk": "Новосибирск",
    "arzamas": "Арзамас", "krasnodar": "Краснодар", "ekaterinburg": "Екатеринбург",
    "anapa": "Анапа", "rostov": "Ростов", "samara": "Самара",
    "kazan": "Казань", "sochi": "Сочи", "ufa": "Уфа",
    "saint petersburg": "Спб", "saint-petersburg": "Спб", "spb": "Спб", "moscow": "Москва",
}

# Отображение для листа
city_display = {
    "Норильск": "🎁 Норильск ", "Череповец": "👮‍♂Череповец ", "Магадан": "🐀Магадан ",
    "Подольск": "🏰 ᴘᴏᴅᴏʟsᴋ ", "Сургут": "🏙 sᴜʀɢᴜᴛ ", "Ижевск": "🏍 ɪᴢʜᴇᴠsᴋ ",
    "Томск": "🎄 ᴛᴏᴍsᴋ ", "Тверь": "🐿 ᴛᴠᴇʀ ", "Вологда": "🐦‍🔥 ᴠᴏʟᴏɢᴅᴀ ",
    "Таганрог": "🦁 ᴛᴀɢᴀɴʀᴏɢ ", "Новгород": "🌼 ɴᴏᴠɢᴏʀᴏᴅ ", "Калуга": "🫐 ᴋᴀʟᴜɢᴀ ",
    "Владимир": "😹 ᴠʟᴀᴅɪᴍɪʀ ", "Кострома": "🐲 ᴋᴏsᴛʀᴏᴍᴀ ", "Чита": "🦎 ᴄʜɪᴛᴀ ",
    "Астрахань": "🧣 ᴀsᴛʀᴀᴋʜᴀɴ ", "Братск": "👜 ʙʀᴀᴛsᴋ ", "Тамбов": "🥐 ᴛᴀᴍʙᴏᴡ ",
    "Якутск": "🥽 ʏᴀᴋᴜᴛsᴋ ", "Ульяновск": "🍭 ᴜʟʏᴀɴᴏᴠsᴋ ", "Липецк": "🎈 ʟɪᴘᴇᴛsᴋ ",
    "Барнаул": "💦 ʙᴀʀɴᴀᴜʟ ", "Ярославль": "🏛 ʏᴀʀᴏsʟᴀᴠʟ ", "Орел": "🦅 ᴏʀᴇʟ ",
    "Брянск": "🧸 ʙʀʏᴀɴsᴋ ", "Псков": "🪭 ᴘsᴋᴏᴡ ", "Смоленск": "🫚 sᴍᴏʟᴇɴsᴋ ",
    "Ставрополь": "🪼 sᴛᴀᴠʀᴏᴘᴏʟ ", "Иваново": "🪅 ɪᴠᴀɴᴏᴠᴏ ", "Тольятти": "🪸 ᴛᴏʟʏᴀᴛᴛɪ ",
    "Тюмень": "🐋 ᴛʏᴜᴍᴇɴ ", "Кемерово": "🌺 ᴋᴇᴍᴇʀᴏᴠᴏ ", "Киров": "🔫 ᴋɪʀᴏᴠ ",
    "Оренбург": "🍖 ᴏʀᴇɴʙᴜʀɢ ", "Архангельск": "🥋 ᴀʀᴋʜᴀɴɢᴇʟsᴋ ", "Курск": "🃏 ᴋᴜʀsᴋ ",
    "Мурманск": "🎳 ᴍᴜʀᴍᴀɴsᴋ ", "Пенза": "🎷 ᴘᴇɴᴢᴀ ", "Рязань": "🎭 ʀʏᴀᴢᴀɴ ",
    "Тула": "⛳ ᴛᴜʟᴀ ", "Пермь": "🏟 ᴘᴇʀᴍ ", "Хабаровск": "🐨 ᴋʜᴀʙᴀʀᴏᴠsᴋ ",
    "Чебоксары": "🪄 ᴄʜᴇʙᴏᴋsᴀʀ ", "Красноярск": "🖇 ᴋʀᴀsɴᴏʏᴀʀsᴋ ", "Челябинск": "🕊 ᴄʜᴇʟʏᴀʙɪɴsᴋ ",
    "Калининград": "👒 ᴋᴀʟɪɴɪɴɢʀᴀᴅ ", "Владивосток": "🧶 ᴠʟᴀᴅɪᴠᴏsᴛᴏᴋ ", "Владикавказ": "🌂 ᴠʟᴀᴅɪᴋᴀᴠᴋᴀᴢ ",
    "Махачкала": "⛑️ ᴍᴀᴋʜᴀᴄʜᴋᴀʟᴀ ", "Белгород": "🎓 ʙᴇʟɢᴏʀᴏᴅ ", "Воронеж": "👑 ᴠᴏʀᴏɴᴇᴢʜ ",
    "Волгоград": "🎒 ᴠᴏʟɢᴏɢʀᴅ ", "Иркутск": "🌪 ɪʀᴋᴜᴛsᴋ ", "Омск": "🪙 ᴏᴍsᴋ ",
    "Саратов": "🐉 sᴀʀᴀᴛᴏᴡ ", "Грозный": "🍙 ɢʀᴏᴢɴʏ ", "Новосибирск": "🍃 ɴᴏᴠᴏsɪʙ ",
    "Арзамас": "🪿 ᴀʀᴢᴀᴍᴀs ", "Екатеринбург": "📗 ᴇᴋʙ ", "Анапа": "🪺 ᴀɴᴀᴘᴀ ",
    "Ростов": "🍺 ʀᴏsᴛᴏᴠ ", "Самара": "🎧 sᴀᴍᴀʀᴀ ", "Казань": "🏛 ᴋᴀᴢᴀɴ ",
    "Сочи": "🌊 sᴏᴄʜɪ ", "Уфа": "🌪 ᴜғᴀ ", "Спб": "🌉 sᴘʙ ",
    "Москва": "🌇 ᴍᴏsᴄᴏᴡ ",
}

def is_admin(user_id):
    return user_id in admins

def update_list_text():
    header = f"ᴧоᴦоʙо ʙоᴩᴋᴇᴩоʙ\n\n"
    list_items = []
    for city_key in city_display.keys():
        status = data.get(city_key, "")
        list_items.append(f"{city_display[city_key]}{status}")
    return header + "\n".join(list_items)

def send_or_update_list():
    global list_message_id, pinned_message_id
    try:
        list_text = update_list_text()
        if list_message_id:
            try:
                bot.edit_message_text(
                    chat_id=WORK_CHAT_ID,
                    message_id=list_message_id,
                    text=list_text,
                    parse_mode='HTML'
                )
                print(f"✅ Лист отредактирован (ID: {list_message_id})")
                return
            except Exception as e:
                if "message is not modified" not in str(e):
                    print(f"❌ Ошибка редактирования: {e}")
                    list_message_id = None
                    pinned_message_id = None
        msg = bot.send_message(WORK_CHAT_ID, list_text, parse_mode='HTML')
        list_message_id = msg.message_id
        print(f"📝 Лист отправлен (ID: {list_message_id})")
        if not pinned_message_id:
            try:
                bot.pin_chat_message(WORK_CHAT_ID, list_message_id, disable_notification=True)
                pinned_message_id = list_message_id
                print(f"📌 Сообщение закреплено (ID: {list_message_id})")
            except Exception as e:
                print(f"⚠️ Не удалось закрепить: {e}")
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")

def delete_message_with_delay(message_id, delay=2):
    def delete_after_delay():
        tm.sleep(delay)
        try:
            bot.delete_message(WORK_CHAT_ID, message_id)
        except:
            pass
    thread = threading.Thread(target=delete_after_delay)
    thread.daemon = True
    thread.start()

def update_stats(username, action="add"):
    if action == "add":
        stats[username] += 1
    elif action == "remove":
        if username in stats and stats[username] > 0:
            stats[username] -= 1
            if stats[username] == 0:
                del stats[username]

@bot.message_handler(commands=['stats'])
def show_stats(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только админы!")
        return
    if not stats:
        bot.reply_to(message, "📊 Статистика пуста")
        return
    sorted_stats = sorted(stats.items(), key=lambda x: x[1], reverse=True)
    stats_text = "📊 **СТАТИСТИКА ЧЕКЕРОВ**\n\n"
    for i, (username, count) in enumerate(sorted_stats, 1):
        stats_text += f"{i}. @{username} - {count} слёт{'ов' if count != 1 else ''}\n"
    stats_text += f"\n📈 Всего: {sum(stats.values())}\n👥 Уникальных: {len(stats)}"
    bot.reply_to(message, stats_text, parse_mode='HTML')

@bot.message_handler(commands=['mystats'])
def show_my_stats(message):
    username = message.from_user.username or message.from_user.first_name
    if username in stats:
        count = stats[username]
        bot.reply_to(message, f"📊 @{username} - {count} слёт{'ов' if count != 1 else ''}")
    else:
        bot.reply_to(message, "📊 Вы еще не чекали слёты!")

@bot.message_handler(commands=['d'])
def delete_my_slet(message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    parts = message.text.split()
    if len(parts) >= 2:
        city_input = parts[1].lower()
        city_key = city_input_map.get(city_input)
        if not city_key:
            reply = bot.reply_to(message, f"❌ Сервер '{city_input}' не найден")
            delete_message_with_delay(reply.message_id, 2)
            return
        if city_key not in data:
            reply = bot.reply_to(message, f"❌ Слёт {city_key} не заполнен")
            delete_message_with_delay(reply.message_id, 2)
            return
        if user_data.get(city_key) != user_id:
            reply = bot.reply_to(message, f"❌ Слёт {city_key} заполнен не вами")
            delete_message_with_delay(reply.message_id, 2)
            return
        del data[city_key]
        del user_data[city_key]
        update_stats(username, "remove")
        if collecting_info:
            send_or_update_list()
        reply = bot.reply_to(message, f"✅ Ваш слёт {city_key} удален")
        delete_message_with_delay(reply.message_id, 2)
    else:
        user_cities = [city for city, user in user_data.items() if user == user_id]
        if user_cities:
            cities_list = "\n".join([f"• {city}" for city in user_cities])
            reply = bot.reply_to(message, f"📋 Ваши слёты:\n{cities_list}\n\n🗑️ Удалить: /d [сервер]")
            delete_message_with_delay(reply.message_id, 5)
        else:
            reply = bot.reply_to(message, "❌ У вас нет заполненных слётов")
            delete_message_with_delay(reply.message_id, 2)

@bot.message_handler(commands=['liststart'])
def start_collecting(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только админы!")
        return
    global collecting_info, data, user_data, list_message_id, pinned_message_id, stats
    collecting_info = True
    data = {}
    user_data = {}
    stats.clear()
    list_message_id = None
    pinned_message_id = None
    try:
        chat = bot.get_chat(WORK_CHAT_ID)
        if chat.pinned_message:
            try:
                bot.unpin_chat_message(WORK_CHAT_ID)
            except:
                pass
    except:
        pass
    send_or_update_list()
    try:
        bot.send_message(
            WORK_CHAT_ID,
            "✅ <b>БОТ АКТИВЕН</b>\n\n"
            "📋 Начат сбор слётов!\n"
            "✍️ Пишите: <code>Город Статус</code>\n"
            "🌐 Можно писать на русском или английском\n"
            "❌ Удалить свой слёт: <code>/d город</code>",
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Ошибка отправки: {e}")
    bot.reply_to(message, "✅ Сбор начат!")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if is_admin(message.from_user.id):
        bot.reply_to(message,
                     f"👨‍💼 Привет, админ!\nТвой ID: {message.from_user.id}\n\n"
                     "📋 Команды:\n/liststart - начать сбор\n/liststop - остановить\n"
                     "/del город - удалить статус\n/pd - полный сброс\n"
                     "/addadmin ID - добавить админа\n/removeadmin ID - удалить админа\n"
                     "/admins - список админов\n/zov - созов\n/stats - статистика\n"
                     "/mystats - моя статистика\n/d [сервер] - удалить свой слёт")
    else:
        bot.reply_to(message,
                     "🤖 Бот для чекинга слётов\n\n📝 Как использовать:\n"
                     "1. Пишите: Город Статус\n2. Можно писать по-русски или по-английски\n"
                     "3. Если ошиблись - /d [сервер]\n4. Посмотреть статистику - /mystats")

@bot.message_handler(commands=['addadmin'])
def add_admin(message):
    if message.from_user.id != MAIN_ADMIN_ID:
        bot.reply_to(message, "❌ Только главный админ!")
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
            bot.reply_to(message, "❌ Неверный ID!")
    else:
        bot.reply_to(message, "📝 /addadmin ID_пользователя")

@bot.message_handler(commands=['removeadmin'])
def remove_admin(message):
    if message.from_user.id != MAIN_ADMIN_ID:
        bot.reply_to(message, "❌ Только главный админ!")
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
                bot.reply_to(message, f"⚠️ Пользователь {admin_id} не найден!")
        except ValueError:
            bot.reply_to(message, "❌ Неверный ID!")
    else:
        bot.reply_to(message, "📝 /removeadmin ID_админа")

@bot.message_handler(commands=['admins'])
def list_admins(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только админы!")
        return
    admin_list = "\n".join([f"• {admin_id}" for admin_id in admins])
    bot.reply_to(message, f"📋 Список админов:\n{admin_list}")

@bot.message_handler(commands=['liststop'])
def stop_collecting(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только админы!")
        return
    global collecting_info
    collecting_info = False
    if pinned_message_id:
        try:
            bot.unpin_chat_message(WORK_CHAT_ID, pinned_message_id)
        except:
            pass
    try:
        bot.send_message(
            WORK_CHAT_ID,
            "⏸️ <b>БОТ ОТКЛЮЧЕН</b>\n\n"
            "📋 Сбор слётов остановлен!\n"
            "✍️ Чекины больше не принимаются\n"
            "🔄 Для нового сбора /liststart",
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Ошибка отправки: {e}")
    bot.reply_to(message, "⏸️ Сбор остановлен")

@bot.message_handler(commands=['del'])
def delete_status(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только админы!")
        return
    parts = message.text.split()
    if len(parts) >= 2:
        city_input = parts[1].lower()
        city_key = city_input_map.get(city_input)
        if city_key:
            if city_key in data:
                username = data[city_key].split(' - @')[-1] if ' - @' in data[city_key] else None
                if username:
                    update_stats(username, "remove")
                del data[city_key]
                if city_key in user_data:
                    del user_data[city_key]
                bot.reply_to(message, f"✅ {city_key} удален")
                if collecting_info:
                    send_or_update_list()
            else:
                bot.reply_to(message, f"❌ {city_key} не найден")
        else:
            bot.reply_to(message, f"❌ {city_input} не найден")

@bot.message_handler(commands=['pd'])
def reset_list(message):
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только админы!")
        return
    global data, user_data, list_message_id, pinned_message_id, stats
    data = {}
    user_data = {}
    stats.clear()
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
    if not is_admin(message.from_user.id):
        bot.reply_to(message, "❌ Только админы!")
        return
    if not collecting_info:
        bot.reply_to(message, "⚠️ Бот отключен! /liststart")
        return
    zov_message = """
📢 <b>СОЗОВ ДЛЯ ВСЕХ УЧАСТНИКОВ!</b> 📢

@all

<b>Внимание всем!</b>

Если вы еще не заполнили свой город - сделайте это сейчас!

<b>Формат:</b> Город Статус
<b>Примеры:</b>
Москва Бб
moscow Бб
Орел 0
orel 0

<b>Удалить свой слёт:</b> /d [сервер]
<b>Пример:</b> /d Москва

⚡ <i>Срочно заполняйте!</i> ⚡
    """
    try:
        bot.send_message(WORK_CHAT_ID, zov_message, parse_mode='HTML')
        bot.reply_to(message, "✅ Созов отправлен!")
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
    city_input = parts[0].lower()
    status = parts[1]
    if city_input not in city_input_map:
        return
    city_key = city_input_map[city_input]
    if city_key in user_data:
        existing_user_id = user_data[city_key]
        if existing_user_id != message.from_user.id:
            reply = bot.reply_to(message, f"⚠️ Сервер {city_key} уже заполнен!")
            delete_message_with_delay(reply.message_id, 2)
            return
    username = message.from_user.username or message.from_user.first_name
    data[city_key] = f"{status} - @{username}"
    user_data[city_key] = message.from_user.id
    update_stats(username, "add")
    send_or_update_list()
    reply = bot.reply_to(message, f"✅ Слёт {city_key} добавлен!\n🗑️ Удалить: /d {city_input}")
    delete_message_with_delay(reply.message_id, 3)

# =========== ЗАПУСК БОТА ===========
print("🤖 Бот запущен!")
print(f"📋 Главный админ: {MAIN_ADMIN_ID}")
print(f"👥 Всего админов: {len(admins)}")

# Запуск с обработкой ошибок
while True:
    try:
        bot.infinity_polling(timeout=30, long_polling_timeout=30)
    except Exception as e:
        print(f"⚠️ Ошибка polling: {e}")
        print("🔄 Перезапуск через 5 секунд...")
        tm.sleep(5)
