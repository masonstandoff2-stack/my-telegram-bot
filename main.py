import asyncio
import logging
import time
from datetime import datetime, timedelta
import json
import os
from collections import defaultdict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8099124698:AAGNxq3E84DUzeFWpRp0y64SyZOKOaVQm0M"

# Владелец бота (получает логи)
OWNER_ID = 8577578314  # Ваш ID, замените на свой

# СПИСОК СКУПОВ (добавил еще ботов)
SKUPPERS = [
    {"id": 8225309172, "name": "Skup kravonosov", "username": "@kravonosov1337"},
    {"id": 7958661386, "name": "Skup Jon Garik", "username": "@Lovlya1337"},
    {"id": 8069649242, "name": "Skup Brskupov", "username": "@BrSkupov"},
    {"id": 5095921550, "name": "Skup Рома", "username": "@roman_abvgd228"},  # Добавил
]

# Список серверов (только английские названия)
SERVERS = [
    "Cherepovets", "Magadan", "Podolsk", "Surgut", "Izhevsk", "Tomsk", "Tver",
    "Vologda", "Taganrog", "Novgorod", "Kaluga", "Vladimir", "Kostroma",
    "Chita", "Astrakhan", "Bratsk", "Tambov", "Yakutsk", "Ulyanovsk",
    "Lipetsk", "Barnaul", "Yaroslavl", "Orel", "Bryansk", "Pskov",
    "Smolensk", "Stavropol", "Ivanovo", "Tolyatti", "Tyumen", "Kemerovo",
    "Kirov", "Orenburg", "Arkhangelsk", "Kursk", "Murmansk", "Penza",
    "Ryazan", "Tula", "Perm", "Khabarovsk", "Cheboksary", "Krasnoyarsk",
    "Chelyabinsk", "Kaliningrad", "Vladivostok", "Vladikavkaz", "Makhachkala",
    "Belgorod", "Voronezh", "Volgograd", "Irkutsk", "Omsk", "Saratov",
    "Grozny", "Novosibirsk", "Arzamas", "Krasnodar", "Ekaterinburg",
    "Anapa", "Rostov", "Samara", "Kazan", "Sochi", "Ufa", "Spb",
    "Moscow", "Choco", "Chilli", "Ice", "Gray", "Aqua", "Platinum",
    "Azure", "Gold", "Crimson", "Magenta", "White", "Indigo", "Black",
    "Cherry", "Pink", "Lime", "Purple", "Orange", "Yellow", "Blue",
    "Green", "Red"
]

ORDER_EXPIRE_TIME = 30

# ===== НАСТРОЙКИ АНТИ-СПАМ =====
MAX_ORDERS_PER_DAY = 10  # Максимум заявок в день
ORDER_COOLDOWN = 180  # 3 минуты между заявками (в секундах)
user_cooldowns = {}  # {user_id: last_order_time}
user_order_counts = defaultdict(int)  # {user_id: order_count_today}

# ===== ИНИЦИАЛИЗАЦИЯ =====
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


# ===== ХРАНИЛИЩЕ ДАННЫХ =====
class Order:
    def __init__(self, order_id, user_id, username, order_type, details, server=None, price=None):
        self.order_id = order_id
        self.user_id = user_id
        self.username = username
        self.order_type = order_type
        self.details = details
        self.server = server
        self.price = price  # Желаемая цена пользователя
        self.created_at = datetime.now()
        self.status = "active"
        self.accepted_by = None
        self.skupper_messages = {}
        self.cancel_button_message_id = None
        self.skupper_username = None  # Username скупа, который принял заказ


orders = {}
order_counter = 1

# Список домов
HOUSES = [
    "Бусаево", "Корякина", "Нижний", "Батырево Квартира",
    "Батырево Банк", "Ферма", "Гарель", "Вч"
]


# ===== СОСТОЯНИЯ =====
class OrderStates(StatesGroup):
    waiting_for_virt_amount = State()
    waiting_for_virt_price = State()
    waiting_for_server_virts = State()
    waiting_for_house_price = State()
    waiting_for_server_house = State()
    choosing_house = State()


# ===== ФУНКЦИИ АНТИ-СПАМ =====
async def check_anti_spam(user_id, username):
    """Проверяет анти-спам правила"""
    now = time.time()

    # Проверяем кулдаун
    if user_id in user_cooldowns:
        last_order = user_cooldowns[user_id]
        time_since_last = now - last_order

        if time_since_last < ORDER_COOLDOWN:
            remaining = int(ORDER_COOLDOWN - time_since_last)
            minutes = remaining // 60
            seconds = remaining % 60
            return False, f"⏳ <b>Слишком часто!</b>\n\nПодождите {minutes} мин {seconds} сек"

    # Проверяем лимит за день
    today = datetime.now().strftime("%Y-%m-%d")
    user_key = f"{user_id}_{today}"

    if user_order_counts[user_key] >= MAX_ORDERS_PER_DAY:
        return False, f"🚫 <b>Лимит исчерпан!</b>\n\nЛимит заявок на сегодня ({MAX_ORDERS_PER_DAY}) исчерпан. Попробуйте завтра."

    return True, ""


async def update_anti_spam(user_id):
    """Обновляет анти-спам данные"""
    now = time.time()
    user_cooldowns[user_id] = now

    today = datetime.now().strftime("%Y-%m-%d")
    user_key = f"{user_id}_{today}"
    user_order_counts[user_key] += 1


# ===== ФУНКЦИИ ДЛЯ ЛОГИРОВАНИЯ =====
def ensure_logs_directory():
    """Создает директорию для логов если ее нет"""
    if not os.path.exists("logs"):
        os.makedirs("logs")


def save_order_log(order, action, extra_info=""):
    """Сохраняет лог заказа в файл"""
    ensure_logs_directory()

    log_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "order_id": order.order_id,
        "user_id": order.user_id,
        "username": order.username,
        "order_type": order.order_type,
        "details": order.details,
        "server": order.server,
        "price": order.price,
        "action": action,
        "extra_info": extra_info,
        "status": order.status,
        "skupper_username": order.skupper_username
    }

    # Сохраняем в файл
    filename = f"logs/orders_{datetime.now().strftime('%Y-%m-%d')}.json"

    try:
        # Читаем существующие логи
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        else:
            logs = []

        # Добавляем новую запись
        logs.append(log_entry)

        # Сохраняем обратно
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"Ошибка сохранения лога: {e}")

        # Создаем новый файл если не удалось прочитать
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([log_entry], f, ensure_ascii=False, indent=2)


async def notify_owner(message_text):
    """Отправляет уведомление владельцу бота"""
    try:
        await bot.send_message(
            chat_id=OWNER_ID,
            text=message_text,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Не могу отправить сообщение владельцу: {e}")


async def log_order_created(order, sent_to_count):
    """Логирует создание заказа и уведомляет владельца"""
    # Сохраняем в файл
    save_order_log(order, "created", f"sent_to_{sent_to_count}_skuppers")

    # Формируем сообщение для владельца
    if order.order_type == "house":
        item_text = f"🏠 Дом: {order.details}"
        price_text = f"💰 Цена: {format_number_with_spaces(order.price)} ₽" if order.price else "💰 Цена: не указана"
    else:
        item_text = f"💎 Сумма: {order.details}"
        price_text = f"💰 Цена: {format_number_with_spaces(order.price)} ₽" if order.price else "💰 Цена: не указана"

    server_info = f"\n🌐 Сервер: {order.server}" if order.server else ""

    owner_message = (
        f"📋 <b>НОВЫЙ ЗАКАЗ #{order.order_id}</b>\n\n"
        f"{item_text}{server_info}\n"
        f"{price_text}\n"
        f"👤 Отправитель: {order.username}\n"
        f"🆔 ID отправителя: <code>{order.user_id}</code>\n"
        f"📨 Отправлено скупам: {sent_to_count}\n"
        f"⏰ Время: {order.created_at.strftime('%H:%M:%S')}"
    )

    # Отправляем владельцу
    await notify_owner(owner_message)


async def log_order_accepted(order, skupper_info):
    """Логирует принятие заказа и уведомляет владельца"""
    # Сохраняем в файл
    save_order_log(order, "accepted", f"accepted_by_{skupper_info}")

    # Формируем сообщение для владельца
    if order.order_type == "house":
        item_text = f"🏠 Дом: {order.details}"
        price_text = f"💰 Цена: {format_number_with_spaces(order.price)} ₽" if order.price else "💰 Цена: не указана"
    else:
        item_text = f"💎 Сумма: {order.details}"
        price_text = f"💰 Цена: {format_number_with_spaces(order.price)} ₽" if order.price else "💰 Цена: не указана"

    server_info = f"\n🌐 Сервер: {order.server}" if order.server else ""

    owner_message = (
        f"✅ <b>ЗАКАЗ #{order.order_id} ПРИНЯТ</b>\n\n"
        f"{item_text}{server_info}\n"
        f"{price_text}\n"
        f"👤 Отправитель: {order.username}\n"
        f"👤 Принял скуп: {skupper_info}\n"
        f"⏰ Время принятия: {datetime.now().strftime('%H:%M:%S')}"
    )

    # Отправляем владельцу
    await notify_owner(owner_message)


async def log_order_cancelled(order):
    """Логирует отмену заказа и уведомляет владельца"""
    # Сохраняем в файл
    save_order_log(order, "cancelled")

    # Формируем сообщение для владельца
    if order.order_type == "house":
        item_text = f"🏠 Дом: {order.details}"
        price_text = f"💰 Цена: {format_number_with_spaces(order.price)} ₽" if order.price else "💰 Цена: не указана"
    else:
        item_text = f"💎 Сумма: {order.details}"
        price_text = f"💰 Цена: {format_number_with_spaces(order.price)} ₽" if order.price else "💰 Цена: не указана"

    server_info = f"\n🌐 Сервер: {order.server}" if order.server else ""

    owner_message = (
        f"❌ <b>ЗАКАЗ #{order.order_id} ОТМЕНЕН</b>\n\n"
        f"{item_text}{server_info}\n"
        f"{price_text}\n"
        f"👤 Отменил: {order.username}\n"
        f"⏰ Время отмены: {datetime.now().strftime('%H:%M:%S')}"
    )

    # Отправляем владельцу
    await notify_owner(owner_message)


async def log_order_expired(order):
    """Логирует истечение заказа и уведомляет владельца"""
    # Сохраняем в файл
    save_order_log(order, "expired")

    # Формируем сообщение для владельца
    if order.order_type == "house":
        item_text = f"🏠 Дом: {order.details}"
        price_text = f"💰 Цена: {format_number_with_spaces(order.price)} ₽" if order.price else "💰 Цена: не указана"
    else:
        item_text = f"💎 Сумма: {order.details}"
        price_text = f"💰 Цена: {format_number_with_spaces(order.price)} ₽" if order.price else "💰 Цена: не указана"

    server_info = f"\n🌐 Сервер: {order.server}" if order.server else ""

    owner_message = (
        f"⏰ <b>ЗАКАЗ #{order.order_id} ИСТЕК</b>\n\n"
        f"{item_text}{server_info}\n"
        f"{price_text}\n"
        f"👤 Отправитель: {order.username}\n"
        f"⏰ Истек через: {ORDER_EXPIRE_TIME} минут"
    )

    # Отправляем владельцу
    await notify_owner(owner_message)


# ===== КЛАВИАТУРЫ (КРАСИВЫЕ) =====
def get_main_keyboard(user_id=None):
    """Главная клавиатура (у владельца есть кнопка logs)"""
    keyboard_buttons = [
        [KeyboardButton(text="🏠 Продать дом")],
        [KeyboardButton(text="💎 Продать вирты")],
    ]

    # Только владелец видит кнопку logs
    if user_id == OWNER_ID:
        keyboard_buttons.append([KeyboardButton(text="📊 Логи заказов")])

    return ReplyKeyboardMarkup(
        keyboard=keyboard_buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите действие 👇"
    )


def get_houses_keyboard():
    """Клавиатура для выбора дома с красивым оформлением"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    buttons = []

    for house in HOUSES:
        emoji = "🏠" if "Квартира" not in house else "🏢"
        buttons.append(InlineKeyboardButton(
            text=f"{emoji} {house}",
            callback_data=f"house_{house}"
        ))

    # Разбиваем на строки по 2 кнопки
    for i in range(0, len(buttons), 2):
        row = buttons[i:i + 2]
        keyboard.inline_keyboard.append(row)

    # Кнопка отмены
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_house")
    ])

    return keyboard


def get_servers_keyboard(callback_prefix="server"):
    """Клавиатура для выбора сервера с красивым оформлением"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])

    # Кнопки серверов с эмодзи
    buttons = []
    for server in SERVERS:
        if server in ["Moscow", "Spb"]:
            emoji = "🏛️"
        elif server in ["Gold", "Diamond", "Platinum"]:
            emoji = "💎"
        elif server in ["Red", "Blue", "Green", "Yellow"]:
            emoji = "🎨"
        else:
            emoji = "🌐"

        buttons.append(InlineKeyboardButton(
            text=f"{emoji} {server}",
            callback_data=f"{callback_prefix}_{server}"
        ))

    # Разбиваем на строки по 3 кнопки
    for i in range(0, len(buttons), 3):
        row = buttons[i:i + 3]
        keyboard.inline_keyboard.append(row)

    # Кнопка отмены
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_server")
    ])

    return keyboard


def get_order_cancel_keyboard(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отменить заявку", callback_data=f"cancel_order_{order_id}")]
    ])


def get_skupper_accept_keyboard(order_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ ВЗЯТЬ ЗАКАЗ", callback_data=f"take_order_{order_id}")]
    ])


def get_logs_keyboard():
    """Клавиатура для управления логами (только для владельца)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="logs_stats"),
            InlineKeyboardButton(text="📅 Сегодня", callback_data="logs_today")
        ],
        [
            InlineKeyboardButton(text="📁 Все логи", callback_data="logs_all"),
            InlineKeyboardButton(text="🗑️ Очистить логи", callback_data="logs_clear")
        ],
        [InlineKeyboardButton(text="❌ Закрыть", callback_data="logs_close")]
    ])


# ===== УТИЛИТЫ =====
def format_amount(amount):
    """Форматирует сумму виртов для отображения"""
    if amount >= 1000000:
        return f"{amount:,}".replace(",", ".") + f" ({amount // 1000000}кк)"
    return f"{amount:,}".replace(",", ".")


def parse_amount(text):
    """Парсит сумму из текста с разными форматами"""
    text = text.strip().replace(" ", "").lower()

    # Убираем все нецифровые символы кроме "к" и точки
    clean_text = ""
    for char in text:
        if char.isdigit() or char == '.' or char == 'к':
            clean_text += char

    # Парсим разные форматы
    if 'кк' in clean_text:
        # Формат: 10кк, 5.5кк
        num = clean_text.replace('кк', '')
        try:
            if '.' in num:
                return int(float(num) * 1000000)
            else:
                return int(num) * 1000000
        except:
            return None

    elif 'к' in clean_text:
        # Формат: 10к (тысячи)
        num = clean_text.replace('к', '')
        try:
            if '.' in num:
                return int(float(num) * 1000)
            else:
                return int(num) * 1000
        except:
            return None

    else:
        # Формат: 15000000, 15.000.000
        num = clean_text.replace('.', '')
        try:
            return int(num)
        except:
            return None


def parse_price(text):
    """Парсит цену в рублях из текста"""
    text = text.strip().replace(" ", "").lower()

    # Убираем нецифровые символы кроме точки
    clean_text = ""
    for char in text:
        if char.isdigit() or char == '.':
            clean_text += char

    try:
        # Если есть точка - это может быть десятичное число
        if '.' in clean_text:
            return float(clean_text)
        else:
            return int(clean_text)
    except:
        return None


def format_number_with_spaces(number):
    """Форматирует число с пробелами для красоты"""
    if isinstance(number, float):
        return f"{number:,.2f}".replace(",", " ").replace(".", ",")
    else:
        return f"{number:,}".replace(",", " ")


# ===== ФУНКЦИИ ДЛЯ РАБОТЫ С ЛОГАМИ =====
async def get_today_stats():
    """Получает статистику за сегодня"""
    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"logs/orders_{today}.json"

    if not os.path.exists(filename):
        return {
            "total": 0,
            "active": 0,
            "accepted": 0,
            "cancelled": 0,
            "expired": 0,
            "houses": 0,
            "virts": 0,
            "total_price": 0
        }

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            logs = json.load(f)
    except:
        logs = []

    stats = {
        "total": len(logs),
        "active": 0,
        "accepted": 0,
        "cancelled": 0,
        "expired": 0,
        "houses": 0,
        "virts": 0,
        "total_price": 0
    }

    for log in logs:
        if log.get("status") == "active":
            stats["active"] += 1
        elif log.get("status") == "accepted":
            stats["accepted"] += 1
        elif log.get("status") == "cancelled":
            stats["cancelled"] += 1
        elif log.get("status") == "expired":
            stats["expired"] += 1

        if log.get("order_type") == "house":
            stats["houses"] += 1
        elif log.get("order_type") == "virts":
            stats["virts"] += 1

        if log.get("price"):
            try:
                stats["total_price"] += float(log["price"])
            except:
                pass

    return stats


async def get_all_logs_stats():
    """Получает статистику за все время"""
    ensure_logs_directory()

    total_stats = {
        "total_orders": 0,
        "total_accepted": 0,
        "total_cancelled": 0,
        "total_expired": 0,
        "days_with_logs": 0,
        "total_houses": 0,
        "total_virts": 0,
        "total_price": 0
    }

    try:
        files = os.listdir("logs")
        log_files = [f for f in files if f.startswith("orders_") and f.endswith(".json")]

        for filename in log_files:
            filepath = os.path.join("logs", filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                logs = json.load(f)

            total_stats["total_orders"] += len(logs)
            total_stats["days_with_logs"] += 1

            for log in logs:
                if log.get("status") == "accepted":
                    total_stats["total_accepted"] += 1
                elif log.get("status") == "cancelled":
                    total_stats["total_cancelled"] += 1
                elif log.get("status") == "expired":
                    total_stats["total_expired"] += 1

                if log.get("order_type") == "house":
                    total_stats["total_houses"] += 1
                elif log.get("order_type") == "virts":
                    total_stats["total_virts"] += 1

                if log.get("price"):
                    try:
                        total_stats["total_price"] += float(log["price"])
                    except:
                        pass

    except Exception as e:
        print(f"Ошибка чтения логов: {e}")

    return total_stats


async def clear_old_logs(days=30):
    """Удаляет логи старше N дней"""
    ensure_logs_directory()

    try:
        files = os.listdir("logs")
        deleted = 0

        for filename in files:
            if filename.startswith("orders_") and filename.endswith(".json"):
                # Извлекаем дату из имени файла
                date_str = filename[7:-5]  # orders_YYYY-MM-DD.json
                try:
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    if (datetime.now() - file_date).days > days:
                        os.remove(os.path.join("logs", filename))
                        deleted += 1
                except:
                    continue

        return deleted
    except Exception as e:
        print(f"Ошибка очистки логов: {e}")
        return 0


# ===== ОСНОВНЫЕ ФУНКЦИИ =====
async def broadcast_order_to_all_skuppers(order):
    """Отправить заявку ВСЕМ скупам одновременно"""
    sent_count = 0
    sent_to = []

    for skupper in SKUPPERS:
        try:
            if order.order_type == "house":
                emoji = "🏠"
                details_text = f"Дом: {order.details}"
            else:
                emoji = "💎"
                details_text = f"Сумма: {order.details}"

            # Добавляем информацию о сервере в сообщение для скупа
            server_info = f"\n🌐 Сервер: {order.server}" if order.server else ""

            # Добавляем цену, если указана
            price_info = f"\n💰 Цена: {format_number_with_spaces(order.price)} ₽" if order.price else "\n💰 Цена: не указана"

            # ВАЖНО: НЕ показываем username пользователя скупу!
            # Скуп видит только номер заказа и детали
            message_text = (
                f"🚨 <b>НОВАЯ ЗАЯВКА #{order.order_id}</b>\n\n"
                f"{emoji} {details_text}{server_info}{price_info}\n"
                f"⏰ Время: {order.created_at.strftime('%H:%M:%S')}\n\n"
                f"⚠️ <i>Приняв заказ, пользователь увидит ваш username</i>"
            )

            msg = await bot.send_message(
                chat_id=skupper["id"],
                text=message_text,
                parse_mode="HTML",
                reply_markup=get_skupper_accept_keyboard(order.order_id)
            )

            order.skupper_messages[skupper["id"]] = msg.message_id
            sent_count += 1
            sent_to.append(f"{skupper['name']} ({skupper['username']})")

        except Exception as e:
            print(f"Не отправлено скупу {skupper['name']}: {e}")
            continue

    return sent_count, sent_to


async def notify_user_order_created(order, sent_to_count, sent_to_list):
    """Уведомить пользователя о создании заявки"""
    try:
        if order.order_type == "house":
            item_text = f"дом '{order.details}'"
        else:
            item_text = f"{order.details} виртов"

        server_info = f"\n🌐 Сервер: {order.server}" if order.server else ""

        # Добавляем цену в уведомление пользователю
        price_info = f"\n💰 Ваша цена: {format_number_with_spaces(order.price)} ₽" if order.price else ""

        msg = await bot.send_message(
            chat_id=order.user_id,
            text=f"✅ <b>Заявка #{order.order_id} создана!</b>\n\n"
                 f"📋 Продажа: {item_text}{server_info}{price_info}\n"
                 f"📨 Отправлено скупам: {sent_to_count}\n"
                 f"⏰ Создано: {order.created_at.strftime('%H:%M:%S')}\n\n"
                 f"<i>Ожидайте ответа от скупщиков...</i>\n"
                 f"<i>Если скуп примет заказ, вы увидите его username</i>",
            parse_mode="HTML",
            reply_markup=get_order_cancel_keyboard(order.order_id)
        )

        order.cancel_button_message_id = msg.message_id

    except Exception as e:
        print(f"Не могу уведомить пользователя: {e}")


async def update_skupper_messages(order, accepted_skupper_id=None):
    """Обновить сообщения у всех скупов"""
    for skupper_id, message_id in order.skupper_messages.items():
        try:
            if accepted_skupper_id:
                if skupper_id == accepted_skupper_id:
                    # Формируем информацию о заказе
                    if order.order_type == "house":
                        order_info = f"🏠 Дом: {order.details}"
                    else:
                        order_info = f"💎 Сумма: {order.details}"

                    # Добавляем цену
                    price_info = f"\n💰 Цена: {format_number_with_spaces(order.price)} ₽" if order.price else ""

                    # Скуп видит, что он принял заказ
                    skupper = next((s for s in SKUPPERS if s["id"] == skupper_id), None)
                    skupper_name = skupper["username"] if skupper else "неизвестно"

                    await bot.edit_message_text(
                        chat_id=skupper_id,
                        message_id=message_id,
                        text=f"🎉 <b>ВЫ ПРИНЯЛИ ЗАКАЗ #{order.order_id}</b>\n\n"
                             f"{order_info}\n"
                             f"🌐 Сервер: {order.server}{price_info}\n"
                             f"⏰ Принято: {datetime.now().strftime('%H:%M:%S')}\n\n"
                             f"💬 <b>Пользователь увидел ваш username: {skupper_name}</b>\n"
                             f"<i>Ожидайте, когда пользователь напишет вам</i>",
                        parse_mode="HTML"
                    )
                else:
                    await bot.edit_message_text(
                        chat_id=skupper_id,
                        message_id=message_id,
                        text=f"❌ <b>ЗАКАЗ #{order.order_id} УЖЕ ВЗЯТ</b>\n\n"
                             f"⚠️ Этот заказ уже принят другим скупом",
                        parse_mode="HTML"
                    )
            elif order.status == "cancelled":
                await bot.edit_message_text(
                    chat_id=skupper_id,
                    message_id=message_id,
                    text=f"🚫 <b>ЗАКАЗ #{order.order_id} ОТМЕНЕН</b>\n\n"
                         f"⚠️ Клиент отменил эту заявку",
                    parse_mode="HTML"
                )

        except Exception as e:
            print(f"Не могу обновить сообщение скупу {skupper_id}: {e}")


async def notify_user_order_accepted(order, skupper_name, skupper_username):
    """Уведомить пользователя, что заказ принят (ПОЛЬЗОВАТЕЛЬ ПИШЕТ САМ)"""
    try:
        skupper = next((s for s in SKUPPERS if s["id"] == order.accepted_by), None)

        if not skupper:
            contact_info = "не указан"
        else:
            contact_info = skupper["username"]
            order.skupper_username = contact_info  # Сохраняем username скупа

        server_info = f"\n🌐 Сервер: {order.server}" if order.server else ""

        # Добавляем информацию о цене
        price_info = f"\n💰 Ваша цена: {format_number_with_spaces(order.price)} ₽" if order.price else ""

        # ВАЖНО: Пользователь видит username скупа и должен написать САМ
        await bot.send_message(
            chat_id=order.user_id,
            text=f"🎉 <b>ЗАЯВКА #{order.order_id} ПРИНЯТА!</b>\n\n"
                 f"👤 <b>Скупщик:</b> {skupper_name}\n"
                 f"📱 <b>Контакт для связи:</b> {contact_info}\n"
                 f"{server_info}{price_info}\n\n"
                 f"💬 <b>ВАЖНО: Напишите скупщику САМИ!</b>\n"
                 f"1. Нажмите на username: {contact_info}\n"
                 f"2. Напишите ему в личные сообщения\n"
                 f"3. Сообщите номер заказа: #{order.order_id}\n\n"
                 f"<i>Скупщик ожидает вашего сообщения</i>",
            parse_mode="HTML",
            reply_markup=get_main_keyboard(order.user_id)
        )

        if order.cancel_button_message_id:
            try:
                await bot.delete_message(
                    chat_id=order.user_id,
                    message_id=order.cancel_button_message_id
                )
            except:
                pass

    except Exception as e:
        print(f"Не могу уведомить пользователя о принятии: {e}")


async def notify_user_order_cancelled(order):
    """Уведомить пользователя об отмене заявки"""
    try:
        await bot.send_message(
            chat_id=order.user_id,
            text=f"🚫 <b>Заявка #{order.order_id} отменена</b>\n\n"
                 f"Вы отменили свою заявку на продажу.",
            parse_mode="HTML",
            reply_markup=get_main_keyboard(order.user_id)
        )
    except Exception as e:
        print(f"Не могу уведомить об отмене: {e}")


async def start_order_expire_timer(order_id):
    """Таймер истечения заявки"""
    try:
        await asyncio.sleep(ORDER_EXPIRE_TIME * 60)

        order = orders.get(order_id)
        if not order or order.status != "active":
            return

        order.status = "expired"

        try:
            await bot.send_message(
                chat_id=order.user_id,
                text=f"⏰ <b>Заявка #{order_id} истекла</b>\n\n"
                     f"Прошло {ORDER_EXPIRE_TIME} минут, заявка автоматически удалена.\n"
                     f"Создайте новую заявку, если нужно.",
                parse_mode="HTML",
                reply_markup=get_main_keyboard(order.user_id)
            )
        except:
            pass

        if order.cancel_button_message_id:
            try:
                await bot.delete_message(
                    chat_id=order.user_id,
                    message_id=order.cancel_button_message_id
                )
            except:
                pass

        await update_skupper_messages(order)
        await log_order_expired(order)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Ошибка в таймере заявки #{order_id}: {e}")


# ===== ОБРАБОТЧИКИ ДЛЯ ПРОДАЖИ =====
@dp.message(F.text == "🏠 Продать дом")
async def sell_house_handler(message: types.Message, state: FSMContext):
    """Обработчик продажи дома"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    # Проверяем анти-спам
    is_allowed, error_msg = await check_anti_spam(user_id, username)
    if not is_allowed:
        await message.answer(error_msg, parse_mode="HTML")
        return

    # Показываем выбор дома с красивым оформлением
    await message.answer(
        "🏠 <b>Выберите дом для продажи:</b>\n\n"
        "<i>Выберите один из доступных домов:</i>",
        parse_mode="HTML",
        reply_markup=get_houses_keyboard()
    )
    await state.set_state(OrderStates.choosing_house)


@dp.message(F.text == "💎 Продать вирты")
async def sell_virts_handler(message: types.Message, state: FSMContext):
    """Обработчик продажи виртов"""
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    # Проверяем анти-спам
    is_allowed, error_msg = await check_anti_spam(user_id, username)
    if not is_allowed:
        await message.answer(error_msg, parse_mode="HTML")
        return

    # Просим ввести сумму виртов с примерами
    await message.answer(
        "💎 <b>Введите сумму виртов для продажи:</b>\n\n"
        "💰 <b>Минимум:</b> 3 000 000 (3кк)\n\n"
        "📝 <b>Примеры форматов:</b>\n"
        "• 15 000 000\n"
        "• 10кк\n"
        "• 5.5кк\n"
        "• 5000000\n"
        "• 7.5кк\n\n"
        "❌ <b>Для отмены введите /cancel</b>",
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.waiting_for_virt_amount)


@dp.message(OrderStates.waiting_for_virt_amount)
async def process_virt_amount(message: types.Message, state: FSMContext):
    """Обработка введенной суммы виртов"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Отменено",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    # Парсим сумму виртов
    amount = parse_amount(message.text)

    if amount is None:
        await message.answer(
            "❌ <b>Неверный формат суммы!</b>\n\n"
            "Введите сумму в одном из форматов:\n"
            "• 15 000 000\n"
            "• 10кк\n"
            "• 5.5кк\n\n"
            "❌ Для отмены введите /cancel",
            parse_mode="HTML"
        )
        return

    # Проверяем минимальную сумму
    if amount < 3000000:
        await message.answer(
            "❌ <b>Слишком маленькая сумма!</b>\n\n"
            "Минимальная сумма для продажи: 3 000 000 виртов (3кк)\n\n"
            "❌ Для отмены введите /cancel",
            parse_mode="HTML"
        )
        return

    # Сохраняем сумму и просим ввести цену
    await state.update_data(virt_amount=amount)

    await message.answer(
        "💰 <b>Введите желаемую цену в рублях:</b>\n\n"
        "<i>Укажите, за сколько хотите продать вирты.</i>\n\n"
        "📝 <b>Примеры:</b>\n"
        "• 1000\n"
        "• 1500.50\n"
        "• 2500\n"
        "• 500\n\n"
        "❌ Для отмены введите /cancel",
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.waiting_for_virt_price)


@dp.message(OrderStates.waiting_for_virt_price)
async def process_virt_price(message: types.Message, state: FSMContext):
    """Обработка введенной цены для виртов"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Отменено",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    # Парсим цену
    price = parse_price(message.text)

    if price is None:
        await message.answer(
            "❌ <b>Неверный формат цены!</b>\n\n"
            "Введите цену в рублях (только цифры):\n"
            "• 1000\n"
            "• 1500.50\n"
            "• 2500\n\n"
            "❌ Для отмены введите /cancel",
            parse_mode="HTML"
        )
        return

    # Проверяем, что цена положительная
    if price <= 0:
        await message.answer(
            "❌ <b>Цена должна быть больше 0!</b>\n\n"
            "Введите корректную цену в рублях.\n\n"
            "❌ Для отмены введите /cancel",
            parse_mode="HTML"
        )
        return

    # Сохраняем цену и просим выбрать сервер
    await state.update_data(virt_price=price)

    data = await state.get_data()
    virt_amount = data.get("virt_amount")

    await message.answer(
        f"💎 <b>Вы хотите продать:</b> {format_amount(virt_amount)} виртов\n"
        f"💰 <b>За сумму:</b> {format_number_with_spaces(price)} ₽\n\n"
        f"🌐 <b>Теперь выберите сервер:</b>",
        parse_mode="HTML",
        reply_markup=get_servers_keyboard("server_virts")
    )
    await state.set_state(OrderStates.waiting_for_server_virts)


# ===== ОБРАБОТЧИКИ ДЛЯ ВЫБОРА ДОМА =====
@dp.callback_query(F.data.startswith("house_"))
async def house_selected_handler(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора дома"""
    if callback.data == "cancel_house":
        await state.clear()
        await callback.message.edit_text("❌ Отменено")
        await callback.answer()
        return

    house_name = callback.data.replace("house_", "")
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name

    # Проверяем анти-спам
    is_allowed, error_msg = await check_anti_spam(user_id, username)
    if not is_allowed:
        await callback.answer(error_msg, show_alert=True)
        return

    # Сохраняем выбранный дом и просим указать цену
    await state.update_data(selected_house=house_name)

    await callback.message.edit_text(
        f"🏠 <b>Вы выбрали дом:</b> {house_name}\n\n"
        f"💰 <b>Введите желаемую цену в рублях:</b>\n\n"
        f"<i>Укажите, за сколько хотите продать дом.</i>\n\n"
        f"📝 <b>Примеры:</b>\n"
        f"• 5000\n"
        f"• 7500.50\n"
        f"• 10000\n"
        f"• 1500\n\n"
        f"❌ Для отмены введите /cancel",
        parse_mode="HTML"
    )
    await state.set_state(OrderStates.waiting_for_house_price)
    await callback.answer()


@dp.message(OrderStates.waiting_for_house_price)
async def process_house_price(message: types.Message, state: FSMContext):
    """Обработка введенной цены для дома"""
    if message.text == "/cancel":
        await state.clear()
        await message.answer(
            "❌ Отменено",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return

    # Парсим цену
    price = parse_price(message.text)

    if price is None:
        await message.answer(
            "❌ <b>Неверный формат цены!</b>\n\n"
            "Введите цену в рублях (только цифры):\n"
            "• 5000\n"
            "• 7500.50\n"
            "• 10000\n\n"
            "❌ Для отмены введите /cancel",
            parse_mode="HTML"
        )
        return

    # Проверяем, что цена положительная
    if price <= 0:
        await message.answer(
            "❌ <b>Цена должна быть больше 0!</b>\n\n"
            "Введите корректную цену в рублях.\n\n"
            "❌ Для отмены введите /cancel",
            parse_mode="HTML"
        )
        return

    # Сохраняем цену и просим выбрать сервер
    await state.update_data(house_price=price)

    data = await state.get_data()
    house_name = data.get("selected_house")

    await message.answer(
        f"🏠 <b>Вы хотите продать дом:</b> {house_name}\n"
        f"💰 <b>За сумму:</b> {format_number_with_spaces(price)} ₽\n\n"
        f"🌐 <b>Теперь выберите сервер:</b>",
        parse_mode="HTML",
        reply_markup=get_servers_keyboard("server_house")
    )
    await state.set_state(OrderStates.waiting_for_server_house)


# ===== ОБРАБОТЧИКИ ДЛЯ ВЫБОРА СЕРВЕРА =====
@dp.callback_query(F.data.startswith("server_virts_"))
async def server_selected_for_virts(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора сервера для виртов"""
    if callback.data == "cancel_server":
        await state.clear()
        await callback.message.edit_text("❌ Отменено")
        await callback.answer()
        return

    server = callback.data.replace("server_virts_", "")
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name

    # Получаем сохраненные данные
    data = await state.get_data()
    virt_amount = data.get("virt_amount")
    virt_price = data.get("virt_price")

    if not virt_amount or not virt_price:
        await callback.answer("❌ Ошибка: данные не найдены", show_alert=True)
        return

    # Проверяем анти-спам
    is_allowed, error_msg = await check_anti_spam(user_id, username)
    if not is_allowed:
        await callback.answer(error_msg, show_alert=True)
        return

    # Создаем заказ
    await create_order(
        user_id=user_id,
        username=username,
        order_type="virts",
        details=format_amount(virt_amount),
        server=server,
        price=virt_price,
        callback=callback
    )
    await state.clear()


@dp.callback_query(F.data.startswith("server_house_"))
async def server_selected_for_house(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора сервера для дома"""
    if callback.data == "cancel_server":
        await state.clear()
        await callback.message.edit_text("❌ Отменено")
        await callback.answer()
        return

    server = callback.data.replace("server_house_", "")
    user_id = callback.from_user.id
    username = callback.from_user.username or callback.from_user.first_name

    # Получаем сохраненные данные
    data = await state.get_data()
    house_name = data.get("selected_house")
    house_price = data.get("house_price")

    if not house_name or not house_price:
        await callback.answer("❌ Ошибка: данные не найдены", show_alert=True)
        return

    # Проверяем анти-спам
    is_allowed, error_msg = await check_anti_spam(user_id, username)
    if not is_allowed:
        await callback.answer(error_msg, show_alert=True)
        return

    # Создаем заказ
    await create_order(
        user_id=user_id,
        username=username,
        order_type="house",
        details=house_name,
        server=server,
        price=house_price,
        callback=callback
    )
    await state.clear()


async def create_order(user_id, username, order_type, details, server, price, callback=None):
    """Создает новый заказ с указанием цены"""
    global order_counter

    # Обновляем анти-спам счетчик
    await update_anti_spam(user_id)

    # Создаем заказ
    order_id = order_counter
    order_counter += 1

    order = Order(
        order_id=order_id,
        user_id=user_id,
        username=username,
        order_type=order_type,
        details=details,
        server=server,
        price=price
    )

    orders[order_id] = order

    # Рассылаем скупам
    sent_count, sent_to_list = await broadcast_order_to_all_skuppers(order)

    # Уведомляем пользователя
    await notify_user_order_created(order, sent_count, sent_to_list)

    # Уведомляем владельца
    await log_order_created(order, sent_count)

    # Запускаем таймер истечения
    asyncio.create_task(start_order_expire_timer(order_id))

    # Отправляем сообщение об успехе
    if callback:
        success_text = f"✅ <b>Заявка #{order_id} создана!</b>\n\n"
        if order_type == "house":
            success_text += f"🏠 Дом: {details}\n"
        else:
            success_text += f"💎 Сумма: {details}\n"

        success_text += f"💰 Цена: {format_number_with_spaces(price)} ₽\n"
        success_text += f"🌐 Сервер: {server}\n"
        success_text += f"📨 Отправлено скупам: {sent_count}\n\n"
        success_text += f"<i>Ожидайте ответа от скупщиков...</i>"

        await callback.message.edit_text(success_text, parse_mode="HTML")
        await callback.answer()


# ===== ОБРАБОТЧИК ОТМЕНЫ ЗАКАЗА =====
@dp.callback_query(F.data.startswith("cancel_order_"))
async def cancel_order_handler(callback: CallbackQuery):
    """Обработчик отмены заказа пользователем"""
    order_id = int(callback.data.replace("cancel_order_", ""))
    user_id = callback.from_user.id

    order = orders.get(order_id)

    if not order:
        await callback.answer("Заявка не найдена!", show_alert=True)
        return

    if order.user_id != user_id:
        await callback.answer("Это не ваша заявка!", show_alert=True)
        return

    if order.status != "active":
        await callback.answer("Заявка уже обработана!", show_alert=True)
        return

    order.status = "cancelled"

    await update_skupper_messages(order)
    await notify_user_order_cancelled(order)
    await log_order_cancelled(order)

    await callback.answer(f"Заявка #{order_id} отменена", show_alert=True)


# ===== ОБРАБОТЧИК ПРИНЯТИЯ ЗАКАЗА =====
@dp.callback_query(F.data.startswith("take_order_"))
async def take_order_handler(callback: CallbackQuery):
    """Скуп принимает заказ (ВАЖНО: скуп НЕ пишет пользователю)"""
    order_id = int(callback.data.replace("take_order_", ""))
    skupper_id = callback.from_user.id
    skupper_name = callback.from_user.username or callback.from_user.first_name
    skupper_username = callback.from_user.username or "без username"

    order = orders.get(order_id)

    if not order:
        await callback.answer("Заявка не найдена или уже обработана!", show_alert=True)
        return

    if order.status != "active":
        await callback.answer("Эта заявка уже обработана!", show_alert=True)
        return

    if not any(s["id"] == skupper_id for s in SKUPPERS):
        await callback.answer("Вы не скупщик!", show_alert=True)
        return

    order.status = "accepted"
    order.accepted_by = skupper_id
    order.skupper_username = skupper_username  # Сохраняем username скупа

    await update_skupper_messages(order, skupper_id)
    await notify_user_order_accepted(order, skupper_name, skupper_username)

    # Логируем принятие заказа
    skupper_info = f"{skupper_name} (@{skupper_username})"
    await log_order_accepted(order, skupper_info)

    await callback.answer(f"✅ Вы приняли заказ #{order_id}!", show_alert=True)


# ===== КОМАНДА /cancel =====
@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Отмена текущего действия"""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("❌ Нечего отменять")
        return

    await state.clear()
    await message.answer(
        "❌ Действие отменено",
        reply_markup=get_main_keyboard(message.from_user.id)
    )


# ===== ОБРАБОТЧИКИ ДЛЯ ЛОГОВ =====
@dp.message(F.text == "📊 Логи заказов")
async def show_logs_menu(message: types.Message):
    """Показывает меню логов (только владельцу)"""
    if message.from_user.id != OWNER_ID:
        await message.answer("⛔ У вас нет доступа к этой команде.")
        return

    await message.answer(
        "📊 <b>Меню управления логами</b>\n\n"
        "Выберите действие:",
        parse_mode="HTML",
        reply_markup=get_logs_keyboard()
    )


@dp.callback_query(F.data.startswith("logs_"))
async def logs_menu_handler(callback: CallbackQuery):
    """Обработчик меню логов"""
    if callback.from_user.id != OWNER_ID:
        await callback.answer("⛔ У вас нет доступа", show_alert=True)
        return

    action = callback.data

    if action == "logs_stats":
        # Статистика за сегодня
        stats = await get_today_stats()

        today = datetime.now().strftime("%d.%m.%Y")
        message_text = (
            f"📊 <b>СТАТИСТИКА ЗА СЕГОДНЯ ({today})</b>\n\n"
            f"📈 <b>Общая статистика:</b>\n"
            f"• Всего заявок: {stats['total']}\n"
            f"• Активные: {stats['active']}\n"
            f"• Принятые: {stats['accepted']}\n"
            f"• Отмененные: {stats['cancelled']}\n"
            f"• Истекшие: {stats['expired']}\n\n"
            f"🏷️ <b>По типам:</b>\n"
            f"• Домов: {stats['houses']}\n"
            f"• Виртов: {stats['virts']}\n\n"
            f"💰 <b>Общая сумма:</b>\n"
            f"• {format_number_with_spaces(stats['total_price'])} ₽"
        )

        await callback.message.edit_text(message_text, parse_mode="HTML")

    elif action == "logs_today":
        # Логи за сегодня
        today = datetime.now().strftime("%Y-%m-%d")
        filename = f"logs/orders_{today}.json"

        if not os.path.exists(filename):
            await callback.message.edit_text(
                f"📅 <b>Логи за сегодня ({datetime.now().strftime('%d.%m.%Y')})</b>\n\n"
                f"📭 Нет данных за сегодня.",
                parse_mode="HTML"
            )
            return

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                logs = json.load(f)

            if not logs:
                await callback.message.edit_text(
                    f"📅 <b>Логи за сегодня ({datetime.now().strftime('%d.%m.%Y')})</b>\n\n"
                    f"📭 Нет данных за сегодня.",
                    parse_mode="HTML"
                )
                return

            # Показываем последние 10 заказов
            recent_logs = logs[-10:] if len(logs) > 10 else logs
            message_text = f"📅 <b>Логи за сегодня ({datetime.now().strftime('%d.%m.%Y')})</b>\n\n"
            message_text += f"📊 Всего записей: {len(logs)}\n\n"

            for log in reversed(recent_logs):
                emoji = "🏠" if log.get("order_type") == "house" else "💎"
                status_emoji = "🟢" if log.get("status") == "active" else \
                    "✅" if log.get("status") == "accepted" else \
                        "❌" if log.get("status") == "cancelled" else "⏰"

                price_text = f"💰 {format_number_with_spaces(log.get('price', 0))} ₽" if log.get("price") else ""

                message_text += (
                    f"{status_emoji} <b>Заказ #{log['order_id']}</b>\n"
                    f"{emoji} {log.get('details', 'N/A')}\n"
                    f"👤 {log.get('username', 'N/A')}\n"
                    f"{price_text}\n"
                    f"⏰ {log.get('timestamp', 'N/A')}\n"
                    f"─────────────────\n"
                )

            await callback.message.edit_text(message_text, parse_mode="HTML")

        except Exception as e:
            await callback.message.edit_text(
                f"❌ <b>Ошибка при чтении логов:</b>\n{str(e)}",
                parse_mode="HTML"
            )

    elif action == "logs_all":
        # Общая статистика
        stats = await get_all_logs_stats()

        message_text = (
            f"📁 <b>ОБЩАЯ СТАТИСТИКА</b>\n\n"
            f"📈 <b>За все время:</b>\n"
            f"• Всего заявок: {stats['total_orders']}\n"
            f"• Принято: {stats['total_accepted']}\n"
            f"• Отменено: {stats['total_cancelled']}\n"
            f"• Истекло: {stats['total_expired']}\n\n"
            f"🏷️ <b>По типам:</b>\n"
            f"• Домов: {stats['total_houses']}\n"
            f"• Виртов: {stats['total_virts']}\n\n"
            f"📅 <b>Дней с логами:</b> {stats['days_with_logs']}\n"
            f"💰 <b>Общая сумма:</b>\n"
            f"• {format_number_with_spaces(stats['total_price'])} ₽"
        )

        await callback.message.edit_text(message_text, parse_mode="HTML")

    elif action == "logs_clear":
        # Очистка старых логов
        deleted = await clear_old_logs(30)

        await callback.message.edit_text(
            f"🗑️ <b>Очистка логов</b>\n\n"
            f"✅ Удалено файлов: {deleted}\n"
            f"📅 Удалены логи старше 30 дней.",
            parse_mode="HTML"
        )

    elif action == "logs_close":
        await callback.message.delete()
        await callback.answer()
        return

    await callback.answer()


# ===== ОСНОВНЫЕ КОМАНДЫ =====
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    await message.answer(
        "👋 <b>Добро пожаловать в бот для продажи!</b>\n\n"
        "🏠 <b>Продать дом</b> - выберите дом и укажите цену\n"
        "💎 <b>Продать вирты</b> - введите сумму и цену\n\n"
        "🎯 <b>Как это работает:</b>\n"
        "1. Выбираете что продавать\n"
        "2. Указываете желаемую цену\n"
        "3. Выбираете сервер\n"
        "4. Заявка отправляется ВСЕМ скупам\n"
        "5. Скуп принимает заявку\n"
        "6. Вы видите username скупа\n"
        "7. <b>Вы пишете скупу САМИ</b>\n"
        "8. Обсуждаете сделку в личных сообщениях\n\n"
        "⚠️ <b>Важно:</b>\n"
        f"• Заявка активна {ORDER_EXPIRE_TIME} минут\n"
        f"• Лимит заявок в день: {MAX_ORDERS_PER_DAY}\n"
        "• Цена указывается в рублях\n"
        "• Скуп видит вашу желаемую цену",
        parse_mode="HTML",
        reply_markup=get_main_keyboard(user_id)
    )


# ===== ЗАПУСК БОТА =====
async def main():
    logging.basicConfig(level=logging.INFO)

    # Создаем директорию для логов
    ensure_logs_directory()

    print("=" * 60)
    print("🤖 БОТ ДЛЯ ПРОДАЖИ ДОМОВ И ВИРТОВ")
    print("=" * 60)
    print(f"🔑 Токен: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")
    print(f"👑 Владелец: {OWNER_ID}")
    print(f"👥 Скупщиков: {len(SKUPPERS)}")
    print(f"🌐 Серверов: {len(SERVERS)}")
    print(f"⏰ Время жизни заявки: {ORDER_EXPIRE_TIME} минут")
    print(f"🛡️  Анти-спам: {MAX_ORDERS_PER_DAY} заявок/день, {ORDER_COOLDOWN // 60} мин кулдаун")
    print("=" * 60)
    print("💰 НОВАЯ ФУНКЦИЯ:")
    print("• Пользователи указывают желаемую цену")
    print("• Скупы видят цену пользователя")
    print("• Поддержка форматов: 15.000.000, 10кк, 5.5кк")
    print("=" * 60)
    print("🔒 ЗАЩИТА ОТ СПАМ-БЛОКИРОВОК:")
    print("• Скупы НЕ видят username пользователей")
    print("• Пользователи видят username скупов")
    print("• Пользователи пишут скупам САМИ")
    print("• Скупы не пишут пользователям первыми")
    print("=" * 60)
    print("📊 Система логов включена")
    print("📁 Логи сохраняются в папке logs/")
    print("=" * 60)
    print("🚀 Бот запущен! Ожидание команд...")
    print("=" * 60)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")


if __name__ == "__main__":
    asyncio.run(main())
