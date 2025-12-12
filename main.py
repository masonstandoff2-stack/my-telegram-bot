import asyncio
import logging
import sqlite3
import re
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ===== КОНФИГУРАЦИЯ =====
BOT_TOKEN = "8547560915:AAFvrXGPcyz2tZinaKTjlrEBujSpNt3pSUQ"
ADMIN_IDS = [8577578314, 5012040224]
CHANNEL_ID = -1002742100828
CHANNEL_LINK = "https://t.me/+PuuOCG7tIYc5YmM6"
SOFTWARE_PRICE = "200 рублей"

MAX_VIRTS = 800000000
MAX_PRICE = 100000
REFERRAL_REWARD = 2000000  # 1кк за 15 приглашенных
REFERRAL_THRESHOLD = 15  # Сколько нужно пригласить

PAYMENT_DETAILS = {
    "phone": "+79093963083",
    "name": "Семён К",
    "bank": "Тинькофф",
    "note": "После оплаты отправьте чек в бота"
}

BR_SERVERS = [
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)


async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Ошибка проверки подписки: {e}")
        return False


def get_subscription_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="📢 Подписаться", url=CHANNEL_LINK))
    keyboard.row(InlineKeyboardButton(text="✅ Проверить", callback_data="check_subscription"))
    return keyboard.as_markup()


class Database:
    def __init__(self):
        self.conn = sqlite3.connect('shop.db')
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        """Создает все необходимые таблицы в базе данных"""
        try:
            # Таблица accounts_shop для магазина аккаунтов
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts_shop (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    category TEXT DEFAULT 'standart',
                    level INTEGER DEFAULT 1,
                    virt_amount TEXT DEFAULT '',
                    bindings TEXT DEFAULT '',
                    contacts TEXT,
                    photo_file_id TEXT,
                    created_at DATETIME,
                    is_active BOOLEAN DEFAULT 1,
                    sold_to INTEGER DEFAULT 0,
                    sold_at DATETIME
                )
            """)
            logger.info("✅ Таблица accounts_shop создана")

            # Таблица accounts_for_sale для старых объявлений
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS accounts_for_sale (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server TEXT,
                    description TEXT,
                    price TEXT,
                    contacts TEXT,
                    photo_file_id TEXT,
                    created_at DATETIME,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            logger.info("✅ Таблица accounts_for_sale создана")

            # Таблица orders
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    full_name TEXT,
                    order_type TEXT,
                    server TEXT,
                    amount TEXT,
                    price TEXT,
                    description TEXT,
                    contacts TEXT,
                    payment_method TEXT,
                    status TEXT DEFAULT 'new',
                    has_receipt BOOLEAN DEFAULT 0,
                    receipt_file_id TEXT,
                    created_at DATETIME
                )
            """)
            logger.info("✅ Таблица orders создана")

            # Таблица sell_requests
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS sell_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    full_name TEXT,
                    server TEXT,
                    description TEXT,
                    price TEXT,
                    contacts TEXT,
                    photo_file_id TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME
                )
            """)
            logger.info("✅ Таблица sell_requests создана")

            # Таблица users
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    reg_date DATETIME,
                    has_subscribed BOOLEAN DEFAULT 0,
                    referrer_id INTEGER DEFAULT 0,
                    referral_count INTEGER DEFAULT 0,
                    got_referral_reward BOOLEAN DEFAULT 0
                )
            """)
            logger.info("✅ Таблица users создана")

            # Таблица referral_rewards
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS referral_rewards (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    reward_amount INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME
                )
            """)
            logger.info("✅ Таблица referral_rewards создана")

            # Таблица broadcasts для истории рассылок
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS broadcasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    admin_id INTEGER NOT NULL,
                    admin_name TEXT,
                    message_text TEXT NOT NULL,
                    total_users INTEGER DEFAULT 0,
                    sent_success INTEGER DEFAULT 0,
                    sent_failed INTEGER DEFAULT 0,
                    blocked_users INTEGER DEFAULT 0,
                    created_at DATETIME,
                    status TEXT DEFAULT 'completed'
                )
            """)
            logger.info("✅ Таблица broadcasts создана")

            self.conn.commit()
            logger.info("✅ Все таблицы успешно созданы")

        except Exception as e:
            logger.error(f"❌ Ошибка создания таблиц: {e}")
            import traceback
            logger.error(f"Трассировка: {traceback.format_exc()}")
            raise

    def get_shop_accounts_for_gallery(self):
        """Получает аккаунты для галереи (магазина)"""
        try:
            self.cursor.execute("""
                SELECT id, server, title, description, price, category, level, 
                       virt_amount, bindings, contacts, photo_file_id, created_at
                FROM accounts_shop 
                WHERE is_active = 1 AND sold_to = 0
                ORDER BY created_at DESC
            """)
            accounts = self.cursor.fetchall()
            logger.info(f"✅ Получено {len(accounts)} аккаунтов для галереи")
            return accounts
        except Exception as e:
            logger.error(f"Ошибка получения аккаунтов для галереи: {e}")
            return []

    def add_broadcast_history(self, admin_id, admin_name, message_text, total_users,
                              sent_success, sent_failed, blocked_users, status='completed'):
        """Добавляет запись о рассылке в историю"""
        try:
            self.cursor.execute("""
                INSERT INTO broadcasts 
                (admin_id, admin_name, message_text, total_users, sent_success, 
                 sent_failed, blocked_users, created_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (admin_id, admin_name, message_text, total_users, sent_success,
                  sent_failed, blocked_users, datetime.now(), status))

            self.conn.commit()
            broadcast_id = self.cursor.lastrowid

            logger.info(f"✅ История рассылки #{broadcast_id} сохранена")
            return broadcast_id

        except Exception as e:
            logger.error(f"❌ Ошибка сохранения истории рассылки: {e}")
            return None



    def update_shop_account_field(self, account_id, field, value):
        """Обновляет конкретное поле аккаунта в магазине"""
        try:
            # Список разрешенных полей для обновления
            allowed_fields = ['title', 'description', 'price', 'server', 'category',
                              'level', 'virt_amount', 'bindings', 'contacts']

            if field not in allowed_fields:
                logger.error(f"Недопустимое поле для обновления: {field}")
                return False

            # Для ценового поля преобразуем значение
            if field == 'price':
                if isinstance(value, str):
                    # Очищаем от нецифровых символов
                    value_clean = ''.join(filter(str.isdigit, value))
                    if not value_clean:
                        logger.error("❌ Неверное значение цены")
                        return False
                    value = int(value_clean)

            query = f"UPDATE accounts_shop SET {field} = ? WHERE id = ?"
            self.cursor.execute(query, (value, account_id))
            self.conn.commit()

            updated = self.cursor.rowcount > 0

            if updated:
                logger.info(f"✅ Поле '{field}' аккаунта #{account_id} обновлено")
            else:
                logger.error(f"❌ Не удалось обновить поле '{field}' аккаунта #{account_id}")

            return updated
        except Exception as e:
            logger.error(f"❌ Ошибка обновления поля '{field}' аккаунта #{account_id}: {e}")
            import traceback
            logger.error(f"Трассировка: {traceback.format_exc()}")
            return False



    def add_account_to_shop(self, server, title, description, price, contacts='',
                            category='standart', level=1, virt_amount='', bindings='',
                            photo_file_id=None):
        """Добавляет аккаунт в магазин"""
        try:
            # ПРОВЕРКА ОБЯЗАТЕЛЬНЫХ ПОЛЕЙ
            if not server or not title or not description:
                logger.error("❌ Обязательные поля не заполнены (server, title, description)")
                return None

            # Преобразуем цену в целое число если это строка
            if isinstance(price, str):
                # Убираем все нецифровые символы
                price_clean = ''.join(filter(str.isdigit, price))
                if not price_clean:  # Если после очистки пустая строка
                    price_clean = '0'
                price_int = int(price_clean)
            elif isinstance(price, (int, float)):
                price_int = int(price)
            else:
                logger.error(f"Неверный тип цены: {type(price)}")
                return None

            logger.info(
                f"Добавление аккаунта в магазин: server={server}, title={title}, price={price_int}, contacts={contacts}")

            # ВАЖНО: количество параметров должно совпадать с количеством ?
            self.cursor.execute("""
                INSERT INTO accounts_shop 
                (server, title, description, price, category, level, virt_amount, 
                 bindings, contacts, photo_file_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (server, title, description, price_int, category, level, virt_amount,
                  bindings, contacts, photo_file_id, datetime.now()))

            self.conn.commit()

            account_id = self.cursor.lastrowid
            logger.info(f"✅ Аккаунт успешно добавлен в магазин с ID: {account_id}")
            return account_id
        except Exception as e:
            logger.error(f"Ошибка добавления аккаунта в магазин: {e}")
            import traceback
            logger.error(f"Трассировка ошибки: {traceback.format_exc()}")
            return None

    def get_shop_accounts_paginated(self, page=0, per_page=5):
        """Получает аккаунты из магазина с пагинацией"""
        try:
            offset = page * per_page
            self.cursor.execute("""
                SELECT id, server, title, description, price, category, level, 
                       virt_amount, bindings, contacts, photo_file_id, created_at
                FROM accounts_shop 
                WHERE is_active = 1 AND sold_to = 0
                ORDER BY price ASC, created_at DESC
                LIMIT ? OFFSET ?
            """, (per_page, offset))
            accounts = self.cursor.fetchall()

            # Получаем общее количество для пагинации
            self.cursor.execute("""
                SELECT COUNT(*) FROM accounts_shop 
                WHERE is_active = 1 AND sold_to = 0
            """)
            total = self.cursor.fetchone()[0]

            return {
                'accounts': accounts,
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page
            }
        except Exception as e:
            logger.error(f"Ошибка получения аккаунтов с пагинацией: {e}")
            return {'accounts': [], 'total': 0, 'page': 0, 'per_page': per_page, 'total_pages': 0}

    def get_shop_accounts(self, server=None, category=None, min_price=0, max_price=1000000):
        """Получает доступные аккаунты из магазина с фильтрами"""
        try:
            query = """
                SELECT id, server, title, description, price, category, level, 
                       virt_amount, bindings, contacts, photo_file_id, created_at
                FROM accounts_shop 
                WHERE is_active = 1 AND sold_to = 0
            """
            params = []

            if server:
                query += " AND server = ?"
                params.append(server)

            if category:
                query += " AND category = ?"
                params.append(category)

            query += " AND price >= ? AND price <= ?"
            params.extend([min_price, max_price])

            query += " ORDER BY price ASC, created_at DESC"

            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения аккаунтов из магазина: {e}")
            return []

    def get_shop_account_by_id(self, account_id, check_sold=True):
        """Получает аккаунт из магазина по ID"""
        try:
            logger.info(f"Запрос аккаунта #{account_id}, check_sold={check_sold}")

            if check_sold:
                # Проверяем, не продан ли аккаунт
                query = """
                    SELECT id, server, title, description, price, category, level, 
                           virt_amount, bindings, contacts, photo_file_id, created_at
                    FROM accounts_shop 
                    WHERE id = ? AND is_active = 1 AND sold_to = 0
                """
            else:
                # Просто получаем данные аккаунта (для просмотра администратором)
                query = """
                    SELECT id, server, title, description, price, category, level, 
                           virt_amount, bindings, contacts, photo_file_id, created_at
                    FROM accounts_shop 
                    WHERE id = ? AND is_active = 1
                """

            self.cursor.execute(query, (account_id,))
            result = self.cursor.fetchone()

            if result:
                logger.info(f"✅ Найден аккаунт #{account_id}: {result[1]} - {result[2][:30]}")
            else:
                logger.info(f"❌ Аккаунт #{account_id} не найден или продан")

            return result
        except Exception as e:
            logger.error(f"Ошибка получения аккаунта из магазина: {e}")
            import traceback
            logger.error(f"Трассировка: {traceback.format_exc()}")
            return None

    def is_account_sold(self, account_id):
        """Проверяет, продан ли аккаунт"""
        try:
            self.cursor.execute("SELECT sold_to FROM accounts_shop WHERE id = ?", (account_id,))
            result = self.cursor.fetchone()

            if result:
                sold_to = result[0]
                return sold_to != 0  # True если продан (sold_to не равен 0)

            return False  # Не найден или не продан
        except Exception as e:
            logger.error(f"Ошибка проверки продажи аккаунта: {e}")
            return False


    def clear_all_shop_accounts(self):
        """Удаляет ВСЕ активные аккаунты из магазина"""
        try:
            # Получаем количество аккаунтов до удаления
            self.cursor.execute("SELECT COUNT(*) FROM accounts_shop WHERE is_active = 1 AND sold_to = 0")
            count_before = self.cursor.fetchone()[0]

            # Если нет аккаунтов, возвращаем 0
            if count_before == 0:
                logger.info("✅ Нет активных аккаунтов для удаления")
                return 0

            # Удаляем все активные аккаунты
            self.cursor.execute("DELETE FROM accounts_shop WHERE is_active = 1 AND sold_to = 0")
            self.conn.commit()

            deleted_count = self.cursor.rowcount
            logger.info(f"✅ Удалено {deleted_count} аккаунтов из магазина (было {count_before})")

            return deleted_count
        except Exception as e:
            logger.error(f"❌ Ошибка удаления всех аккаунтов: {e}")
            import traceback
            logger.error(f"Трассировка: {traceback.format_exc()}")
            return 0

    def delete_shop_account(self, account_id):
        """Удаляет конкретный аккаунт из магазина"""
        try:
            self.cursor.execute("DELETE FROM accounts_shop WHERE id = ?", (account_id,))
            self.conn.commit()
            deleted = self.cursor.rowcount > 0

            if deleted:
                logger.info(f"✅ Аккаунт #{account_id} успешно удален из магазина")
            else:
                logger.error(f"❌ Не удалось удалить аккаунт #{account_id}")

            return deleted
        except Exception as e:
            logger.error(f"❌ Ошибка удаления аккаунта #{account_id}: {e}")
            return False

    def mark_shop_account_sold(self, account_id, buyer_id):
        """Помечает аккаунт как проданный в магазине"""
        try:
            self.cursor.execute("""
                UPDATE accounts_shop 
                SET sold_to = ?, sold_at = ?, is_active = 0
                WHERE id = ? AND is_active = 1 AND sold_to = 0
            """, (buyer_id, datetime.now(), account_id))
            self.conn.commit()

            updated = self.cursor.rowcount > 0

            if updated:
                logger.info(f"✅ Аккаунт #{account_id} помечен как проданный покупателю {buyer_id}")
            else:
                logger.warning(f"⚠️ Не удалось пометить аккаунт #{account_id} как проданный")

            return updated
        except Exception as e:
            logger.error(f"Ошибка пометки аккаунта как проданного: {e}")
            return False

    def get_sold_shop_accounts(self):
        """Получает проданные аккаунты из магазина"""
        try:
            self.cursor.execute("""
                SELECT a.id, a.server, a.title, a.price, a.category, a.sold_at,
                       u.username, u.full_name, u.user_id
                FROM accounts_shop a
                LEFT JOIN users u ON a.sold_to = u.user_id
                WHERE a.sold_to != 0
                ORDER BY a.sold_at DESC
            """)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения проданных аккаунтов: {e}")
            return []



    def get_shop_accounts_for_navigation(self):
        """Получает все доступные аккаунты для навигации"""
        try:
            self.cursor.execute("""
                SELECT id, server, title, description, price, photo_file_id
                FROM accounts_shop 
                WHERE is_active = 1 AND sold_to = 0
                ORDER BY created_at DESC
            """)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения аккаунтов для навигации: {e}")
            return []

    def add_user(self, user_id, username, full_name, referrer_id=0):
        try:
            self.cursor.execute(
                """INSERT OR IGNORE INTO users (user_id, username, full_name, reg_date, referrer_id) 
                VALUES (?, ?, ?, ?, ?)""",
                (user_id, username, full_name, datetime.now(), referrer_id)
            )

            # Если указан реферер, увеличиваем его счетчик
            if referrer_id and referrer_id != user_id:
                self.cursor.execute(
                    "UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?",
                    (referrer_id,)
                )

                # Проверяем, достиг ли реферер порога для награды
                self.check_referral_reward(referrer_id)

            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка добавления пользователя: {e}")
            return False

    def check_referral_reward(self, user_id):
        """Проверяет, достиг ли пользователь порога для получения награды"""
        try:
            self.cursor.execute(
                "SELECT referral_count, got_referral_reward FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = self.cursor.fetchone()

            if result:
                referral_count, got_reward = result

                # Если пользователь пригласил достаточно людей и еще не получал награду
                if referral_count >= REFERRAL_THRESHOLD and not got_reward:
                    # Добавляем запрос на награду
                    self.cursor.execute(
                        """INSERT INTO referral_rewards (user_id, reward_amount, created_at)
                        VALUES (?, ?, ?)""",
                        (user_id, REFERRAL_REWARD, datetime.now())
                    )

                    # Помечаем, что пользователь получил награду
                    self.cursor.execute(
                        "UPDATE users SET got_referral_reward = 1 WHERE user_id = ?",
                        (user_id,)
                    )

                    self.conn.commit()
                    return True
            return False
        except Exception as e:
            logger.error(f"Ошибка проверки награды реферала: {e}")
            return False

    def get_user_referral_stats(self, user_id):
        """Получает статистику рефералов пользователя"""
        try:
            self.cursor.execute(
                "SELECT referral_count, got_referral_reward FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = self.cursor.fetchone()

            if result:
                referral_count, got_reward = result

                # Получаем список рефералов
                self.cursor.execute(
                    "SELECT user_id, username, full_name, reg_date FROM users WHERE referrer_id = ? ORDER BY reg_date DESC",
                    (user_id,)
                )
                referrals = self.cursor.fetchall()

                return {
                    'referral_count': referral_count,
                    'got_reward': bool(got_reward),
                    'referrals': referrals,
                    'needed': max(0, REFERRAL_THRESHOLD - referral_count)
                }
            return None
        except Exception as e:
            logger.error(f"Ошибка получения статистики рефералов: {e}")
            return None

    def get_pending_referral_rewards(self):
        """Получает список ожидающих наград за рефералов"""
        try:
            self.cursor.execute("""
                SELECT rr.id, rr.user_id, u.username, u.full_name, rr.reward_amount, rr.created_at
                FROM referral_rewards rr
                JOIN users u ON rr.user_id = u.user_id
                WHERE rr.status = 'pending'
                ORDER BY rr.created_at DESC
            """)
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения ожидающих наград: {e}")
            return []

    def update_referral_reward_status(self, reward_id, status):
        """Обновляет статус награды за рефералов"""
        try:
            self.cursor.execute(
                "UPDATE referral_rewards SET status = ? WHERE id = ?",
                (status, reward_id)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления статуса награды: {e}")
            return False

    def update_user_subscription(self, user_id, status: bool):
        try:
            self.cursor.execute(
                "UPDATE users SET has_subscribed = ? WHERE user_id = ?",
                (1 if status else 0, user_id)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка обновления подписки: {e}")

    def add_account_for_sale(self, server, description, price, contacts, photo_file_id=None):
        try:
            description_clean = description.replace("[", "").replace("]", "")
            self.cursor.execute("""
                INSERT INTO accounts_for_sale (server, description, price, contacts, photo_file_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (server, description_clean, price, contacts, photo_file_id, datetime.now()))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка добавления объявления: {e}")
            return None

    def delete_account(self, account_id):
        try:
            self.cursor.execute("DELETE FROM accounts_for_sale WHERE id = ?", (account_id,))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления аккаунта: {e}")
            return False

    def add_sell_request(self, user_id, username, full_name, server, description, price, contacts, photo_file_id=None):
        try:
            description_clean = description.replace("[", "").replace("]", "")
            self.cursor.execute("""
                INSERT INTO sell_requests (user_id, username, full_name, server, description, price, contacts, photo_file_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, username, full_name, server, description_clean, price, contacts, photo_file_id,
                  datetime.now()))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            logger.error(f"Ошибка добавления заявки: {e}")
            return None

    def update_sell_request_status(self, request_id, status):
        try:
            self.cursor.execute("UPDATE sell_requests SET status = ? WHERE id = ?", (status, request_id))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления статуса заявки: {e}")
            return False

    def get_sell_requests(self, status='pending'):
        try:
            self.cursor.execute(
                "SELECT * FROM sell_requests WHERE status = ? ORDER BY created_at DESC",
                (status,)
            )
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения заявок: {e}")
            return []

    def get_sell_request_by_id(self, request_id):
        try:
            self.cursor.execute("SELECT * FROM sell_requests WHERE id = ?", (request_id,))
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"Ошибка получения заявки: {e}")
            return None

    def add_order(self, user_id, username, full_name, order_type, **kwargs):
        try:
            self.cursor.execute("""
                INSERT INTO orders 
                (user_id, username, full_name, order_type, server, amount, price, description, contacts, payment_method, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id, username, full_name, order_type,
                kwargs.get('server'), kwargs.get('amount'),
                kwargs.get('price'), kwargs.get('description'),
                kwargs.get('contacts'), kwargs.get('payment_method'),
                datetime.now()
            ))
            self.conn.commit()

            order_id = self.cursor.lastrowid

            # Логируем создание заказа
            logger.info(f"✅ Создан заказ #{order_id} для пользователя {user_id} ({full_name})")

            return order_id
        except Exception as e:
            logger.error(f"Ошибка добавления заказа: {e}")
            import traceback
            logger.error(f"Трассировка: {traceback.format_exc()}")
            return None

    def get_active_accounts(self):
        try:
            self.cursor.execute(
                "SELECT id, server, description, price, contacts, photo_file_id FROM accounts_for_sale WHERE is_active = 1 ORDER BY created_at DESC"
            )
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения объявлений: {e}")
            return []

    def get_account_by_id(self, account_id):
        try:
            self.cursor.execute(
                "SELECT id, server, description, price, contacts, photo_file_id FROM accounts_for_sale WHERE id = ? AND is_active = 1",
                (account_id,)
            )
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"Ошибка получения объявления: {e}")
            return None

    def get_all_users(self):
        """Получает всех пользователей"""
        try:
            self.cursor.execute(
                "SELECT user_id, username, full_name, reg_date, referral_count FROM users ORDER BY reg_date DESC")
            users = self.cursor.fetchall()
            logger.info(f"✅ Получено {len(users)} пользователей из базы")
            return users
        except Exception as e:
            logger.error(f"Ошибка получения пользователей: {e}")
            return []

    def get_orders_by_status(self, status=None):
        try:
            if status:
                self.cursor.execute(
                    "SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC",
                    (status,)
                )
            else:
                self.cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения заказов: {e}")
            return []

    def get_all_orders(self):
        try:
            self.cursor.execute("SELECT * FROM orders ORDER BY created_at DESC")
            return self.cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка получения всех заказов: {e}")
            return []

    def update_order_status(self, order_id, status):
        try:
            self.cursor.execute(
                "UPDATE orders SET status = ? WHERE id = ?",
                (status, order_id)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка обновления статуса заказа: {e}")

    def update_order_receipt(self, order_id, receipt_file_id):
        try:
            self.cursor.execute(
                "UPDATE orders SET has_receipt = 1, receipt_file_id = ? WHERE id = ?",
                (receipt_file_id, order_id)
            )
            self.conn.commit()
        except Exception as e:
            logger.error(f"Ошибка обновления чека: {e}")

    def get_order_by_id(self, order_id):
        try:
            self.cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
            return self.cursor.fetchone()
        except Exception as e:
            logger.error(f"Ошибка получения заказа: {e}")
            return None

    def get_statistics(self):
        """Получает полную статистику бота"""
        try:
            # Инициализируем все значения по умолчанию
            stats = {
                'total_users': 0,
                'subscribed_users': 0,
                'users_with_referrals': 0,
                'total_referrals': 0,
                'total_orders': 0,
                'new_orders': 0,
                'completed_orders': 0,
                'rejected_orders': 0,
                'active_accounts': 0,
                'pending_requests': 0,
                'pending_rewards_count': 0,
                'pending_rewards_amount': 0,
                'total_revenue': 0
            }

            # 1. Получаем статистику пользователей
            try:
                self.cursor.execute("SELECT COUNT(*) FROM users")
                result = self.cursor.fetchone()
                stats['total_users'] = result[0] if result and result[0] else 0
            except:
                stats['total_users'] = 0

            try:
                self.cursor.execute("SELECT COUNT(*) FROM users WHERE has_subscribed = 1")
                result = self.cursor.fetchone()
                stats['subscribed_users'] = result[0] if result and result[0] else 0
            except:
                stats['subscribed_users'] = 0

            try:
                self.cursor.execute("SELECT COUNT(*) FROM users WHERE referral_count > 0")
                result = self.cursor.fetchone()
                stats['users_with_referrals'] = result[0] if result and result[0] else 0
            except:
                stats['users_with_referrals'] = 0

            try:
                self.cursor.execute("SELECT SUM(referral_count) FROM users")
                result = self.cursor.fetchone()
                stats['total_referrals'] = int(result[0]) if result and result[0] else 0
            except:
                stats['total_referrals'] = 0

            # 2. Получаем статистику заказов
            try:
                self.cursor.execute("SELECT COUNT(*) FROM orders")
                result = self.cursor.fetchone()
                stats['total_orders'] = result[0] if result and result[0] else 0
            except:
                stats['total_orders'] = 0

            try:
                self.cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'new'")
                result = self.cursor.fetchone()
                stats['new_orders'] = result[0] if result and result[0] else 0
            except:
                stats['new_orders'] = 0

            try:
                self.cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'")
                result = self.cursor.fetchone()
                stats['completed_orders'] = result[0] if result and result[0] else 0
            except:
                stats['completed_orders'] = 0

            try:
                self.cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'rejected'")
                result = self.cursor.fetchone()
                stats['rejected_orders'] = result[0] if result and result[0] else 0
            except:
                stats['rejected_orders'] = 0

            # 3. Выручка
            try:
                self.cursor.execute("SELECT price FROM orders WHERE status = 'completed'")
                completed_prices = self.cursor.fetchall()
                total_revenue = 0
                for price_tuple in completed_prices:
                    if price_tuple and price_tuple[0]:
                        price_str = str(price_tuple[0])
                        # Извлекаем только цифры
                        price_digits = ''.join(filter(str.isdigit, price_str))
                        if price_digits:
                            try:
                                total_revenue += int(price_digits)
                            except:
                                continue
                stats['total_revenue'] = total_revenue
            except:
                stats['total_revenue'] = 0

            # 4. Активные объявления
            try:
                self.cursor.execute("SELECT COUNT(*) FROM accounts_for_sale WHERE is_active = 1")
                result = self.cursor.fetchone()
                stats['active_accounts'] = result[0] if result and result[0] else 0
            except:
                stats['active_accounts'] = 0

            # 5. Заявки на продажу
            try:
                self.cursor.execute("SELECT COUNT(*) FROM sell_requests WHERE status = 'pending'")
                result = self.cursor.fetchone()
                stats['pending_requests'] = result[0] if result and result[0] else 0
            except:
                stats['pending_requests'] = 0

            # 6. Реферальные награды
            try:
                self.cursor.execute(
                    "SELECT COUNT(*), SUM(reward_amount) FROM referral_rewards WHERE status = 'pending'")
                result = self.cursor.fetchone()
                if result:
                    stats['pending_rewards_count'] = result[0] if result[0] else 0
                    stats['pending_rewards_amount'] = int(result[1]) if result[1] else 0
            except:
                stats['pending_rewards_count'] = 0
                stats['pending_rewards_amount'] = 0

            logger.info(f"Статистика получена: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Критическая ошибка получения статистики: {e}", exc_info=True)
            return None

db = Database()


class Form(StatesGroup):
    sell_currency_server = State()
    sell_currency_amount = State()
    sell_currency_contacts = State()

    buy_currency_amount = State()
    buy_currency_server = State()

    buy_software_confirm = State()

    admin_broadcast_message = State()
    admin_broadcast_confirm = State()

    # Состояния для редактирования аккаунта
    edit_account = State()
    edit_account_field = State()
    edit_account_value = State()

    # Состояния для удаления аккаунта
    delete_account_confirm = State()

    # Состояния для продажи аккаунта пользователем
    sell_account_server = State()        # Выбор сервера для продажи аккаунта
    sell_account_description = State()   # Описание аккаунта
    sell_account_photo = State()         # Фото аккаунта (добавьте это!)
    sell_account_price = State()         # Цена аккаунта
    sell_account_contacts = State()      # Контакты для связи


    # Состояния для добавления аккаунта администратором
    admin_add_account_server = State()
    admin_add_account_description = State()
    admin_add_account_photo = State()
    admin_add_account_price = State()
    admin_add_account_contacts = State()

    admin_broadcast = State()
    waiting_for_receipt = State()


def validate_virts_amount(amount: str) -> tuple[bool, int, str]:
    amount = amount.strip().lower()

    try:
        # Обрабатываем формат с "kk"
        if 'kk' in amount or 'кк' in amount:
            num_text = re.sub(r'[^\d\.]', '', amount)
            if not num_text:
                return False, 0, "❌ Неверный формат! Используйте: 1.000.000 или 1kk"
            kk_amount = float(num_text)
            num = int(kk_amount * 1000000)
        else:
            # Обрабатываем формат с точками
            amount_clean = amount.replace('.', '')
            if not re.match(r'^\d+$', amount_clean):
                return False, 0, "❌ Неверный формат! Используйте цифры: 1.000.000, 5.000.000"
            num = int(amount_clean)

        # Минимум 1.000.000 (1 миллион)
        if num < 1000000:
            return False, 0, "❌ Минимум: 1.000.000 (1 миллион виртов)"

        if num > MAX_VIRTS:
            return False, 0, f"❌ Максимум: {MAX_VIRTS:,} (800кк)".replace(',', '.')

        return True, num, ""
    except:
        return False, 0, "❌ Ошибка! Используйте формат: 1.000.000 или 1kk"


def validate_price(price: str) -> tuple[bool, int, str]:
    price = price.strip().replace(' ', '').replace('р', '').replace('руб', '').replace(',', '.')

    try:
        num = float(price)

        if num <= 0:
            return False, 0, "❌ Цена должна быть больше 0"

        if num > MAX_PRICE:
            return False, 0, f"❌ Максимальная сумма: {MAX_PRICE:,} ₽".replace(',', ' ')

        return True, int(num), ""
    except:
        return False, 0, "❌ Введите корректную сумму (только цифры)"


async def notify_admins(text: str, keyboard=None, photo_file_id=None):
    """Отправляет уведомление всем администраторам"""
    logger.info(f"Отправка уведомления администраторам: {len(ADMIN_IDS)} админов")

    sent_count = 0
    for admin_id in ADMIN_IDS:
        try:
            logger.info(f"Попытка отправки уведомления администратору {admin_id}")

            if photo_file_id:
                await bot.send_photo(
                    chat_id=admin_id,
                    photo=photo_file_id,
                    caption=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            else:
                await bot.send_message(
                    chat_id=admin_id,
                    text=text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
            sent_count += 1
            logger.info(f"✅ Уведомление отправлено администратору {admin_id}")

        except Exception as e:
            logger.error(f"❌ Ошибка отправки уведомления админу {admin_id}: {e}")
            import traceback
            logger.error(f"Трассировка: {traceback.format_exc()}")

    logger.info(f"✅ Уведомлений отправлено: {sent_count}/{len(ADMIN_IDS)}")
    return sent_count


def get_main_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text="💎 Продать вирты", callback_data="sell_currency"),
        InlineKeyboardButton(text="🛒 Купить вирты", callback_data="buy_currency")
    )
    keyboard.row(
        InlineKeyboardButton(text="🛍️ Магазин аккаунтов", callback_data="buy_account"),  # Изменено название
        InlineKeyboardButton(text="⚡ Купить софт", callback_data="buy_software")
    )
    keyboard.row(
        InlineKeyboardButton(text="👥 Реферальная система", callback_data="referral_system")
    )
    return keyboard.as_markup()


def get_cancel_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="🚫 Отмена", callback_data="cancel")
    return keyboard.as_markup()


def get_payment_keyboard(order_type, order_id=None):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="💸 Купить", callback_data=f"confirm_payment_{order_type}"))
    if order_id:
        keyboard.row(InlineKeyboardButton(text="📄 Отправить чек", callback_data=f"send_receipt_{order_id}"))
    keyboard.row(InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu"))
    return keyboard.as_markup()


def get_receipt_keyboard(order_id):
    """Клавиатура для отправки чека - С ПРОВЕРКОЙ"""
    try:
        logger.info(f"Создание клавиатуры для чека заказа #{order_id}")

        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text="📄 Отправить чек", callback_data=f"send_receipt_{order_id}"))
        keyboard.row(InlineKeyboardButton(text="🔙 Назад", callback_data=f"back_to_order_{order_id}"))
        keyboard.row(InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu"))

        return keyboard.as_markup()
    except Exception as e:
        logger.error(f"Ошибка создания клавиатуры для чека: {e}")
        # Возвращаем простую клавиатуру в случае ошибки
        keyboard = InlineKeyboardBuilder()
        keyboard.row(InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu"))
        return keyboard.as_markup()


def get_servers_keyboard(page=0, servers_per_page=27, admin_mode=False, for_edit=False, account_id=None):
    keyboard = InlineKeyboardBuilder()
    start = page * servers_per_page
    end = start + servers_per_page
    current_servers = BR_SERVERS[start:end]

    for i in range(0, len(current_servers), 3):
        row_servers = current_servers[i:i + 3]
        row_buttons = []
        for server in row_servers:
            if for_edit and account_id:
                # Для редактирования
                row_buttons.append(InlineKeyboardButton(
                    text=server,
                    callback_data=f"edit_server_{server}_{account_id}"
                ))
            elif admin_mode:
                row_buttons.append(InlineKeyboardButton(
                    text=server,
                    callback_data=f"admin_server_{server}"
                ))
            else:
                row_buttons.append(InlineKeyboardButton(
                    text=server,
                    callback_data=f"server_{server}"
                ))
        keyboard.row(*row_buttons)

    nav_buttons = []
    if page > 0:
        if for_edit and account_id:
            nav_buttons.append(InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"edit_servers_{page - 1}_{account_id}"
            ))
        elif admin_mode:
            nav_buttons.append(InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"admin_servers_{page - 1}"  # Исправлено: должно быть page - 1, не page + 1
            ))
        else:
            nav_buttons.append(InlineKeyboardButton(
                text="◀️ Назад",
                callback_data=f"servers_{page - 1}"
            ))

    if end < len(BR_SERVERS):
        if for_edit and account_id:
            nav_buttons.append(InlineKeyboardButton(
                text="▶️ Вперед",
                callback_data=f"edit_servers_{page + 1}_{account_id}"
            ))
        elif admin_mode:
            nav_buttons.append(InlineKeyboardButton(
                text="▶️ Вперед",
                callback_data=f"admin_servers_{page + 1}"
            ))
        else:
            nav_buttons.append(InlineKeyboardButton(
                text="▶️ Вперед",
                callback_data=f"servers_{page + 1}"
            ))

    if nav_buttons:
        keyboard.row(*nav_buttons)

    # Корректная кнопка отмены
    if account_id:
        if for_edit:
            cancel_callback = f"admin_shop_edit_{account_id}"
        else:
            cancel_callback = f"admin_shop_view_{account_id}"
    else:
        cancel_callback = "cancel"

    keyboard.row(InlineKeyboardButton(text="🚫 Отмена", callback_data=cancel_callback))
    return keyboard.as_markup()

def get_accounts_keyboard(accounts, page=0, accounts_per_page=5):
    keyboard = InlineKeyboardBuilder()
    start = page * accounts_per_page
    end = start + accounts_per_page
    current_accounts = accounts[start:end]

    logger.info(f"Создание клавиатуры для {len(current_accounts)} объявлений")

    for acc in current_accounts:
        # Проверяем, что данные есть и их достаточно
        if acc and len(acc) >= 6:
            acc_id = acc[0]
            server = acc[1] if acc[1] else "Без сервера"
            price = acc[3] if acc[3] else "0 ₽"

            button_text = f"👤 {server} - {price}"
            if len(button_text) > 50:
                button_text = button_text[:47] + "..."

            logger.info(f"Добавляем кнопку для аккаунта #{acc_id}: {server} - {price}")

            keyboard.row(
                InlineKeyboardButton(
                    text=button_text,
                    callback_data=f"view_account_{acc_id}"
                )
            )
        else:
            logger.error(f"Некорректные данные объявления: {acc}")

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️ Назад", callback_data=f"accounts_{page - 1}"))
    if end < len(accounts):
        nav_buttons.append(InlineKeyboardButton(text="▶️ Вперед", callback_data=f"accounts_{page + 1}"))

    if nav_buttons:
        keyboard.row(*nav_buttons)

    keyboard.row(InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu"))
    return keyboard.as_markup()


def get_referral_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="📊 Моя статистика", callback_data="referral_stats"))
    keyboard.row(InlineKeyboardButton(text="📢 Пригласить друга", callback_data="referral_invite"))
    keyboard.row(InlineKeyboardButton(text="📝 Правила", callback_data="referral_rules"))
    keyboard.row(InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu"))
    return keyboard.as_markup()


def get_admin_menu():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="🛍️ Магазин аккаунтов", callback_data="admin_shop_main"))
    keyboard.row(InlineKeyboardButton(text="➕ Добавить объявление", callback_data="admin_add_account"))
    keyboard.row(InlineKeyboardButton(text="🗑️ Управление объявлениями", callback_data="admin_manage_accounts"))
    keyboard.row(InlineKeyboardButton(text="📋 Заявки на продажу", callback_data="admin_manage_requests"))
    keyboard.row(InlineKeyboardButton(text="📦 Заказы", callback_data="admin_manage_orders"))
    keyboard.row(InlineKeyboardButton(text="💰 Награды за рефералов", callback_data="admin_referral_rewards"))
    keyboard.row(InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"))
    keyboard.row(InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin_all_users"))
    keyboard.row(InlineKeyboardButton(text="📢 Рассылка всем пользователям", callback_data="admin_broadcast"))
    keyboard.row(InlineKeyboardButton(text="🛒 Перейти в магазин", callback_data="to_shop_menu"))
    return keyboard.as_markup()


def get_photo_keyboard():
    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="📷 Отправить фото", callback_data="send_photo"))
    keyboard.row(InlineKeyboardButton(text="⏭️ Пропустить фото", callback_data="skip_photo"))
    keyboard.row(InlineKeyboardButton(text="🚫 Отмена", callback_data="cancel"))
    return keyboard.as_markup()


def get_payment_details():
    return f"""
💳 *РЕКВИЗИТЫ ДЛЯ ОПЛАТЫ:*
📱 Номер: `{PAYMENT_DETAILS['phone']}`
👤 Имя: {PAYMENT_DETAILS['name']}
🏦 Банк: {PAYMENT_DETAILS['bank']}
📞 Контакт: @Kornycod

⚠️ {PAYMENT_DETAILS['note']}
"""


def get_referral_link(user_id: int) -> str:
    """Генерирует реферальную ссылку"""
    return f"https://t.me/NovKornycod_bot?start=ref{user_id}"


async def check_access(message_or_callback):
    if hasattr(message_or_callback, 'from_user'):
        user_id = message_or_callback.from_user.id
    else:
        user_id = message_or_callback

    # Админы всегда имеют доступ
    if user_id in ADMIN_IDS:
        return True

    # Проверяем подписку
    is_subscribed = await check_subscription(user_id)
    if is_subscribed:
        db.update_user_subscription(user_id, True)
        return True

    db.update_user_subscription(user_id, False)
    return False


def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором"""
    return user_id in ADMIN_IDS


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    try:
        user = message.from_user

        # Проверяем реферальную ссылку
        referrer_id = 0
        if len(message.text.split()) > 1:
            ref_code = message.text.split()[1]
            if ref_code.startswith('ref'):
                try:
                    referrer_id = int(ref_code[3:])  # Извлекаем ID из ref123456
                    # Проверяем, существует ли реферер
                    if referrer_id == user.id:
                        referrer_id = 0  # Нельзя быть реферером самому себе
                except:
                    referrer_id = 0

        db.add_user(user.id, user.username, user.full_name, referrer_id)

        if not await check_access(message):
            await message.answer(
                f"⚠️ *Доступ ограничен!*\n\n"
                f"Для использования бота необходимо подписаться на наш канал:\n"
                f"{CHANNEL_LINK}\n\n"
                f"После подписки нажмите '✅ Проверить подписку'",
                parse_mode="Markdown",
                reply_markup=get_subscription_keyboard()
            )
            return

        # Админы могут выбирать между админкой и главным меню
        if is_admin(user.id):
            keyboard = InlineKeyboardBuilder()
            keyboard.row(
                InlineKeyboardButton(text="👑 Админ панель", callback_data="to_admin_menu"),
                InlineKeyboardButton(text="🛒 Магазин", callback_data="to_shop_menu")
            )
            await message.answer(
                "👑 *АДМИН ДОСТУП*\n\n"
                "Выберите режим работы:",
                parse_mode="Markdown",
                reply_markup=keyboard.as_markup()
            )
        else:
            await message.answer(
                "🛒 *Shop Kornycod*\n\n"
                "Добро пожаловать в магазин!\n"
                "Выберите раздел:",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )

    except Exception as e:
        logger.error(f"Ошибка в cmd_start: {e}")
        try:
            await message.answer(
                "🛒 *Shop Kornycod*\n\n"
                "Добро пожаловать! Что вас интересует?",
                reply_markup=get_main_menu()
            )
        except:
            pass


@dp.callback_query(F.data == "referral_system")
async def referral_system(callback: types.CallbackQuery):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    await callback.message.edit_text(
        "👥 *РЕФЕРАЛЬНАЯ СИСТЕМА*\n\n"
        f"🎁 *Награда: {REFERRAL_REWARD:,} ₽ за {REFERRAL_THRESHOLD} приглашенных!*\n\n"
        f"Приглашайте друзей и получайте награду!\n"
        f"Как только {REFERRAL_THRESHOLD} человек зарегистрируются по вашей ссылке, вы получите {REFERRAL_REWARD:,} ₽!",
        parse_mode="Markdown",
        reply_markup=get_referral_menu()
    )
    await callback.answer()


@dp.callback_query(F.data == "no_action")
async def no_action_handler(callback: types.CallbackQuery):
    """Обработка пустого действия (кнопка-заглушка)"""
    await callback.answer()


@dp.callback_query(F.data == "referral_stats")
async def referral_stats(callback: types.CallbackQuery):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    try:
        stats = db.get_user_referral_stats(callback.from_user.id)

        if not stats:
            # Если статистика не найдена, возможно пользователя нет в базе
            # Добавим его
            user = callback.from_user
            db.add_user(user.id, user.username, user.full_name, 0)
            stats = db.get_user_referral_stats(callback.from_user.id)

            if not stats:
                # Если все еще нет статистики
                stats = {
                    'referral_count': 0,
                    'got_reward': False,
                    'referrals': [],
                    'needed': REFERRAL_THRESHOLD
                }
    except Exception as e:
        logger.error(f"Ошибка получения реферальной статистики для пользователя {callback.from_user.id}: {e}")
        stats = {
            'referral_count': 0,
            'got_reward': False,
            'referrals': [],
            'needed': REFERRAL_THRESHOLD
        }

    referral_link = get_referral_link(callback.from_user.id)

    stats_text = f"""📊 *ВАША РЕФЕРАЛЬНАЯ СТАТИСТИКА*

👥 Приглашено друзей: {stats.get('referral_count', 0)}/{REFERRAL_THRESHOLD}
🎯 Осталось пригласить: {stats.get('needed', REFERRAL_THRESHOLD)}
🎁 Статус награды: {'✅ Получена' if stats.get('got_reward', False) else '❌ Еще не получена'}

🔗 *Ваша реферальная ссылка:*
`{referral_link}`

📝 *Как использовать:*
1. Поделитесь этой ссылкой с друзьями
2. Каждый друг, который зарегистрируется по вашей ссылке, будет засчитан
3. Когда наберется {REFERRAL_THRESHOLD} человек - вы получите {REFERRAL_REWARD:,} ₽!"""

    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(
        text="📢 Поделиться ссылкой",
        url=f"https://t.me/share/url?url={referral_link}&text=Привет! Заходи в лучший магазин для игроков!"
    ))
    keyboard.row(InlineKeyboardButton(text="🔄 Обновить", callback_data="referral_stats"))
    keyboard.row(InlineKeyboardButton(text="◀️ Назад", callback_data="referral_system"))

    try:
        await callback.message.edit_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=keyboard.as_markup()
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения: {e}")
        # Если не удалось отредактировать, отправляем новое
        await callback.message.answer(
            stats_text,
            parse_mode="Markdown",
            reply_markup=keyboard.as_markup()
        )

    await callback.answer()


@dp.callback_query(F.data == "referral_invite")
async def referral_invite(callback: types.CallbackQuery):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    referral_link = get_referral_link(callback.from_user.id)

    invite_text = f"""📢 *ПРИГЛАСИТЕ ДРУЗЕЙ И ПОЛУЧИТЕ {REFERRAL_REWARD:,} ₽!*

🎁 *Условия:*
• Пригласите {REFERRAL_THRESHOLD} друзей
• Каждый друг должен зарегистрироваться по вашей ссылке
• Как только наберется {REFERRAL_THRESHOLD} человек - вы получаете {REFERRAL_REWARD:,} ₽!

🔗 *Ваша реферальная ссылка:*
`{referral_link}`

📝 *Текст для приглашения:*
Привет! Заходи в лучший магазин для игроков Kornycod Shop! Здесь можно купить/продать вирты, аккаунты и софт для игры!"""

    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="📢 Поделиться ссылкой",
                                      url=f"https://t.me/share/url?url={referral_link}&text=Привет! Заходи в лучший магазин для игроков Kornycod Shop! Здесь можно купить/продать вирты, аккаунты и софт для игры!"))
    keyboard.row(InlineKeyboardButton(text="◀️ Назад", callback_data="referral_system"))

    await callback.message.edit_text(
        invite_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "referral_rules")
async def referral_rules(callback: types.CallbackQuery):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    rules_text = f"""📝 *ПРАВИЛА РЕФЕРАЛЬНОЙ СИСТЕМЫ*

🎯 *Условия получения награды:*
1. Пригласите {REFERRAL_THRESHOLD} уникальных пользователей
2. Каждый приглашенный должен зарегистрироваться по вашей ссылке
3. Приглашенные должны подписаться на канал {CHANNEL_LINK}
4. Награда выплачивается один раз за достижение порога

⚠️ *Важные моменты:*
• Нельзя приглашать самого себя
• Награда выплачивается после проверки администратором
• Система отслеживает только уникальных пользователей
• Мошенничество (накрутка) приведет к блокировке

💰 *Размер награды:* {REFERRAL_REWARD:,} ₽

🔄 *Как проверить прогресс:*
Используйте кнопку "📊 Моя статистика" для отслеживания количества приглашенных"""

    keyboard = InlineKeyboardBuilder()
    keyboard.row(InlineKeyboardButton(text="📊 Моя статистика", callback_data="referral_stats"))
    keyboard.row(InlineKeyboardButton(text="📢 Пригласить друга", callback_data="referral_invite"))
    keyboard.row(InlineKeyboardButton(text="◀️ Назад", callback_data="referral_system"))

    await callback.message.edit_text(
        rules_text,
        parse_mode="Markdown",
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()


@dp.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: types.CallbackQuery):
    if await check_access(callback):
        if is_admin(callback.from_user.id):
            await callback.message.edit_text(
                "👑 *АДМИН ПАНЕЛЬ*\n\n"
                "✅ Вы подписаны на канал!\n"
                "Выберите действие:",
                parse_mode="Markdown",
                reply_markup=get_admin_menu()
            )
        else:
            await callback.message.edit_text(
                "✅ *Отлично! Вы подписаны на канал!*\n\n"
                "Теперь вы можете пользоваться всеми функциями бота.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
    else:
        await callback.answer(
            "❌ Вы не подписаны на канал! Подпишитесь и попробуйте снова.",
            show_alert=True
        )
    await callback.answer()


@dp.callback_query(F.data == "sell_currency")
async def sell_currency_start(callback: types.CallbackQuery, state: FSMContext):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    await state.set_state(Form.sell_currency_server)
    await callback.message.edit_text(
        "💎 *ПРОДАЖА ВИРТОВ*\n\n"
        "Выберите сервер:",
        parse_mode="Markdown",
        reply_markup=get_servers_keyboard()
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("server_"))
async def server_selected(callback: types.CallbackQuery, state: FSMContext):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    server = callback.data.replace("server_", "")
    current_state = await state.get_state()

    # Обработка для продажи виртов
    if current_state == Form.sell_currency_server.state:
        await state.update_data(server=server)
        await state.set_state(Form.sell_currency_amount)

        await callback.message.edit_text(
            f"💎 *ПРОДАЖА ВИРТОВ*\n\n"
            f"✅ Сервер: *{server}*\n\n"
            f"💰 *Введите количество виртов:*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 *Доступный диапазон:*\n"
            f"• От **1.000.000** (1 миллион) до **800.000.000** (800 миллионов)\n\n"
            f"✨ *Поддерживаемые форматы:*\n"
            f"• **1.000.000** (1 миллион)\n"
            f"• **1kk** или **1кк** (1 миллион)\n"
            f"• **2.5kk** или **2.5кк** (2.5 миллиона)\n"
            f"• **100kk** или **100кк** (100 миллионов)\n\n"
            f"📝 *Примеры ввода:*\n"
            f"▫️ 1.000.000\n"
            f"▫️ 5.000.000\n"
            f"▫️ 1kk\n"
            f"▫️ 2.5kk\n"
            f"▫️ 100kk",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )

    # В функции server_selected, в части для buy_currency_server.state:
    elif current_state == Form.buy_currency_server.state:
        await state.update_data(server=server)
        data = await state.get_data()

        try:
            amount_num = data.get('amount_num')
            kk_value = data.get('kk_value')

            if not amount_num or not kk_value:
                await callback.answer("❌ Ошибка данных!", show_alert=True)
                return

            # Цена: 1кк = 80 ₽
            price = int(kk_value * 80)

            # Форматируем для отображения
            if kk_value.is_integer():
                display_amount = f"{int(kk_value)}кк"
            else:
                display_amount = f"{kk_value:.1f}кк"

            await state.update_data(
                price=f"{price:,} ₽".replace(',', ' '),
                order_type="buy_currency",
                display_amount=display_amount
            )

            await callback.message.edit_text(
                f"🛒 *ПОКУПКА ВИРТОВ*\n\n"
                f"📋 *Детали заказа:*\n"
                f"• Сервер: *{server}*\n"
                f"• Количество: *{display_amount}*\n"
                f"• Стоимость: *{price:,} ₽*\n\n"
                f"{get_payment_details()}\n"
                f"Нажмите кнопку 'Купить' для оформления заказа:",
                parse_mode="Markdown",
                reply_markup=get_payment_keyboard("buy_currency")
            )
        except Exception as e:
            await callback.answer(f"❌ Ошибка: {str(e)}", show_alert=True)
            return

    # Обработка для продажи аккаунта
    elif current_state == Form.sell_account_server.state:  # <-- Это состояние существует
        await state.update_data(server=server)
        await state.set_state(Form.sell_account_description)  # <-- Переходим к описанию
        await callback.message.edit_text(
            f"👤 *ПРОДАЖА АККАУНТА*\n\n"
            f"Сервер: *{server}*\n\n"
            f"Опишите аккаунт:\n"
            f"• Уровень \n• Привязки\n• Имущество\n• Сервер\n• Цена",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )

    await callback.answer()


@dp.callback_query(F.data.startswith("servers_"))
async def servers_pagination(callback: types.CallbackQuery):
    try:
        page = int(callback.data.replace("servers_", ""))
        await callback.message.edit_reply_markup(
            reply_markup=get_servers_keyboard(page=page)
        )
    except:
        pass
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_servers_"))
async def admin_servers_pagination(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    try:
        page = int(callback.data.replace("admin_servers_", ""))
        await callback.message.edit_reply_markup(
            reply_markup=get_servers_keyboard(page=page, admin_mode=True)
        )
    except:
        pass
    await callback.answer()


@dp.message(Form.sell_currency_amount)
async def process_sell_amount(message: types.Message, state: FSMContext):
    if not await check_access(message):
        return

    amount_text = message.text.strip().lower()

    try:
        # Обрабатываем формат с "kk" (например: "1kk", "2.5kk", "100kk")
        if 'kk' in amount_text or 'кк' in amount_text:
            # Убираем все нецифровые символы кроме точки
            num_text = re.sub(r'[^\d\.]', '', amount_text)

            if not num_text:
                await message.answer("❌ Неверный формат! Пример: 1kk, 2.5kk, 100кк",
                                     reply_markup=get_cancel_keyboard())
                return

            kk_amount = float(num_text)
            amount_num = int(kk_amount * 1000000)  # конвертируем кк в вирты
            display_text = f"{kk_amount}кк" if kk_amount.is_integer() else f"{kk_amount}кк"

        else:
            # Обрабатываем формат с точками: "1.000.000", "500.000", "1000"
            # Убираем все точки для проверки
            amount_clean = amount_text.replace('.', '')

            if not re.match(r'^\d+$', amount_clean):
                await message.answer("❌ Неверный формат! Используйте цифры: 1.000.000, 500.000, 1000",
                                     reply_markup=get_cancel_keyboard())
                return

            amount_num = int(amount_clean)

            # Форматируем для отображения
            if amount_num >= 1000000:
                kk_amount = amount_num / 1000000
                if kk_amount.is_integer():
                    display_text = f"{int(kk_amount)}кк"
                else:
                    display_text = f"{kk_amount:.1f}кк"
            else:
                display_text = f"{amount_num:,}".replace(',', '.')

        # Валидация
        if amount_num < 1:
            await message.answer("❌ Минимум: 1", reply_markup=get_cancel_keyboard())
            return
        if amount_num > MAX_VIRTS:
            await message.answer(f"❌ Максимум: {MAX_VIRTS:,} (800кк)".replace(',', '.'),
                                 reply_markup=get_cancel_keyboard())
            return

        # Автоматический расчет цены (1кк = 30 руб)
        price_per_kk = 30
        kk = amount_num / 1000000
        price_num = int(kk * price_per_kk)

        if price_num < 1:
            price_num = 1

        # Форматируем для сохранения
        formatted_amount = f"{amount_num:,}".replace(",", ".")

        await state.update_data(
            amount=formatted_amount,
            amount_num=amount_num,
            price=f"{price_num:,} ₽".replace(',', '.'),
            display_amount=display_text
        )

        await state.set_state(Form.sell_currency_contacts)

        await message.answer(
            f"💎 *ПРОДАЖА ВИРТОВ*\n\n"
            f"✅ Количество: *{display_text}*\n"
            f"💰 Автоматическая цена: *{price_num:,} ₽*\n"
            f"📊 *1кк (1.000.000) = 30 руб*\n\n"
            f"Введите ваши контакты для связи:\n"
            f"• Telegram (@ник)\n"
            f"• Номер телефона",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка обработки количества виртов: {e}")
        # В process_sell_amount и process_buy_amount в блоке except:
        await message.answer(
            "❌ Ошибка! Введите количество в формате:\n"
            "• 1.000.000\n"
            "• 500.000\n"
            "• 1кк\n"
            "• 2.5кк",
            reply_markup=get_cancel_keyboard()
        )


@dp.message(Form.sell_currency_contacts)
async def process_sell_contacts(message: types.Message, state: FSMContext):
    if not await check_access(message):
        return

    contacts = message.text.strip()
    user_data = await state.get_data()

    order_id = db.add_order(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        order_type="sell_currency",
        server=user_data.get('server'),
        amount=user_data.get('amount'),
        price=user_data.get('price'),
        description="Продажа виртов",
        contacts=contacts,
        payment_method="Не требуется"
    )

    if order_id:
        await message.answer(
            f"✅ *Заявка создана!*\n\n"
            f"📋 *Детали:*\n"
            f"• Сервер: {user_data.get('server')}\n"
            f"• Количество: {user_data.get('amount')}\n"
            f"• Цена: {user_data.get('price')}\n"
            f"• Контакты: {contacts}\n\n"
            f"Владелец свяжется с вами в ближайшее время!",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

        # Уведомление всем администраторам
        try:
            display_amount = user_data.get('display_amount', user_data.get('amount'))
            order_text = f"""
            🆕 *НОВАЯ ЗАЯВКА НА ПРОДАЖУ ВИРТОВ #{order_id}*

            👤 Пользователь: {message.from_user.full_name}
            📱 Юзернейм: @{message.from_user.username or 'нет'}
            🆔 ID: {message.from_user.id}

            🖥️ Сервер: {user_data.get('server')}
            💎 Количество: {display_amount} ({user_data.get('amount')})
            💰 Цена: {user_data.get('price')}
            📞 Контакты: {contacts}

            📝 Тип: Продажа виртов
            """

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 Связаться", url=f"tg://user?id={message.from_user.id}")],
                [InlineKeyboardButton(text="📋 К заказам", callback_data="admin_manage_orders")]
            ])

            await notify_admins(order_text, keyboard)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления админам: {e}")

    await state.clear()


@dp.callback_query(F.data == "buy_currency")
async def buy_currency_start(callback: types.CallbackQuery, state: FSMContext):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    await state.set_state(Form.buy_currency_amount)
    await callback.message.edit_text(
        "🛒 *ПОКУПКА ВИРТОВ*\n\n"
        "💰 *Введите количество виртов:*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📊 *Доступный диапазон:*\n"
        "• От **1.000.000** (1 миллион) до **800.000.000** (800 миллионов)\n\n"
        "✨ *Поддерживаемые форматы:*\n"
        "• **1.000.000** (1 миллион)\n"
        "• **1kk** или **1кк** (1 миллион)\n"
        "• **2.5kk** или **2.5кк** (2.5 миллиона)\n"
        "• **100kk** или **100кк** (100 миллионов)\n\n"
        "📝 *Примеры ввода:*\n"
        "▫️ 1.000.000\n"
        "▫️ 5.000.000\n"
        "▫️ 1kk\n"
        "▫️ 2.5kk\n"
        "▫️ 100kk",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@dp.message(Form.buy_currency_amount)
async def process_buy_amount(message: types.Message, state: FSMContext):
    if not await check_access(message):
        return

    amount_text = message.text.strip().lower()

    try:
        # Обрабатываем формат с "kk" (например: "1kk", "2.5kk", "100kk")
        if 'kk' in amount_text or 'кк' in amount_text:
            # Убираем все нецифровые символы кроме точки
            num_text = re.sub(r'[^\d\.]', '', amount_text)

            if not num_text:
                await message.answer("❌ Неверный формат! Пример: 1kk, 2.5kk, 100кк",
                                     reply_markup=get_cancel_keyboard())
                return

            kk_amount = float(num_text)
            amount_num = int(kk_amount * 1000000)  # конвертируем кк в вирты
            kk_value = kk_amount  # количество в кк

        else:
            # Обрабатываем формат с точками: "1.000.000", "5.000.000"
            # Убираем все точки для проверки
            amount_clean = amount_text.replace('.', '')

            if not re.match(r'^\d+$', amount_clean):
                await message.answer("❌ Неверный формат! Используйте цифры: 1.000.000, 5.000.000",
                                     reply_markup=get_cancel_keyboard())
                return

            amount_num = int(amount_clean)
            kk_value = amount_num / 1000000  # конвертируем в кк

        # Валидация - минимум 1 миллион
        if amount_num < 1000000:
            await message.answer("❌ Минимум: 1.000.000 (1 миллион виртов)",
                                 reply_markup=get_cancel_keyboard())
            return

        if amount_num > MAX_VIRTS:
            await message.answer(f"❌ Максимум: {MAX_VIRTS:,} (800кк)".replace(',', '.'),
                                 reply_markup=get_cancel_keyboard())
            return

        # ПРАВИЛЬНЫЙ РАСЧЕТ ЦЕНЫ: 1кк = 80 ₽
        price = int(kk_value * 80)  # kk_value - количество в кк

        await state.update_data(
            amount=str(amount_num),
            amount_num=amount_num,
            kk_value=kk_value,
            price=str(price)
        )
        await state.set_state(Form.buy_currency_server)

        # Форматируем для отображения
        if amount_num >= 1000000:
            if kk_value.is_integer():
                display_text = f"{int(kk_value)}кк"
            else:
                display_text = f"{kk_value:.1f}кк"
        else:
            display_text = f"{amount_num:,}".replace(',', '.')

        await message.answer(
            f"🛒 *ПОКУПКА ВИРТОВ*\n\n"
            f"✅ Количество: *{display_text}*\n"
            f"💰 Стоимость: *{price:,} ₽*\n\n"
            f"Выберите сервер:",
            parse_mode="Markdown",
            reply_markup=get_servers_keyboard()
        )

    except Exception as e:
        logger.error(f"Ошибка обработки количества виртов: {e}")
        await message.answer(
            "❌ Ошибка! Введите количество в формате:\n"
            "• 1.000.000\n"
            "• 5.000.000\n"
            "• 1kk\n"
            "• 2.5kk\n"
            "• 100kk",
            reply_markup=get_cancel_keyboard()
        )

@dp.callback_query(F.data.startswith("confirm_payment_"))
async def confirm_payment(callback: types.CallbackQuery, state: FSMContext):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    order_type = callback.data.replace("confirm_payment_", "")
    user_data = await state.get_data()

    if not user_data:
        await callback.answer("❌ Данные не найдены!", show_alert=True)
        return

    if order_type == "buy_currency":
        order_id = db.add_order(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            full_name=callback.from_user.full_name,
            order_type="buy_currency",
            server=user_data.get('server'),
            amount=user_data.get('amount'),
            price=user_data.get('price'),
            description="Покупка виртов",
            contacts=f"@{callback.from_user.username or 'нет юзернейма'}",
            payment_method="Онлайн оплата"
        )
        order_details = f"Сервер: {user_data.get('server')}\nКоличество: {user_data.get('amount')}\nСумма: {user_data.get('price')}"
    elif order_type == "buy_software":
        order_id = db.add_order(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            full_name=callback.from_user.full_name,
            order_type="buy_software",
            server="Не требуется",
            amount="1 шт.",
            price=SOFTWARE_PRICE,
            description="Покупка софта для ловли",
            contacts=f"@{callback.from_user.username or 'нет юзернейма'}",
            payment_method="Онлайн оплата"
        )
        order_details = f"Товар: Софт для ловли\nСумма: {SOFTWARE_PRICE}"
    elif order_type == "buy_account":
        account_id = user_data.get('account_id', 0)
        order_id = db.add_order(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            full_name=callback.from_user.full_name,
            order_type="buy_account",
            server=user_data.get('server'),
            amount="1 аккаунт",
            price=user_data.get('price'),
            description=user_data.get('description'),
            contacts=f"@{callback.from_user.username or 'нет юзернейма'}",
            payment_method="Онлайн оплата"
        )
        order_details = f"Товар: Аккаунт #{account_id}\nСервер: {user_data.get('server')}\nСумма: {user_data.get('price')}"

    if order_id:
        await callback.message.edit_text(
            f"✅ *Заказ оформлен!*\n\n"
            f"🆔 Номер заказа: #{order_id}\n"
            f"{order_details}\n\n"
            f"{get_payment_details()}\n"
            f"После оплаты отправьте чек:",
            parse_mode="Markdown",
            reply_markup=get_receipt_keyboard(order_id)
        )

        try:
            order_text = f"🆕 *НОВЫЙ ЗАКАЗ #{order_id}*\n\n"
            order_text += f"Пользователь: {callback.from_user.full_name}\n"
            order_text += f"Юзернейм: @{callback.from_user.username or 'нет'}\n"
            order_text += f"ID: {callback.from_user.id}\n"
            order_text += f"Тип: {order_type}\n"
            order_text += f"{order_details}\n\n"
            order_text += f"Ожидайте чек об оплате"

            await notify_admins(order_text)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления админам: {e}")

    await state.clear()
    await callback.answer()


@dp.callback_query(F.data.startswith("send_receipt_"))
async def send_receipt_prompt(callback: types.CallbackQuery, state: FSMContext):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    order_id = int(callback.data.replace("send_receipt_", ""))

    await state.set_state(Form.waiting_for_receipt)
    await state.update_data(receipt_order_id=order_id)

    await callback.message.edit_text(
        f"📄 *Отправка чека*\n\n"
        f"Заказ: #{order_id}\n\n"
        f"Отправьте фото или документ с чеком об оплате:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚫 Отмена", callback_data=f"back_to_order_{order_id}")]
        ])
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("back_to_order_"))
async def back_to_order(callback: types.CallbackQuery, state: FSMContext):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    order_id = int(callback.data.replace("back_to_order_", ""))

    await callback.message.edit_text(
        f"📋 *Ваш заказ*\n\n"
        f"🆔 Номер заказа: #{order_id}\n\n"
        f"{get_payment_details()}\n"
        f"После оплаты нажмите '📄 Отправить чек'",
        parse_mode="Markdown",
        reply_markup=get_receipt_keyboard(order_id)
    )
    await callback.answer()


@dp.message(Form.waiting_for_receipt, F.photo | F.document)
async def handle_receipt_photo(message: types.Message, state: FSMContext):
    """Обработка отправки чека по заказу"""
    if not await check_access(message):
        return

    user_data = await state.get_data()
    order_id = user_data.get('receipt_order_id')

    if not order_id:
        await message.answer("❌ Ошибка: не найден номер заказа", reply_markup=get_main_menu())
        await state.clear()
        return

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
    else:
        await message.answer("❌ Пожалуйста, отправьте фото или документ")
        return

    # Получаем информацию о заказе
    order = db.get_order_by_id(order_id)
    if not order:
        await message.answer("❌ Заказ не найден!", reply_markup=get_main_menu())
        await state.clear()
        return

    # Сохраняем чек в базу
    db.update_order_receipt(order_id, file_id)

    # Определяем тип заказа
    try:
        order_type = order[4] if len(order) > 4 else ""  # order_type
        order_user_id = order[1]  # user_id
        order_username = order[2] or "нет"  # username
        order_full_name = order[3] or "Неизвестно"  # full_name
        order_server = order[5] or ""  # server
        order_price = order[7] or "0"  # price
        order_description = order[8] or ""  # description

        logger.info(f"📄 Чек для заказа #{order_id}, тип: {order_type}")

        # Извлекаем ID аккаунта из описания (для заказов из магазина)
        account_id = None
        if order_type == "buy_account_shop" and order_description:
            import re
            match = re.search(r'Аккаунт #(\d+)', order_description)
            if match:
                account_id = int(match.group(1))
                logger.info(f"📦 Найден ID аккаунта в описании: #{account_id}")

        # Формируем текст уведомления для администраторов
        admin_notification = f"""📄 *НОВЫЙ ЧЕК ПО ЗАКАЗУ #{order_id}*

👤 *Покупатель:*
• Имя: {order_full_name}
• Юзернейм: @{order_username}
• ID: {order_user_id}

💰 *Детали заказа:*
• Тип: {order_type}
• Сервер: {order_server}
• Сумма: {order_price}"""

        # Добавляем информацию об аккаунте если это заказ из магазина
        if account_id:
            # Получаем информацию об аккаунте
            account = db.get_shop_account_by_id(account_id)
            if account:
                account_title = account[2] if len(account) > 2 else "Без названия"
                admin_notification += f"""
📦 *Аккаунт:*
• ID: #{account_id}
• Название: {account_title[:50]}
• Сервер: {account[1] if len(account) > 1 else 'Не указан'}"""

        admin_notification += f"\n\n📅 *Время:* {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}"
        admin_notification += f"\n⚠️ *Статус:* Ожидает проверки"

        # Создаем клавиатуру для администраторов
        keyboard_buttons = [
            [InlineKeyboardButton(text="💬 Связаться с покупателем", url=f"tg://user?id={order_user_id}")],
            [InlineKeyboardButton(text="📋 К заказам", callback_data="admin_manage_orders")]
        ]

        # Добавляем кнопку подтверждения для заказов из магазина
        if order_type == "buy_account_shop" and account_id:
            keyboard_buttons.insert(0, [
                InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data=f"admin_complete_order_{order_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_order_{order_id}")
            ])
        elif order_type in ["buy_currency", "buy_software", "buy_account"]:
            keyboard_buttons.insert(0, [
                InlineKeyboardButton(text="✅ Выполнить заказ", callback_data=f"admin_complete_order_{order_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_order_{order_id}")
            ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

        # Отправляем чек и уведомление всем администраторам
        sent_to_admins = 0

        for admin_id in ADMIN_IDS:
            try:
                if file_type == "photo":
                    await bot.send_photo(
                        chat_id=admin_id,
                        photo=file_id,
                        caption=admin_notification[:1024],  # Ограничение длины подписи
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                else:
                    # Для документов отправляем отдельно
                    await bot.send_document(
                        chat_id=admin_id,
                        document=file_id,
                        caption=admin_notification[:1024],
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )

                sent_to_admins += 1
                logger.info(f"✅ Чек по заказу #{order_id} отправлен администратору {admin_id}")

                # Небольшая задержка между отправками
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"❌ Ошибка отправки чека администратору {admin_id}: {str(e)}")
                continue

        logger.info(f"📢 Чек по заказу #{order_id} отправлен {sent_to_admins}/{len(ADMIN_IDS)} администраторам")

        if sent_to_admins == 0:
            logger.error(f"🚨 Чек по заказу #{order_id} НЕ отправлен ни одному администратору!")

            # Отправляем альтернативное уведомление без чека
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=f"🚨 *ВАЖНО! ЧЕК ПО ЗАКАЗУ #{order_id}*\n\n"
                             f"Пользователь отправил чек, но не удалось отправить файл.\n\n"
                             f"{admin_notification}\n\n"
                             f"📞 Свяжитесь с пользователем для получения чека: @{order_username}",
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                except Exception as e:
                    logger.error(f"❌ Ошибка отправки текстового уведомления: {str(e)}")

    except Exception as e:
        logger.error(f"❌ Критическая ошибка обработки чека: {str(e)}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")

        # Все равно сообщаем пользователю об успехе
        await message.answer(
            f"✅ Чек получен!\n\n"
            f"Заказ: #{order_id}\n"
            f"Статус: Ожидает проверки\n\n"
            f"Владелец проверит чек и свяжется с вами для выдачи товара.",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

        # Пытаемся уведомить администраторов об ошибке
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=f"🚨 *ОШИБКА ПРИ ОБРАБОТКЕ ЧЕКА #${order_id}*\n\n"
                         f"Пользователь: @{order_username or 'нет'}\n"
                         f"Ошибка: {str(e)[:200]}",
                    parse_mode="Markdown"
                )
            except:
                pass

        await state.clear()
        return

    # Сообщаем пользователю об успехе
    await message.answer(
        f"✅ *Чек получен!*\n\n"
        f"Заказ: #{order_id}\n"
        f"Статус: Ожидает проверки\n\n"
        f"Владелец проверит чек и свяжется с вами для выдачи товара.",
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

    await state.clear()


@dp.message(Command("notify_admins"))
async def cmd_notify_admins(message: types.Message):
    """Принудительно отправить уведомление администраторам"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа!")
        return

    try:
        # Просим ввести номер заказа
        args = message.text.split()
        if len(args) < 2:
            await message.answer("📝 Использование: /notify_admins <номер_заказа>")
            return

        order_id = int(args[1])
        order = db.get_order_by_id(order_id)

        if not order:
            await message.answer(f"❌ Заказ #{order_id} не найден!")
            return

        # Формируем уведомление
        order_type = order[4]
        order_user_id = order[1]
        order_username = order[2] or "нет"
        order_full_name = order[3] or "Неизвестно"
        order_price = order[7] or "0"

        notification = f"🔔 *ПРИНУДИТЕЛЬНОЕ УВЕДОМЛЕНИЕ*\n\n"
        notification += f"Заказ: #{order_id}\n"
        notification += f"Тип: {order_type}\n"
        notification += f"Пользователь: {order_full_name} (@{order_username})\n"
        notification += f"Сумма: {order_price}\n"
        notification += f"Чек: {'✅ Есть' if order[12] else '❌ Нет'}\n\n"
        notification += f"📅 {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}"

        # Отправляем всем администраторам
        sent_count = 0
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=notification,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text="📋 К заказам", callback_data="admin_manage_orders")]
                    ])
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки принудительного уведомления: {e}")

        await message.answer(f"✅ Уведомление отправлено {sent_count}/{len(ADMIN_IDS)} админам")

    except Exception as e:
        logger.error(f"Ошибка принудительной отправки уведомления: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")













@dp.message(Command("test_notify"))
async def cmd_test_notify(message: types.Message):
    """Тестовая команда для проверки уведомлений"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа!")
        return

    await message.answer("🔄 Тестирование отправки уведомлений...")

    try:
        # Отправляем тестовое уведомление
        test_text = "🔔 *ТЕСТОВОЕ УВЕДОМЛЕНИЕ*\n\nЭто тестовое сообщение для проверки работы уведомлений.\n\n✅ Если вы это видите, уведомления работают!"

        sent_count = 0
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=test_text,
                    parse_mode="Markdown"
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки теста админу {admin_id}: {e}")

        await message.answer(f"✅ Тестовые уведомления отправлены {sent_count}/{len(ADMIN_IDS)} админам")

    except Exception as e:
        logger.error(f"Ошибка тестирования уведомлений: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")


@dp.callback_query(F.data == "buy_software")
async def buy_software_start(callback: types.CallbackQuery, state: FSMContext):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    await state.set_state(Form.buy_software_confirm)

    await state.update_data(
        price=SOFTWARE_PRICE,
        order_type="buy_software"
    )

    software_info = """1. Полное обучение ловли домов
• Подробное видео-обучение
• Советы от опытных ловцов
• Пошаговые инструкции

2. Специальный лаунчер для ловли
• Фулл Обход
• Авто Покупка
• Спидхак — увеличение скорости
• АФК Призрак 
• Заморозка камеры 
• Флудер (Для домов и гаражей)
• Другие полезные функции

5. Лаунчер для ловли в PD
• Бесконечное окно
• Подробный гайд по использованию

Особенности:
• Цена: 200 рублей (навсегда)
• Обновления: Бесплатные
• Поддержка: 24/7

🏠 Начни ловить дома уже сегодня!"""

    await callback.message.edit_text(
        f"✅ **ПОКУПКА СОФТА**\n\n"
        f"💰 **Цена:** {SOFTWARE_PRICE} руб.\n\n"
        f"{software_info}\n\n"
        f"{get_payment_details()}\n"
        f"👉 **Нажмите кнопку 'Купить' для оформления заказа:**",
        parse_mode="Markdown",
        reply_markup=get_payment_keyboard("buy_software")
    )
    await callback.answer()


@dp.callback_query(F.data == "sell_account")
async def sell_account_start(callback: types.CallbackQuery, state: FSMContext):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    await state.set_state(Form.sell_account_server)  # <-- Это состояние существует
    await callback.message.edit_text(
        "👤 *ПРОДАЖА АККАУНТА*\n\n"
        "Выберите сервер:",
        parse_mode="Markdown",
        reply_markup=get_servers_keyboard()
    )
    await callback.answer()


@dp.message(Form.sell_account_description)  # <-- Это состояние существует
async def process_account_desc(message: types.Message, state: FSMContext):
    if not await check_access(message):
        return

    description = message.text.strip()
    await state.update_data(description=description)

    await message.answer(
        f"👤 *ПРОДАЖА АККАУНТА*\n\n"
        f"✅ Описание сохранено\n\n"
        f"Теперь вы можете отправить фото аккаунта (скриншот) или пропустить этот шаг:",
        reply_markup=get_photo_keyboard()
    )


@dp.message(Form.sell_account_price)  # <-- Это состояние существует
async def process_account_price(message: types.Message, state: FSMContext):
    if not await check_access(message):
        return

    price_text = message.text.strip()
    is_valid, price_num, error_msg = validate_price(price_text)

    if not is_valid:
        await message.answer(error_msg, reply_markup=get_cancel_keyboard())
        return

    await state.update_data(price=f"{price_num:,} ₽".replace(',', ' '))
    await state.set_state(Form.sell_account_contacts)  # <-- Переходим к контактам

    await message.answer(
        f"👤 *ПРОДАЖА АККАУНТА*\n\n"
        f"✅ Цена сохранена: {price_num:,} ₽\n\n"
        f"Введите контакты для связи (Telegram, номер):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )


@dp.message(Form.sell_account_contacts)  # <-- ЭТО состояние ДОЛЖНО существовать!
async def process_account_contacts(message: types.Message, state: FSMContext):
    if not await check_access(message):
        return

    contacts = message.text.strip()
    user_data = await state.get_data()

    request_id = db.add_sell_request(
        user_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name,
        server=user_data.get('server'),
        description=user_data.get('description'),
        price=user_data.get('price'),
        contacts=contacts,
        photo_file_id=user_data.get('photo_file_id')
    )

    if request_id:
        await message.answer(
            f"✅ *Заявка на продажу отправлена!*\n\n"
            f"📋 Детали:\n"
            f"• Сервер: {user_data.get('server')}\n"
            f"• Цена: {user_data.get('price')}\n"
            f"• Контакты: {contacts}\n\n"
            f"Владелец свяжется с вами в ближайшее время для обсуждения сделки!",
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

        # Уведомление админам
        try:
            request_text = f"""
🆕 *НОВАЯ ЗАЯВКА НА ПРОДАЖУ АККАУНТА #{request_id}*

👤 Пользователь: {message.from_user.full_name}
📱 Юзернейм: @{message.from_user.username or 'нет'}
🆔 ID: {message.from_user.id}

🖥️ Сервер: {user_data.get('server')}
💰 Цена: {user_data.get('price')}
📞 Контакты: {contacts}

📝 Описание:
{user_data.get('description')}
"""

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 Связаться", url=f"tg://user?id={message.from_user.id}")],
                [InlineKeyboardButton(text="📋 К заявкам", callback_data="admin_manage_requests")]
            ])

            if user_data.get('photo_file_id'):
                await notify_admins(request_text, keyboard, user_data.get('photo_file_id'))
            else:
                await notify_admins(request_text, keyboard)
        except Exception as e:
            logger.error(f"Ошибка отправки уведомления админам: {e}")

    await state.clear()


@dp.callback_query(F.data == "buy_account")
async def buy_account_start(callback: types.CallbackQuery):
    """Начало покупки аккаунта - показываем выбор аккаунта"""
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    # Получаем все аккаунты
    accounts = db.get_shop_accounts_for_gallery()

    if not accounts:
        await callback.message.edit_text(
            "🛍️ *МАГАЗИН АККАУНТОВ*\n\n"
            "😔 *Пока нет аккаунтов в продаже*\n\n"
            "Новые аккаунты появляются регулярно!\n"
            "Следите за обновлениями.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Проверить снова", callback_data="buy_account")],
                [InlineKeyboardButton(text="🏠 В главное меню", callback_data="to_menu")]
            ])
        )
        return

    # Показываем выбор аккаунта
    await show_account_selection(callback, accounts)
    await callback.answer()


async def show_account_selection(callback: types.CallbackQuery, accounts):
    """Показывает выбор аккаунта с плавающей клавиатурой"""
    try:
        # Сначала загружаем аккаунты заново
        accounts = db.get_shop_accounts_for_gallery()

        if not accounts:
            await callback.message.edit_text(
                "🛍️ *МАГАЗИН АККАУНТОВ*\n\n"
                "😔 *Пока нет аккаунтов в продаже*\n\n"
                "Новые аккаунты появляются регулярно!\n"
                "Следите за обновлениями.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔄 Проверить снова", callback_data="buy_account")],
                    [InlineKeyboardButton(text="🏠 В главное меню", callback_data="to_menu")]
                ])
            )
            return

        text = "🛍️ *ВЫБЕРИТЕ АККАУНТ ДЛЯ ПОКУПКИ:*\n\n"
        keyboard = InlineKeyboardBuilder()

        for acc in accounts[:20]:  # Ограничиваем 20 аккаунтами
            try:
                acc_id = acc[0]
                server = acc[1] if acc[1] else "Без сервера"
                title = acc[2] if acc[2] else "Без названия"
                price = acc[4] if len(acc) > 4 else 0

                # Форматируем цену
                try:
                    if isinstance(price, (int, float)):
                        price_num = int(price)
                        formatted_price = f"{price_num:,} ₽".replace(',', ' ')
                    else:
                        # Извлекаем цифры из строки
                        if isinstance(price, str):
                            price_clean = ''.join(filter(str.isdigit, price))
                            price_num = int(price_clean) if price_clean else 0
                        else:
                            price_num = 0
                        formatted_price = f"{price_num:,} ₽".replace(',', ' ')
                except:
                    formatted_price = "0 ₽"

                # Создаем текст кнопки
                button_text = f"#{acc_id} {server} - {formatted_price}"
                if len(button_text) > 40:
                    button_text = button_text[:37] + "..."

                # Кнопка аккаунта
                keyboard.row(
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"select_acc_{acc_id}"
                    )
                )

            except Exception as e:
                logger.error(f"Ошибка обработки аккаунта: {e}")
                continue

        # Кнопки навигации
        keyboard.row(
            InlineKeyboardButton(text="◀️ В меню", callback_data="to_menu"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="buy_account")
        )

        if len(accounts) > 20:
            text += f"*Доступно {len(accounts)} аккаунтов*\n"
            text += "Показаны первые 20. Уточните запрос.\n\n"
        else:
            text += f"*Доступно {len(accounts)} аккаунтов*\n\n"

        text += "Нажмите на аккаунт для просмотра деталей и покупки."

        # Удаляем предыдущее сообщение и отправляем новое
        try:
            await callback.message.delete()
        except:
            pass

        await callback.message.answer(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard.as_markup()
        )

    except Exception as e:
        logger.error(f"Ошибка показа выбора аккаунта: {e}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки аккаунтов!", show_alert=True)


@dp.callback_query(F.data.startswith("select_acc_"))
async def select_account_handler(callback: types.CallbackQuery):
    """Обработка выбора аккаунта"""
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    try:
        # Получаем ID аккаунта
        account_id = int(callback.data.replace("select_acc_", ""))

        logger.info(f"Выбран аккаунт #{account_id} пользователем {callback.from_user.id}")

        # Получаем аккаунт из базы
        account = db.get_shop_account_by_id(account_id)

        if not account:
            await callback.answer("❌ Аккаунт не найден или уже продан!", show_alert=True)
            return

        # Показываем детали аккаунта
        await show_account_details_simple(callback, account)

    except ValueError:
        await callback.answer("❌ Ошибка: неверный ID аккаунта!", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в select_account_handler: {e}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки аккаунта!", show_alert=True)


async def show_account_details_simple(callback: types.CallbackQuery, account):
    """Показывает детали аккаунта"""
    try:
        # Распаковываем данные
        acc_id = account[0]
        server = account[1] if account[1] else "Не указан"
        title = account[2] if account[2] else "Без названия"
        description = account[3] if account[3] else "Без описания"
        price = account[4] if len(account) > 4 else 0
        category = account[5] if len(account) > 5 else "standart"
        level = account[6] if len(account) > 6 else 1
        virt_amount = account[7] if len(account) > 7 else ""
        bindings = account[8] if len(account) > 8 else ""
        contacts = account[9] if len(account) > 9 else ""
        photo_file_id = account[10] if len(account) > 10 else None

        # Проверяем, продан ли аккаунт
        is_sold = db.is_account_sold(acc_id)

        # Форматируем цену
        try:
            if isinstance(price, (int, float)):
                price_num = int(price)
                formatted_price = f"{price_num:,} ₽".replace(',', ' ')
            else:
                price_clean = ''.join(filter(str.isdigit, str(price)))
                price_num = int(price_clean) if price_clean else 0
                formatted_price = f"{price_num:,} ₽".replace(',', ' ')
        except:
            formatted_price = str(price)

        # Формируем текст
        account_text = f"""🛍️ *АККАУНТ #{acc_id}*

📋 *Категория:* {category}
📊 *Уровень:* {level}
🖥️ *Сервер:* {server}
💰 *Цена:* {formatted_price}
{'❌ *ПРОДАН*' if is_sold else '✅ *В НАЛИЧИИ*'}

📝 *Описание:*
{description[:500]}{'...' if len(description) > 500 else ''}

🔗 *Привязки:* {bindings if bindings else 'Нет'}
💎 *Вирты:* {virt_amount if virt_amount else 'Не указано'}
📞 *Контакты:* {contacts if contacts else 'Не указаны'}"""

        # Создаем клавиатуру
        keyboard = InlineKeyboardBuilder()

        if not is_sold:
            # Кнопка покупки только если не продан
            keyboard.row(
                InlineKeyboardButton(
                    text="💸 Купить этот аккаунт",
                    callback_data=f"buy_acc_{acc_id}"
                )
            )
        else:
            keyboard.row(
                InlineKeyboardButton(
                    text="❌ ПРОДАН",
                    callback_data="no_action"
                )
            )

        # Кнопки навигации
        keyboard.row(
            InlineKeyboardButton(text="🔙 Назад к списку", callback_data="buy_account"),
            InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu")
        )

        # Отправляем сообщение
        try:
            if photo_file_id:
                await bot.send_photo(
                    chat_id=callback.from_user.id,
                    photo=photo_file_id,
                    caption=account_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard.as_markup()
                )
                await callback.message.delete()
            else:
                await callback.message.edit_text(
                    account_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard.as_markup()
                )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            await callback.message.answer(
                account_text,
                parse_mode="Markdown",
                reply_markup=keyboard.as_markup()
            )

    except Exception as e:
        logger.error(f"Ошибка в show_account_details_simple: {e}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки аккаунта!", show_alert=True)













async def show_account_details(callback: types.CallbackQuery, account):
    """Показывает детали аккаунта с кнопкой покупки"""
    try:
        # Проверяем структуру данных
        if len(account) >= 12:
            acc_id, server, title, description, price, category, level, virt_amount, bindings, contacts, photo_file_id, created_at = account[
                :12]

            # Форматируем дату
            if created_at:
                if isinstance(created_at, str):
                    created_date = created_at.split()[0]
                elif hasattr(created_at, 'strftime'):
                    created_date = created_at.strftime('%Y-%m-%d')
                else:
                    created_date = str(created_at)[:10]
            else:
                created_date = "Недавно"

            # Форматируем цену
            try:
                if isinstance(price, (int, float)):
                    price_num = int(price)
                    formatted_price = f"{price_num:,} ₽".replace(',', ' ')
                else:
                    # Извлекаем цифры из строки
                    price_clean = ''.join(filter(str.isdigit, str(price)))
                    price_num = int(price_clean) if price_clean else 0
                    formatted_price = f"{price_num:,} ₽".replace(',', ' ')
            except:
                formatted_price = str(price)

            # Формируем текст
            account_text = f"""🛍️ *АККАУНТ #{acc_id}*

📋 *Категория:* {category}
📊 *Уровень:* {level}
🖥️ *Сервер:* {server}
💰 *Цена:* {formatted_price}
📅 *Добавлен:* {created_date}

📝 *Описание:*
{description[:300]}{'...' if len(description) > 300 else ''}

🔗 *Привязки:* {bindings if bindings else 'Нет'}
💎 *Вирты:* {virt_amount if virt_amount else 'Не указано'}
📞 *Контакты:* {contacts if contacts else 'Не указаны'}"""

            # Создаем клавиатуру
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💸 Купить этот аккаунт", callback_data=f"buy_acc_{acc_id}")],
                [InlineKeyboardButton(text="🔙 Назад к выбору", callback_data="buy_account")],
                [InlineKeyboardButton(text="🏠 В главное меню", callback_data="to_menu")]
            ])

            try:
                if photo_file_id:
                    await bot.send_photo(
                        chat_id=callback.from_user.id,
                        photo=photo_file_id,
                        caption=account_text,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                    await callback.message.delete()
                else:
                    await callback.message.edit_text(
                        account_text,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
            except Exception as e:
                logger.error(f"Ошибка показа аккаунта: {e}")
                await callback.message.edit_text(
                    account_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
        else:
            logger.error(f"Неверная структура данных аккаунта: {len(account)} полей")
            await callback.answer("❌ Ошибка данных аккаунта!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка в show_account_details: {e}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки аккаунта!", show_alert=True)







async def show_account_list(callback: types.CallbackQuery, accounts):
    """Показывает список аккаунтов для выбора"""
    try:
        if not accounts:
            await callback.answer("❌ Нет аккаунтов!", show_alert=True)
            return

        text = "🛍️ *ВЫБЕРИТЕ АККАУНТ:*\n\n"
        keyboard = InlineKeyboardBuilder()

        for i, acc in enumerate(accounts[:10]):  # Показываем первые 10
            try:
                acc_id = acc[0]
                server = acc[1] if len(acc) > 1 else "Без сервера"
                title = acc[2] if len(acc) > 2 else "Без названия"
                price = acc[4] if len(acc) > 4 else "0"

                # Форматируем цену
                try:
                    if isinstance(price, (int, float)):
                        formatted_price = f"{int(price):,} ₽".replace(',', ' ')
                    else:
                        price_clean = ''.join(filter(str.isdigit, str(price)))
                        price_num = int(price_clean) if price_clean else 0
                        formatted_price = f"{price_num:,} ₽".replace(',', ' ')
                except:
                    formatted_price = str(price)

                button_text = f"#{acc_id} - {server} - {formatted_price}"
                if len(button_text) > 50:
                    button_text = button_text[:47] + "..."

                keyboard.row(
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"select_acc_{acc_id}"
                    )
                )

                # Добавляем в текст
                text += f"{i + 1}. *Аккаунт #{acc_id}*\n"
                text += f"   Сервер: {server}\n"
                text += f"   Цена: {formatted_price}\n"
                if title and len(title) > 2:
                    text += f"   Описание: {title[:30]}...\n"
                text += "\n"

            except Exception as e:
                logger.error(f"Ошибка обработки аккаунта {i}: {e}")
                continue

        if len(accounts) > 10:
            text += f"\n... и еще {len(accounts) - 10} аккаунтов"

        # Кнопки навигации
        keyboard.row(
            InlineKeyboardButton(text="◀️ Назад", callback_data="to_menu"),
            InlineKeyboardButton(text="🔄 Обновить", callback_data="buy_account")
        )

        await callback.message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=keyboard.as_markup()
        )

    except Exception as e:
        logger.error(f"Ошибка показа списка аккаунтов: {e}")
        await callback.answer("❌ Ошибка загрузки списка!", show_alert=True)



def get_account_navigation_keyboard(accounts, current_index):
    """Клавиатура навигации по аккаунтам"""
    keyboard = InlineKeyboardBuilder()

    # Кнопки навигации
    nav_buttons = []

    # Проверяем, есть ли предыдущий аккаунт
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(
            text="◀️ Предыдущий",
            callback_data=f"shop_acc_{current_index - 1}"
        ))

    # Кнопка покупки текущего аккаунта
    if accounts and current_index < len(accounts):
        try:
            acc_id = accounts[current_index][0]
            keyboard.row(
                InlineKeyboardButton(
                    text="💸 Купить этот аккаунт",
                    callback_data=f"buy_acc_{acc_id}"
                )
            )
        except Exception as e:
            logger.error(f"Ошибка получения ID аккаунта: {e}")

    # Проверяем, есть ли следующий аккаунт
    if current_index < len(accounts) - 1:
        nav_buttons.append(InlineKeyboardButton(
            text="▶️ Следующий",
            callback_data=f"shop_acc_{current_index + 1}"
        ))

    if nav_buttons:
        keyboard.row(*nav_buttons)

    # Общая информация
    if accounts:
        keyboard.row(InlineKeyboardButton(
            text=f"📊 {current_index + 1}/{len(accounts)}",
            callback_data="no_action"
        ))

    keyboard.row(InlineKeyboardButton(text="🏠 В главное меню", callback_data="to_menu"))

    return keyboard.as_markup()

@dp.callback_query(F.data.startswith("shop_page_"))
async def shop_page_navigation(callback: types.CallbackQuery):
    """Навигация по страницам магазина"""
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    try:
        page = int(callback.data.replace("shop_page_", ""))

        # Получаем аккаунты для указанной страницы
        result = db.get_shop_accounts_paginated(page=page, per_page=1)

        if not result['accounts']:
            await callback.answer("❌ На этой странице нет аккаунтов!", show_alert=True)

            # Возвращаемся на первую страницу
            result = db.get_shop_accounts_paginated(page=0, per_page=1)
            if result['accounts']:
                await show_account(callback, result['accounts'], 0, result)
        else:
            # Показываем первый аккаунт на странице
            await show_account(callback, result['accounts'], 0, result)

    except Exception as e:
        logger.error(f"Ошибка навигации по страницам: {e}")
        await callback.answer("❌ Ошибка перехода на страницу!", show_alert=True)

    await callback.answer()




async def show_account(callback: types.CallbackQuery, accounts, index, pagination_data=None):
    """Показывает аккаунт с индексом"""
    try:
        if index < 0 or index >= len(accounts):
            await callback.answer("❌ Аккаунт не найден!", show_alert=True)
            return

        acc = accounts[index]

        # Проверяем структуру данных
        if len(acc) >= 12:
            acc_id, server, title, description, price, category, level, virt_amount, bindings, contacts, photo_file_id, created_at = acc[:12]

            # Форматируем текст
            account_text = f"""
🛍️ *АККАУНТ #{acc_id}*

🖥️ *Сервер:* {server}
💰 *Цена:* {price:,} ₽
📅 *Добавлен:* {created_at[:10] if created_at else 'Недавно'}
📋 *Категория:* {category}
📊 *Уровень:* {level}

📝 *Заголовок:*
{title}

📝 *Описание:*
{description[:500]}{'...' if len(description) > 500 else ''}

🔗 *Привязки:* {bindings if bindings else 'Нет'}
💎 *Вирты:* {virt_amount if virt_amount else 'Не указано'}
📞 *Контакты:* {contacts if contacts else 'Не указаны'}
"""
            # Получаем клавиатуру
            keyboard = get_account_navigation_keyboard(accounts, index)

            try:
                if photo_file_id:
                    await bot.send_photo(
                        chat_id=callback.from_user.id,
                        photo=photo_file_id,
                        caption=account_text,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
                    await callback.message.delete()
                else:
                    await callback.message.edit_text(
                        account_text,
                        parse_mode="Markdown",
                        reply_markup=keyboard
                    )
            except Exception as e:
                logger.error(f"Ошибка показа аккаунта: {e}")
                await callback.message.edit_text(
                    account_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
        else:
            logger.error(f"Неверная структура данных аккаунта: {len(acc)} полей")
            await callback.answer("❌ Ошибка данных аккаунта!", show_alert=True)
    except Exception as e:
        logger.error(f"Ошибка в show_account: {e}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки аккаунта!", show_alert=True)


@dp.callback_query(F.data.startswith("shop_acc_"))
async def navigate_accounts(callback: types.CallbackQuery):
    """Навигация по аккаунтам"""
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    try:
        # Извлекаем данные: shop_acc_страница_индекс
        parts = callback.data.replace("shop_acc_", "").split("_")

        if len(parts) >= 2:
            page = int(parts[0])
            index = int(parts[1])
        else:
            # Старый формат для обратной совместимости
            index = int(callback.data.replace("shop_acc_", ""))
            page = 0

        # Получаем аккаунты для страницы
        result = db.get_shop_accounts_paginated(page=page, per_page=1)

        if not result['accounts']:
            await callback.answer("❌ Нет доступных аккаунтов!", show_alert=True)
            return

        # Проверяем границы
        if index < 0:
            index = 0
        elif index >= len(result['accounts']):
            index = len(result['accounts']) - 1

        await show_account(callback, result['accounts'], index, result)

    except Exception as e:
        logger.error(f"Ошибка навигации: {e}")
        await callback.answer("❌ Ошибка!", show_alert=True)

    await callback.answer()


@dp.callback_query(F.data.startswith("buy_acc_"))
async def buy_account_process(callback: types.CallbackQuery, state: FSMContext):
    """Покупка выбранного аккаунта - УПРОЩЕННАЯ ВЕРСИЯ"""
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    try:
        account_id = int(callback.data.replace("buy_acc_", ""))

        logger.info(f"Начало покупки аккаунта #{account_id} пользователем {callback.from_user.id}")

        # Получаем аккаунт из магазина (accounts_shop)
        account = db.get_shop_account_by_id(account_id)
        if not account:
            await callback.answer("❌ Аккаунт не найден или уже продан!", show_alert=True)
            return

        # Распаковываем данные из accounts_shop (12 полей)
        try:
            # account содержит: id, server, title, description, price, category, level,
            # virt_amount, bindings, contacts, photo_file_id, created_at
            acc_id = account[0]
            server = account[1] if account[1] else "Не указан"
            title = account[2] if account[2] else "Без названия"
            description = account[3] if account[3] else "Без описания"
            price = account[4]
            # category = account[5] - не нужно для покупки
            # level = account[6] - не нужно для покупки
            # virt_amount = account[7] - не нужно для покупки
            # bindings = account[8] - не нужно для покупки
            # contacts = account[9] - не нужно для покупки
            # photo_file_id = account[10] - не нужно для покупки
            # created_at = account[11] - не нужно для покупки

            logger.info(f"Данные аккаунта #{acc_id}: сервер={server}, цена={price}, title={title[:30]}")
        except Exception as e:
            logger.error(f"Ошибка распаковки данных аккаунта: {e}")
            await callback.answer("❌ Ошибка данных аккаунта!", show_alert=True)
            return

        # Форматируем цену
        try:
            if isinstance(price, (int, float)):
                price_num = int(price)
                formatted_price = f"{price_num:,} ₽".replace(',', ' ')
            else:
                # Извлекаем цифры из строки
                if isinstance(price, str):
                    price_clean = ''.join(filter(str.isdigit, str(price)))
                    price_num = int(price_clean) if price_clean else 0
                else:
                    price_num = 0
                formatted_price = f"{price_num:,} ₽".replace(',', ' ')
        except Exception as e:
            logger.error(f"Ошибка форматирования цены: {e}")
            formatted_price = str(price)
            price_num = 0

        # Сохраняем минимальные данные для заказа
        await state.update_data({
            'account_id': acc_id,
            'server': server,
            'price': price_num,
            'formatted_price': formatted_price,
            'description': f"Аккаунт #{acc_id} - {server} - {title[:50]}",
            'order_type': 'buy_account_shop'  # Новый тип заказа для магазина
        })

        # Показываем простую форму подтверждения
        await callback.message.edit_text(
            f"🛒 *ПОДТВЕРЖДЕНИЕ ПОКУПКИ*\n\n"
            f"📋 *Детали аккаунта:*\n"
            f"• ID: #{acc_id}\n"
            f"• Сервер: {server}\n"
            f"• Название: {title[:50]}{'...' if len(title) > 50 else ''}\n"
            f"• Цена: {formatted_price}\n\n"
            f"💳 *Для оплаты:*\n"
            f"📱 Номер: `{PAYMENT_DETAILS['phone']}`\n"
            f"👤 Имя: {PAYMENT_DETAILS['name']}\n"
            f"🏦 Банк: {PAYMENT_DETAILS['bank']}\n\n"
            f"⚠️ После оплаты отправьте чек\n\n"
            f"Нажмите '💸 Купить' для оформления заказа:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💸 Купить", callback_data=f"confirm_buy_shop_{acc_id}")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"select_acc_{acc_id}")],
                [InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu")]
            ])
        )

    except Exception as e:
        logger.error(f"Ошибка в buy_account_process: {e}", exc_info=True)
        await callback.answer("❌ Ошибка оформления покупки!", show_alert=True)

    await callback.answer()


@dp.callback_query(F.data.startswith("confirm_buy_shop_"))
async def simple_confirm_buy(callback: types.CallbackQuery):
    """САМАЯ ПРОСТАЯ версия подтверждения покупки"""
    try:
        account_id = int(callback.data.replace("confirm_buy_shop_", ""))

        # Получаем аккаунт
        account = db.get_shop_account_by_id(account_id)
        if not account:
            await callback.answer("❌ Аккаунт не найден!", show_alert=True)
            return

        acc_id = account[0]
        server = account[1] if account[1] else "Без сервера"
        title = account[2] if account[2] else "Без названия"
        price = account[4] if len(account) > 4 else 0

        # Проверяем, не продан ли уже аккаунт
        if db.is_account_sold(account_id):
            await callback.answer("❌ Этот аккаунт уже продан!", show_alert=True)
            return

        # Форматируем цену
        if isinstance(price, (int, float)):
            formatted_price = f"{int(price):,} ₽".replace(',', ' ')
            price_str = formatted_price
        else:
            formatted_price = str(price)
            price_str = formatted_price

        # Создаем заказ БЕЗ пометки как проданного
        order_id = db.add_order(
            user_id=callback.from_user.id,
            username=callback.from_user.username,
            full_name=callback.from_user.full_name,
            order_type="buy_account_shop",
            server=server,
            amount="1 аккаунт",
            price=price_str,
            description=f"Аккаунт #{acc_id} - {server} - {title[:50]}",
            contacts=f"@{callback.from_user.username or 'нет'}",
            payment_method="Онлайн оплата"
        )

        if order_id:
            # Уведомляем администраторов
            asyncio.create_task(
                send_admin_notification_for_account_order(
                    order_id=order_id,
                    account_id=acc_id,
                    user_id=callback.from_user.id,
                    username=callback.from_user.username,
                    full_name=callback.from_user.full_name,
                    server=server,
                    price=formatted_price,
                    account_title=title
                )
            )

            await callback.message.edit_text(
                f"✅ *ЗАКАЗ ОФОРМЛЕН!*\n\n"
                f"🆔 Номер заказа: #{order_id}\n"
                f"📦 Аккаунт: #{acc_id}\n"
                f"💰 Сумма: {formatted_price}\n\n"
                f"💳 *Реквизиты для оплаты:*\n"
                f"📱 Номер: `{PAYMENT_DETAILS['phone']}`\n"
                f"👤 Имя: {PAYMENT_DETAILS['name']}\n"
                f"🏦 Банк: {PAYMENT_DETAILS['bank']}\n\n"
                f"📝 *Что делать дальше:*\n"
                f"1. Оплатите по реквизитам\n"
                f"2. Нажмите '📄 Отправить чек'\n"
                f"3. Владелец проверит оплату и отдаст данные аккаунта",
                parse_mode="Markdown",
                reply_markup=get_receipt_keyboard(order_id)
            )

        else:
            await callback.answer("❌ Ошибка создания заказа!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка в simple_confirm_buy: {e}", exc_info=True)
        await callback.answer(f"❌ Ошибка: {str(e)[:50]}", show_alert=True)

    await callback.answer()


@dp.callback_query(F.data.startswith("admin_confirm_account_payment_"))
async def admin_confirm_account_payment(callback: types.CallbackQuery):
    """Администратор подтверждает оплату за аккаунт"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    try:
        # Формат: admin_confirm_account_payment_orderId_accountId
        data = callback.data.replace("admin_confirm_account_payment_", "")
        parts = data.split("_")

        if len(parts) < 2:
            await callback.answer("❌ Ошибка данных!", show_alert=True)
            return

        order_id = int(parts[0])
        account_id = int(parts[1])

        # Получаем заказ
        order = db.get_order_by_id(order_id)
        if not order:
            await callback.answer("❌ Заказ не найден!", show_alert=True)
            return

        # Помечаем аккаунт как проданный
        buyer_id = order[1]  # user_id из заказа
        if db.mark_shop_account_sold(account_id, buyer_id):
            # Обновляем статус заказа
            db.update_order_status(order_id, 'completed')

            # Уведомляем покупателя
            try:
                await bot.send_message(
                    chat_id=buyer_id,
                    text=f"🎉 *ОПЛАТА ПОДТВЕРЖДЕНА!*\n\n"
                         f"✅ Ваш заказ #{order_id} выполнен!\n"
                         f"📦 Аккаунт: #{account_id}\n\n"
                         f"👑 *Данные аккаунта:*\n"
                         f"Владелец свяжется с вами для передачи данных аккаунта.\n\n"
                         f"📞 Если возникли вопросы, обращайтесь к @Kornycod",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка уведомления покупателя: {e}")

            # Уведомление другим админам
            confirm_text = f"""✅ *ОПЛАТА ПОДТВЕРЖДЕНА*

👤 Подтвердил: {callback.from_user.full_name}
📦 Аккаунт: #{account_id}
💰 Заказ: #{order_id}
👤 Покупатель: {order[3]} (@{order[2] or 'нет'})
🆔 ID покупателя: {buyer_id}

✅ Аккаунт помечен как проданный.
👑 Теперь свяжитесь с покупателем для передачи данных."""

            await notify_admins(confirm_text)

            await callback.answer("✅ Оплата подтверждена! Аккаунт помечен как проданный.", show_alert=True)

            # Возвращаемся к списку заказов
            await admin_manage_orders(callback)
        else:
            await callback.answer("❌ Ошибка при пометке аккаунта как проданного!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка подтверждения оплаты аккаунта: {e}")
        await callback.answer("❌ Ошибка подтверждения оплаты!", show_alert=True)


@dp.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало рассылки сообщений всем пользователям"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    # Получаем статистику пользователей
    users = db.get_all_users()
    total_users = len(users) if users else 0

    if total_users == 0:
        await callback.answer("❌ Нет пользователей для рассылки!", show_alert=True)
        return

    await state.set_state(Form.admin_broadcast_message)

    await callback.message.edit_text(
        f"📢 *РАССЫЛКА СООБЩЕНИЙ*\n\n"
        f"👥 Всего пользователей: {total_users}\n\n"
        f"✍️ *Введите сообщение для рассылки:*\n\n"
        f"📝 *Поддерживается:*\n"
        f"• Текст\n"
        f"• Эмодзи\n"
        f"• Разметка Markdown\n"
        f"• Ссылки\n\n"
        f"⚠️ *Внимание:*\n"
        f"• Сообщение будет отправлено ВСЕМ пользователям\n"
        f"• Нельзя отменить после отправки\n"
        f"• Рекомендуется тестировать на себе сначала",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚫 Отмена", callback_data="to_admin_menu")]
        ])
    )
    await callback.answer()


@dp.message(Form.admin_broadcast_message)
async def admin_broadcast_get_message(message: types.Message, state: FSMContext):
    """Получение сообщения для рассылки"""
    if not is_admin(message.from_user.id):
        return

    broadcast_text = message.text.strip()

    if not broadcast_text:
        await message.answer("❌ Сообщение не может быть пустым!")
        return

    if len(broadcast_text) > 4000:
        await message.answer("❌ Сообщение слишком длинное (максимум 4000 символов)")
        return

    # Сохраняем текст и ID сообщения (для возможного ответа)
    await state.update_data(
        broadcast_text=broadcast_text,
        broadcast_message_id=message.message_id
    )
    await state.set_state(Form.admin_broadcast_confirm)

    # Получаем статистику пользователей
    users = db.get_all_users()
    total_users = len(users) if users else 0

    # Показываем предпросмотр
    preview_text = f"📢 *ПРЕДПРОСМОТР РАССЫЛКИ*\n\n"
    preview_text += f"👥 Будет отправлено: {total_users} пользователям\n\n"
    preview_text += f"📝 *Ваше сообщение:*\n"
    preview_text += f"━━━━━━━━━━━━━━━━━━━━\n"
    preview_text += f"{broadcast_text[:500]}"
    if len(broadcast_text) > 500:
        preview_text += f"\n... (еще {len(broadcast_text) - 500} символов)"
    preview_text += f"\n━━━━━━━━━━━━━━━━━━━━\n\n"
    preview_text += f"✅ *Отправить рассылку?*"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, отправить", callback_data="broadcast_confirm"),
            InlineKeyboardButton(text="✏️ Изменить", callback_data="admin_broadcast")
        ],
        [InlineKeyboardButton(text="🚫 Отмена", callback_data="to_admin_menu")]
    ])

    await message.answer(
        preview_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@dp.callback_query(F.data == "broadcast_confirm")
async def admin_broadcast_send(callback: types.CallbackQuery, state: FSMContext):
    """Улучшенная отправка рассылки всем пользователям"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    await callback.answer("⏳ Начинаю рассылку...", show_alert=False)

    user_data = await state.get_data()
    broadcast_text = user_data.get('broadcast_text', '')

    if not broadcast_text:
        await callback.message.edit_text("❌ Ошибка: текст рассылки не найден")
        await state.clear()
        return

    # Получаем всех пользователей
    users = db.get_all_users()

    if not users:
        await callback.message.edit_text("❌ Нет пользователей для рассылки")
        await state.clear()
        return

    total_users = len(users)
    sent_count = 0
    failed_count = 0
    blocked_count = 0

    # Отправляем уведомление о начале рассылки
    status_message = await callback.message.edit_text(
        f"📢 *РАССЫЛКА НАЧАТА*\n\n"
        f"⏳ Отправка сообщения {total_users} пользователям...\n"
        f"✅ Отправлено: 0\n"
        f"❌ Ошибок: 0\n"
        f"🚫 Заблокировали: 0",
        parse_mode="Markdown"
    )

    start_time = datetime.now()

    # ОТПРАВЛЯЕМ СООБЩЕНИЯ ПООЧЕРЕДНО
    for i, user in enumerate(users):
        try:
            user_id = user[0]  # первый элемент - user_id

            # Пропускаем админов, если они есть в списке
            if user_id in ADMIN_IDS:
                continue

            # Отправляем сообщение
            await bot.send_message(
                chat_id=user_id,
                text=broadcast_text,
                parse_mode="Markdown"
            )
            sent_count += 1

            # Обновляем статус каждые 10 сообщений
            if i % 10 == 0 or i == len(users) - 1:
                elapsed = (datetime.now() - start_time).seconds
                speed = sent_count / max(elapsed, 1)

                try:
                    await status_message.edit_text(
                        f"📢 *РАССЫЛКА В ПРОЦЕССЕ*\n\n"
                        f"⏳ Обработано: {i + 1}/{len(users)}\n"
                        f"✅ Отправлено: {sent_count}\n"
                        f"❌ Ошибок: {failed_count}\n"
                        f"🚫 Заблокировали: {blocked_count}\n"
                        f"📊 Скорость: {speed:.1f} сообщ/сек\n"
                        f"⏱ Время: {elapsed} сек",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Ошибка обновления статуса: {e}")

            # Задержка чтобы не превышать лимиты Telegram
            await asyncio.sleep(0.1)  # 10 сообщений в секунду

        except Exception as e:
            error_msg = str(e).lower()
            logger.warning(f"Ошибка отправки пользователю {user[0] if user else 'unknown'}: {error_msg}")

            # Проверяем частые ошибки
            if "bot was blocked" in error_msg or "user is deactivated" in error_msg:
                blocked_count += 1
            elif "chat not found" in error_msg or "user not found" in error_msg:
                blocked_count += 1
            elif "forbidden" in error_msg:
                blocked_count += 1
            elif "bot can't initiate conversation" in error_msg:
                blocked_count += 1
            else:
                failed_count += 1
            continue

    # Рассчитываем итоговую статистику
    end_time = datetime.now()
    total_time = (end_time - start_time).seconds
    success_rate = (sent_count / len(users) * 100) if len(users) > 0 else 0

    # Сохраняем историю рассылки
    try:
        db.add_broadcast_history(
            admin_id=callback.from_user.id,
            admin_name=callback.from_user.full_name,
            message_text=broadcast_text[:500],
            total_users=len(users),
            sent_success=sent_count,
            sent_failed=failed_count,
            blocked_users=blocked_count,
            status='completed'
        )
    except Exception as e:
        logger.error(f"Ошибка сохранения истории рассылки: {e}")

    # Формируем итоговый отчет
    result_text = f"""📢 *РАССЫЛКА ЗАВЕРШЕНА*

📊 *Итоговая статистика:*
• Всего пользователей: {len(users)}
• Успешно отправлено: {sent_count}
• Заблокировали бота: {blocked_count}
• Ошибок отправки: {failed_count}
• Процент успеха: {success_rate:.1f}%

⏱ *Время выполнения:*
• Начало: {start_time.strftime('%H:%M:%S')}
• Конец: {end_time.strftime('%H:%M:%S')}
• Общее время: {total_time} секунд

📝 *Сообщение отправлено.*"""

    # Отправляем итоговый отчет
    try:
        await status_message.edit_text(
            result_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 История рассылок", callback_data="admin_broadcast_history")],
                [InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu")]
            ])
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования статусного сообщения: {e}")
        await callback.message.answer(
            result_text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 История рассылок", callback_data="admin_broadcast_history")],
                [InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu")]
            ])
        )

    # Очищаем состояние
    await state.clear()


@dp.callback_query(F.data == "admin_broadcast_history")
async def admin_broadcast_history(callback: types.CallbackQuery):
    """Просмотр истории рассылок"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    try:
        # Получаем историю рассылок из базы данных
        db.cursor.execute("""
            SELECT id, admin_name, message_text, total_users, sent_success, 
                   sent_failed, blocked_users, created_at
            FROM broadcasts 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        broadcasts = db.cursor.fetchall()

        if not broadcasts:
            await callback.message.edit_text(
                "📋 *ИСТОРИЯ РАССЫЛОК*\n\n"
                "📭 Нет записей о рассылках\n\n"
                "Здесь будет отображаться история всех проведенных рассылок.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast")]
                ])
            )
        else:
            history_text = f"📋 *ИСТОРИЯ РАССЫЛОК*\n\n"
            history_text += f"📊 Всего записей: {len(broadcasts)}\n\n"

            for broadcast in broadcasts[:5]:  # Показываем первые 5
                b_id, admin_name, message_text, total_users, sent_success, sent_failed, blocked_users, created_at = broadcast

                # Форматируем дату
                if isinstance(created_at, str):
                    created_date = created_at[:10]
                elif hasattr(created_at, 'strftime'):
                    created_date = created_at.strftime('%Y-%m-%d')
                else:
                    created_date = str(created_at)[:10]

                success_rate = (sent_success / total_users * 100) if total_users > 0 else 0

                history_text += f"📧 *Рассылка #{b_id}*\n"
                history_text += f"👤 Админ: {admin_name}\n"
                history_text += f"📅 Дата: {created_date}\n"
                history_text += f"👥 Получателей: {total_users}\n"
                history_text += f"✅ Отправлено: {sent_success}\n"
                history_text += f"❌ Ошибок: {sent_failed + blocked_users}\n"
                history_text += f"📊 Успех: {success_rate:.1f}%\n"
                history_text += f"📝 Текст: {message_text[:50]}...\n\n"

            if len(broadcasts) > 5:
                history_text += f"📁 ... и еще {len(broadcasts) - 5} записей\n"

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_broadcast_history")],
                [InlineKeyboardButton(text="📢 Новая рассылка", callback_data="admin_broadcast")],
                [InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu")]
            ])

            await callback.message.edit_text(
                history_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"Ошибка получения истории рассылок: {e}")
        await callback.message.edit_text(
            f"📋 *ИСТОРИЯ РАССЫЛОК*\n\n"
            f"❌ Ошибка получения данных: {str(e)}\n\n"
            f"Попробуйте позже.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_broadcast")]
            ])
        )
    await callback.answer()










@dp.callback_query(F.data == "broadcast_report_detail")
async def broadcast_report_detail(callback: types.CallbackQuery):
    """Подробный отчет о рассылке"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    # Здесь можно добавить логику для сохранения и отображения
    # детальной статистики по рассылке

    await callback.message.answer(
        "📊 *ДЕТАЛЬНЫЙ ОТЧЕТ ПО РАССЫЛКЕ*\n\n"
        "Для детального отчета необходимо:\n"
        "1. Сохранять статистику в базу данных\n"
        "2. Логировать каждую отправку\n"
        "3. Вести историю рассылок\n\n"
        "⚠️ Эта функция требует доработки базы данных",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="to_admin_menu")]
        ])
    )
    await callback.answer()


@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    """Команда для быстрой рассылки"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа!")
        return

    # Получаем текст сообщения
    if len(message.text.split()) < 2:
        await message.answer(
            "📢 *Быстрая рассылка*\n\n"
            "Использование: `/broadcast <текст сообщения>`\n\n"
            "Пример:\n"
            "`/broadcast Привет! Новые аккаунты в продаже!`",
            parse_mode="Markdown"
        )
        return

    broadcast_text = message.text.split(maxsplit=1)[1]

    # Проверяем длину
    if len(broadcast_text) > 4000:
        await message.answer("❌ Сообщение слишком длинное (максимум 4000 символов)")
        return

    # Получаем пользователей
    users = db.get_all_users()
    if not users:
        await message.answer("❌ Нет пользователей для рассылки")
        return

    # Показываем предпросмотр
    preview_text = f"""📢 *ПОДТВЕРЖДЕНИЕ РАССЫЛКИ*

👥 Получателей: {len(users)}

📝 *Сообщение:*
━━━━━━━━━━━━━━━━━━━━
{broadcast_text[:200]}
{'...' if len(broadcast_text) > 200 else ''}
━━━━━━━━━━━━━━━━━━━━

✅ *Начать рассылку?*"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Да, начать", callback_data=f"quick_broadcast")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="to_admin_menu")]
    ])

    await message.answer(
        preview_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


@dp.callback_query(F.data == "quick_broadcast")
async def quick_broadcast_handler(callback: types.CallbackQuery):
    """Обработчик быстрой рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    # Получаем текст из предыдущего сообщения
    broadcast_text = callback.message.text.split("━━━━━━━━━━━━━━━━━━━━")[1].strip()

    # Создаем состояние и запускаем рассылку
    from aiogram.fsm.context import FSMContext
    state = FSMContext(storage, callback.from_user.id, callback.message.chat.id)
    await state.update_data(broadcast_text=broadcast_text)

    await admin_broadcast_send(callback, state)





@dp.callback_query(F.data.startswith("test_broadcast_"))
async def test_broadcast(callback: types.CallbackQuery):
    """Отправка тестового сообщения себе"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    try:
        # Получаем текст сообщения из кэша или состояния
        # Здесь нужно сохранять текст в состоянии или временном хранилище
        # Временное решение - попросить администратора ввести текст заново

        await callback.answer("⚠️ Для теста используйте полную рассылку через админ меню", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка тестовой рассылки: {e}")
        await callback.answer("❌ Ошибка тестовой отправки", show_alert=True)


@dp.callback_query(F.data.startswith("back_to_acc_"))
async def back_to_account(callback: types.CallbackQuery):
    """Вернуться к просмотру аккаунта"""
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    account_id = int(callback.data.replace("back_to_acc_", ""))

    # Ищем аккаунт по всем страницам
    found = False
    page = 0

    while not found:
        result = db.get_shop_accounts_paginated(page=page, per_page=1)

        if not result['accounts']:
            break

        for i, acc in enumerate(result['accounts']):
            if acc[0] == account_id:
                await show_account(callback, result['accounts'], i, result)
                found = True
                break

        if not found:
            page += 1
            # Ограничиваем поиск 10 страницами
            if page > 10:
                break

    if not found:
        await callback.answer("❌ Аккаунт не найден!", show_alert=True)

    await callback.answer()


def get_shop_accounts(self):
    """Получает все доступные аккаунты из магазина"""
    try:
        self.cursor.execute("""
            SELECT id, server, description, price, photo_file_id, created_at
            FROM accounts_shop 
            WHERE is_active = 1 AND sold_to = 0
            ORDER BY created_at DESC
        """)
        return self.cursor.fetchall()
    except Exception as e:
        logger.error(f"Ошибка получения аккаунтов из магазина: {e}")
        return []




@dp.callback_query(F.data.startswith("buy_account_confirm_"))
async def buy_account_confirm(callback: types.CallbackQuery, state: FSMContext):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    account_id = int(callback.data.replace("buy_account_confirm_", ""))
    account = db.get_account_by_id(account_id)

    if not account:
        await callback.answer("❌ Объявление не найдено!", show_alert=True)
        return

    acc_id, server, description, price, contacts, photo_file_id = account

    await state.update_data(
        order_type="buy_account",
        server=server,
        price=price,
        description=f"Покупка аккаунта #{acc_id}",
        account_id=acc_id
    )

    await callback.message.edit_text(
        f"🛍️ *ПОДТВЕРЖДЕНИЕ ПОКУПКИ*\n\n"
        f"📋 Детали аккаунта:\n"
        f"🆔 Объявление: #{acc_id}\n"
        f"🖥️ Сервер: {server}\n"
        f"💰 Сумма к оплате: {price}\n\n"
        f"{get_payment_details()}\n"
        f"Нажмите 'Купить' для оформления заказа:",
        parse_mode="Markdown",
        reply_markup=get_payment_keyboard("buy_account")
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("accounts_"))
async def accounts_pagination(callback: types.CallbackQuery):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    try:
        page = int(callback.data.replace("accounts_", ""))
        accounts = db.get_active_accounts()
        await callback.message.edit_reply_markup(
            reply_markup=get_accounts_keyboard(accounts, page=page)
        )
    except:
        pass
    await callback.answer()


@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ У вас нет доступа к этой команде!")
        return

    await message.answer(
        "👑 *АДМИН ПАНЕЛЬ*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=get_admin_menu()
    )


@dp.callback_query(F.data == "to_admin_menu")
async def to_admin_menu(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    await state.clear()

    try:
        await callback.message.edit_text(
            "👑 *АДМИН ПАНЕЛЬ*\n\n"
            "Выберите действие:",
            parse_mode="Markdown",
            reply_markup=get_admin_menu()
        )
    except:
        await callback.message.answer(
            "👑 *АДМИН ПАНЕЛЬ*\n\n"
            "Выберите действие:",
            parse_mode="Markdown",
            reply_markup=get_admin_menu()
        )

    await callback.answer()


class ShopAdminStates(StatesGroup):
    add_account_server = State()
    add_account_title = State()
    add_account_description = State()
    add_account_category = State()
    add_account_level = State()
    add_account_virts = State()
    add_account_bindings = State()
    add_account_price = State()
    add_account_photo = State()
    add_account_contacts = State()
    confirm_account_add = State()

    edit_account_select = State()
    edit_account_field = State()
    edit_account_value = State()



@dp.callback_query(F.data == "admin_referral_rewards")
async def admin_referral_rewards(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    pending_rewards = db.get_pending_referral_rewards()

    if not pending_rewards:
        await callback.message.edit_text(
            "💰 *НАГРАДЫ ЗА РЕФЕРАЛОВ*\n\n"
            "✅ Нет ожидающих наград\n",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu")]
            ])
        )
    else:
        keyboard = InlineKeyboardBuilder()
        for reward in pending_rewards[:10]:
            reward_id, user_id, username, full_name, amount, created_at = reward
            keyboard.row(
                InlineKeyboardButton(
                    text=f"💰 #{reward_id} - @{username or 'нет'} - {amount:,} ₽",
                    callback_data=f"admin_view_reward_{reward_id}"
                )
            )
        keyboard.row(InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu"))

        await callback.message.edit_text(
            f"💰 *НАГРАДЫ ЗА РЕФЕРАЛОВ*\n\n"
            f"🆕 Ожидающих выплат: {len(pending_rewards)}\n"
            f"💵 Общая сумма: {sum(r[4] for r in pending_rewards):,} ₽\n\n"
            f"Выберите награду для обработки:",
            parse_mode="Markdown",
            reply_markup=keyboard.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_view_reward_"))
async def admin_view_reward(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    try:
        reward_id = int(callback.data.replace("admin_view_reward_", ""))

        db.cursor.execute("""
            SELECT rr.id, rr.user_id, u.username, u.full_name, u.referral_count, 
                   rr.reward_amount, rr.status, rr.created_at
            FROM referral_rewards rr
            JOIN users u ON rr.user_id = u.user_id
            WHERE rr.id = ?
        """, (reward_id,))
        reward = db.cursor.fetchone()

        if not reward:
            await callback.answer("❌ Награда не найдена!", show_alert=True)
            return

        reward_id, user_id, username, full_name, referral_count, amount, status, created_at = reward

        # Получаем список рефералов
        db.cursor.execute(
            "SELECT user_id, username, full_name, reg_date FROM users WHERE referrer_id = ? ORDER BY reg_date",
            (user_id,)
        )
        referrals = db.cursor.fetchall()

        reward_text = f"""💰 *НАГРАДА ЗА РЕФЕРАЛОВ #{reward_id}*

👤 Пользователь: {full_name} (@{username or 'нет'})
🆔 ID: {user_id}
👥 Приглашено друзей: {referral_count}/{REFERRAL_THRESHOLD}
💵 Сумма награды: {amount:,} ₽
📅 Дата запроса: {created_at}
🔘 Статус: {status}

📋 *Список приглашенных ({len(referrals)}):*"""

        for i, ref in enumerate(referrals[:15], 1):
            ref_id, ref_username, ref_name, ref_date = ref
            reward_text += f"\n{i}. {ref_name} (@{ref_username or 'нет'}) - {ref_date}"

        if len(referrals) > 15:
            reward_text += f"\n... и еще {len(referrals) - 15} пользователей"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать пользователю", url=f"tg://user?id={user_id}")],
            [
                InlineKeyboardButton(text="✅ Выплатить", callback_data=f"admin_pay_reward_{reward_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_reward_{reward_id}")
            ],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_referral_rewards")]
        ])

        await callback.message.edit_text(
            reward_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка получения информации о награде: {e}")
        await callback.answer("❌ Ошибка получения информации", show_alert=True)
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_pay_reward_"))
async def admin_pay_reward(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    reward_id = int(callback.data.replace("admin_pay_reward_", ""))

    db.update_referral_reward_status(reward_id, 'paid')

    # Получаем информацию о награде для уведомления пользователя
    try:
        db.cursor.execute("SELECT user_id, reward_amount FROM referral_rewards WHERE id = ?", (reward_id,))
        result = db.cursor.fetchone()

        if result:
            user_id, amount = result

            # Уведомляем пользователя
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 *ПОЗДРАВЛЯЕМ!*\n\n"
                         f"Вы получили награду за приглашение друзей!\n\n"
                         f"💰 Сумма: {amount:,} ₽\n"
                         f"✅ Статус: Выплачено\n\n"
                         f"Спасибо за приглашение друзей в наш магазин!",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя: {e}")
    except Exception as e:
        logger.error(f"Ошибка получения информации о награде: {e}")

    await callback.answer("✅ Награда выплачена!", show_alert=True)
    await admin_referral_rewards(callback)


@dp.callback_query(F.data.startswith("admin_reject_reward_"))
async def admin_reject_reward(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    reward_id = int(callback.data.replace("admin_reject_reward_", ""))

    db.update_referral_reward_status(reward_id, 'rejected')

    await callback.answer("❌ Награда отклонена!", show_alert=True)
    await admin_referral_rewards(callback)


@dp.callback_query(F.data == "admin_manage_orders")
async def admin_manage_orders(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    try:
        # Удаляем старое сообщение и отправляем новое
        await callback.message.delete()

        # Получаем заказы
        new_orders = db.get_orders_by_status('new')
        all_orders = db.get_all_orders()

        if not new_orders or len(new_orders) == 0:
            text = "📦 *ЗАКАЗЫ*\n\n✅ Нет новых заказов\n\n📊 Всего заказов: 0"

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_manage_orders")],
                [InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu")]
            ])

            await callback.message.answer(
                text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        else:
            keyboard = InlineKeyboardBuilder()

            # Показываем все заказы
            for i, order in enumerate(new_orders[:15], 1):
                try:
                    order_id = order[0]  # id
                    username = order[2] or "нет"  # username
                    order_type = order[4] or "тип"  # order_type
                    price = order[7] or "0 ₽"  # price

                    # Укороченный текст кнопки
                    button_text = f"🆕 #{order_id}"
                    if username != "нет":
                        button_text += f" @{username[:10]}"
                    button_text += f" - {price}"

                    keyboard.row(
                        InlineKeyboardButton(
                            text=button_text,
                            callback_data=f"admin_view_order_{order_id}"
                        )
                    )
                except Exception as e:
                    logger.error(f"Ошибка обработки заказа: {e}")
                    continue

            # Кнопки навигации
            keyboard.row(InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_manage_orders"))
            keyboard.row(InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu"))

            await callback.message.answer(
                f"📦 *ЗАКАЗЫ*\n\n"
                f"🆕 Новых заказов: {len(new_orders)}\n"
                f"📊 Всего заказов: {len(all_orders) if all_orders else 0}\n\n"
                f"Выберите заказ для просмотра:",
                parse_mode="Markdown",
                reply_markup=keyboard.as_markup()
            )

    except Exception as e:
        logger.error(f"Ошибка в admin_manage_orders: {e}", exc_info=True)

        error_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Повторить", callback_data="admin_manage_orders")],
            [InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu")]
        ])

        await callback.message.answer(
            f"📦 *ЗАКАЗЫ*\n\n"
            f"❌ Ошибка при загрузке заказов\n"
            f"Ошибка: {str(e)}\n\n"
            f"Попробуйте еще раз:",
            parse_mode="Markdown",
            reply_markup=error_keyboard
        )

    await callback.answer()


@dp.callback_query(F.data.startswith("admin_view_order_"))
async def admin_view_order(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    order_id = int(callback.data.replace("admin_view_order_", ""))
    order = db.get_order_by_id(order_id)

    if not order:
        await callback.answer("❌ Заказ не найден!", show_alert=True)
        return

    status_icons = {
        'new': '🆕',
        'completed': '✅',
        'rejected': '❌'
    }

    status_icon = status_icons.get(order[11], '❓')

    order_text = f"""{status_icon} *ЗАКАЗ #{order[0]}*

👤 Пользователь: {order[3]} (@{order[2] or 'нет'})
🆔 ID: {order[1]}
📞 Контакты: {order[9]}

📋 Тип: {order[4]}
🖥️ Сервер: {order[5]}
📊 Количество: {order[6]}
💰 Сумма: {order[7]}

📝 Описание: {order[8]}
💳 Способ оплаты: {order[10]}
📄 Чек: {'✅ Есть' if order[12] else '❌ Нет'}

🕐 Создан: {order[14]}
🔘 Статус: {order[11]}"""

    keyboard_buttons = [
        [InlineKeyboardButton(text="💬 Связаться", url=f"tg://user?id={order[1]}")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_manage_orders")]
    ]

    if order[11] == 'new':
        keyboard_buttons.insert(1, [
            InlineKeyboardButton(text="✅ Выполнить", callback_data=f"admin_complete_order_{order[0]}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_order_{order[0]}")
        ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)

    await callback.message.edit_text(
        order_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_complete_order_"))
async def admin_complete_order(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    order_id = int(callback.data.replace("admin_complete_order_", ""))

    db.update_order_status(order_id, 'completed')

    # Уведомление пользователю
    try:
        order = db.get_order_by_id(order_id)
        if order:
            await bot.send_message(
                chat_id=order[1],
                text=f"✅ *Ваш заказ #{order_id} выполнен!*\n\n"
                     f"Благодарим за покупку! Если у вас есть вопросы, обращайтесь к администратору.",
                parse_mode="Markdown"
            )
    except Exception as e:
        logger.error(f"Ошибка отправки уведомления пользователю: {e}")

    await callback.answer("✅ Заказ выполнен!", show_alert=True)
    await admin_manage_orders(callback)


@dp.callback_query(F.data.startswith("admin_reject_order_"))
async def admin_reject_order(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    order_id = int(callback.data.replace("admin_reject_order_", ""))

    db.update_order_status(order_id, 'rejected')

    await callback.answer("❌ Заказ отклонен!", show_alert=True)
    await admin_manage_orders(callback)


@dp.callback_query(F.data == "admin_manage_requests")
async def admin_manage_requests(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    pending_requests = db.get_sell_requests('pending')

    if not pending_requests:
        await callback.message.edit_text(
            "📋 *ЗАЯВКИ НА ПРОДАЖУ*\n\n"
            "✅ Нет новых заявок\n",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu")]
            ])
        )
    else:
        keyboard = InlineKeyboardBuilder()
        for req in pending_requests[:10]:
            req_id = req[0]
            username = req[3] or "без юзернейма"
            server = req[5]
            price = req[7]
            keyboard.row(
                InlineKeyboardButton(
                    text=f"👤 @{username[:15]} - {server} - {price}",
                    callback_data=f"admin_view_request_{req_id}"
                )
            )
        keyboard.row(InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu"))

        await callback.message.edit_text(
            f"📋 *ЗАЯВКИ НА ПРОДАЖУ*\n\n"
            f"🆕 Новых заявок: {len(pending_requests)}\n\n"
            f"Выберите заявку:",
            parse_mode="Markdown",
            reply_markup=keyboard.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_view_request_"))
async def admin_view_request(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    request_id = int(callback.data.replace("admin_view_request_", ""))
    request = db.get_sell_request_by_id(request_id)

    if not request:
        await callback.answer("❌ Заявка не найдена!", show_alert=True)
        return

    req_id, user_id, username, full_name, server, description, price, contacts, photo_file_id, status, created_at = request

    request_text = f"""📋 *ЗАЯВКА НА ПРОДАЖУ #{req_id}*

👤 Пользователь: {full_name} (@{username or 'нет'})
🆔 ID: {user_id}
🖥️ Сервер: {server}
💰 Цена: {price}
📞 Контакты: {contacts}

📝 Описание:
{description}

🕐 Создана: {created_at}"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать продавцу", url=f"tg://user?id={user_id}")],
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"admin_accept_request_{req_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_request_{req_id}")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_manage_requests")]
    ])

    if photo_file_id:
        try:
            await bot.send_photo(
                chat_id=callback.from_user.id,
                photo=photo_file_id,
                caption=request_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            await callback.message.delete()
        except Exception as e:
            logger.error(f"Ошибка отправки фото: {e}")
            await callback.message.edit_text(
                request_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    else:
        await callback.message.edit_text(
            request_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    await callback.answer()


@dp.callback_query(F.data == "admin_shop_main")
async def admin_shop_main(callback: types.CallbackQuery):
    """Главное меню управления магазином аккаунтов"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    # Получаем статистику
    accounts = db.get_shop_accounts()
    sold_accounts = db.get_sold_shop_accounts()

    active_count = len(accounts) if accounts else 0
    sold_count = len(sold_accounts) if sold_accounts else 0

    # Формируем сообщение со статистикой
    stats_text = f"""
🛍️ *УПРАВЛЕНИЕ МАГАЗИНОМ АККАУНТОВ*

📊 *Статистика:*
• Активных аккаунтов: {active_count}
• Проданных аккаунтов: {sold_count}
• Всего в базе: {active_count + sold_count}

💡 *Действия:*
1️⃣ Добавить - добавить новый аккаунт в магазин
2️⃣ Активные - просмотр и редактирование
3️⃣ Проданные - история продаж
4️⃣ Очистить - удалить ВСЕ активные аккаунты

⚠️ *Внимание:* Очистка удалит все активные аккаунты без возможности восстановления!
"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить аккаунт в магазин", callback_data="admin_shop_add")],
        [InlineKeyboardButton(text="📋 Активные аккаунты", callback_data="admin_shop_list")],
        [InlineKeyboardButton(text="💰 Проданные аккаунты", callback_data="admin_shop_sold")],
        [InlineKeyboardButton(text="🗑️ ОЧИСТИТЬ ВСЕ АККАУНТЫ", callback_data="admin_clear_all_accounts")],
        [InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu")]
    ])

    await callback.message.edit_text(
        stats_text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query(F.data == "admin_shop_list")
async def admin_shop_list(callback: types.CallbackQuery):
    """Список активных аккаунтов в магазине"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    accounts = db.get_shop_accounts()  # Используем исправленную функцию

    if not accounts:
        await callback.message.edit_text(
            "📋 *АКТИВНЫЕ АККАУНТЫ В МАГАЗИНЕ*\n\n"
            "✅ Нет активных аккаунтов\n",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить аккаунт", callback_data="admin_shop_add")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_shop_main")]
            ])
        )
    else:
        keyboard = InlineKeyboardBuilder()
        for acc in accounts[:15]:
            try:
                acc_id = acc[0]
                server = acc[1] if len(acc) > 1 else "Не указан"
                title = acc[2] if len(acc) > 2 else "Без названия"
                price = acc[4] if len(acc) > 4 else "0"

                button_text = f"#{acc_id} - {server} - {price} ₽"
                if len(button_text) > 50:
                    button_text = button_text[:47] + "..."

                keyboard.row(
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"admin_shop_view_{acc_id}"
                    )
                )
            except Exception as e:
                logger.error(f"Ошибка обработки аккаунта: {e}")
                continue

        keyboard.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_shop_main"))

        await callback.message.edit_text(
            f"📋 *АКТИВНЫЕ АККАУНТЫ В МАГАЗИНЕ*\n\n"
            f"🛍️ Активных аккаунтов: {len(accounts)}\n\n"
            f"Выберите аккаунт для управления:",
            parse_mode="Markdown",
            reply_markup=keyboard.as_markup()
        )
    await callback.answer()


def clear_all_shop_accounts(self):
    """Удаляет ВСЕ активные аккаунты из магазина"""
    try:
        # Получаем количество аккаунтов до удаления
        self.cursor.execute("SELECT COUNT(*) FROM accounts_shop WHERE is_active = 1 AND sold_to = 0")
        count_before = self.cursor.fetchone()[0]

        # Удаляем все активные аккаунты
        self.cursor.execute("DELETE FROM accounts_shop WHERE is_active = 1 AND sold_to = 0")

        self.conn.commit()
        deleted_count = self.cursor.rowcount

        logger.info(f"✅ Удалено {deleted_count} аккаунтов из магазина (было {count_before})")

        return deleted_count
    except Exception as e:
        logger.error(f"❌ Ошибка удаления всех аккаунтов: {e}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        return 0


def delete_shop_account(self, account_id):
    """Удаляет конкретный аккаунт из магазина"""
    try:
        # Сначала проверяем, существует ли аккаунт
        self.cursor.execute("SELECT id FROM accounts_shop WHERE id = ?", (account_id,))
        account = self.cursor.fetchone()

        if not account:
            logger.error(f"❌ Аккаунт #{account_id} не найден для удаления")
            return False

        # Удаляем аккаунт
        self.cursor.execute("DELETE FROM accounts_shop WHERE id = ?", (account_id,))
        self.conn.commit()

        deleted = self.cursor.rowcount > 0

        if deleted:
            logger.info(f"✅ Аккаунт #{account_id} успешно удален из магазина")
        else:
            logger.error(f"❌ Не удалось удалить аккаунт #{account_id}")

        return deleted
    except Exception as e:
        logger.error(f"❌ Ошибка удаления аккаунта #{account_id}: {e}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        return False


def delete_account(self, account_id):
    """Удаляет аккаунт из старой таблицы (accounts_for_sale)"""
    try:
        self.cursor.execute("DELETE FROM accounts_for_sale WHERE id = ?", (account_id,))
        self.conn.commit()
        deleted = self.cursor.rowcount > 0

        if deleted:
            logger.info(f"✅ Объявление #{account_id} удалено из accounts_for_sale")
        else:
            logger.error(f"❌ Объявление #{account_id} не найдено в accounts_for_sale")

        return deleted
    except Exception as e:
        logger.error(f"❌ Ошибка удаления объявления #{account_id}: {e}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        return False


@dp.callback_query(F.data == "admin_clear_all_accounts")
async def admin_clear_all_accounts(callback: types.CallbackQuery):
    """Подтверждение удаления всех аккаунтов из магазина"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    # Получаем статистику перед удалением
    accounts = db.get_shop_accounts()
    active_count = len(accounts) if accounts else 0

    if active_count == 0:
        await callback.answer("✅ В магазине уже нет аккаунтов!", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить ВСЕ", callback_data="admin_clear_all_confirm"),
            InlineKeyboardButton(text="❌ Нет, отмена", callback_data="admin_shop_main")
        ]
    ])

    await callback.message.edit_text(
        f"⚠️ *ВНИМАНИЕ!*\n\n"
        f"Вы собираетесь удалить ВСЕ аккаунты из магазина!\n\n"
        f"📊 *Будет удалено:* {active_count} аккаунтов\n\n"
        f"🔥 *Это действие:*\n"
        f"• Удалит все активные аккаунты\n"
        f"• Нельзя будет восстановить\n"
        f"• Затронет только таблицу accounts_shop\n"
        f"• Не затронет проданные аккаунты\n\n"
        f"🛑 *Вы уверены?*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query(F.data == "admin_clear_all_confirm")
async def admin_clear_all_confirm(callback: types.CallbackQuery):
    """Удаление всех аккаунтов из магазина"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    try:
        # Показываем уведомление о начале процесса
        await callback.answer("⏳ Удаление аккаунтов...", show_alert=False)

        # Получаем количество аккаунтов до удаления
        accounts = db.get_shop_accounts()
        active_count = len(accounts) if accounts else 0

        if active_count == 0:
            await callback.answer("✅ В магазине уже нет аккаунтов!", show_alert=True)
            await admin_shop_main(callback)
            return

        # Удаляем аккаунты
        deleted_count = db.clear_all_shop_accounts()

        if deleted_count > 0:
            success_text = f"""
✅ *ВЫПОЛНЕНО!*

🗑️ Удалено аккаунтов: {deleted_count}
📦 Магазин аккаунтов очищен
🔄 Все аккаунты удалены из базы данных
"""
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="➕ Добавить новые аккаунты", callback_data="admin_shop_add")],
                [InlineKeyboardButton(text="◀️ В управление магазином", callback_data="admin_shop_main")]
            ])

            await callback.message.edit_text(
                success_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        else:
            await callback.answer("❌ Не удалось удалить аккаунты!", show_alert=True)
            await admin_shop_main(callback)

    except Exception as e:
        logger.error(f"Ошибка удаления всех аккаунтов: {e}")
        await callback.answer("❌ Произошла ошибка при удалении!", show_alert=True)
        await admin_shop_main(callback)

    await callback.answer()


async def show_account_details(callback: types.CallbackQuery, accounts, index):
    """Показывает аккаунт с навигацией влево/вправо"""
    try:
        if index < 0 or index >= len(accounts):
            await callback.answer("❌ Аккаунт не найден!", show_alert=True)
            return

        acc = accounts[index]

        # Проверяем структуру данных
        if len(acc) >= 12:
            acc_id, server, title, description, price, category, level, virt_amount, bindings, contacts, photo_file_id, created_at = acc[
                :12]

            # Форматируем дату
            if created_at:
                if isinstance(created_at, str):
                    created_date = created_at.split()[0]
                elif hasattr(created_at, 'strftime'):
                    created_date = created_at.strftime('%Y-%m-%d')
                else:
                    created_date = str(created_at)[:10]
            else:
                created_date = "Недавно"

            # Форматируем цену
            try:
                if isinstance(price, (int, float)):
                    price_num = int(price)
                    formatted_price = f"{price_num:,} ₽".replace(',', ' ')
                else:
                    # Извлекаем цифры из строки
                    price_clean = ''.join(filter(str.isdigit, str(price)))
                    price_num = int(price_clean) if price_clean else 0
                    formatted_price = f"{price_num:,} ₽".replace(',', ' ')
            except:
                formatted_price = str(price)

            # Формируем текст
            account_text = f"""🛍️ *АККАУНТ #{acc_id}*

📋 *Категория:* {category}
📊 *Уровень:* {level}
🖥️ *Сервер:* {server}
💰 *Цена:* {formatted_price}
📅 *Добавлен:* {created_date}

📝 *Описание:*
{description[:300]}{'...' if len(description) > 300 else ''}

🔗 *Привязки:* {bindings if bindings else 'Нет'}
💎 *Вирты:* {virt_amount if virt_amount else 'Не указано'}
📞 *Контакты:* {contacts if contacts else 'Не указаны'}"""

            # Создаем клавиатуру с навигацией
            keyboard = InlineKeyboardBuilder()

            # Кнопки навигации (влево/вправо)
            nav_buttons = []

            if index > 0:
                nav_buttons.append(InlineKeyboardButton(
                    text="◀️",
                    callback_data=f"nav_prev_{index - 1}"
                ))

            nav_buttons.append(InlineKeyboardButton(
                text=f"{index + 1}/{len(accounts)}",
                callback_data="no_action"
            ))

            if index < len(accounts) - 1:
                nav_buttons.append(InlineKeyboardButton(
                    text="▶️",
                    callback_data=f"nav_next_{index + 1}"
                ))

            keyboard.row(*nav_buttons)

            # Кнопка покупки
            keyboard.row(InlineKeyboardButton(
                text="💸 Купить этот аккаунт",
                callback_data=f"buy_acc_{acc_id}"
            ))

            # Кнопки меню
            keyboard.row(
                InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu"),
                InlineKeyboardButton(text="🔄 Обновить", callback_data="buy_account")
            )

            try:
                if photo_file_id:
                    await bot.send_photo(
                        chat_id=callback.from_user.id,
                        photo=photo_file_id,
                        caption=account_text,
                        parse_mode="Markdown",
                        reply_markup=keyboard.as_markup()
                    )
                    await callback.message.delete()
                else:
                    await callback.message.edit_text(
                        account_text,
                        parse_mode="Markdown",
                        reply_markup=keyboard.as_markup()
                    )
            except Exception as e:
                logger.error(f"Ошибка показа аккаунта: {e}")
                await callback.message.edit_text(
                    account_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard.as_markup()
                )
        else:
            logger.error(f"Неверная структура данных аккаунта: {len(acc)} полей")
            await callback.answer("❌ Ошибка данных аккаунта!", show_alert=True)

    except Exception as e:
        logger.error(f"Ошибка в show_account_details: {e}", exc_info=True)
        await callback.answer("❌ Ошибка загрузки аккаунта!", show_alert=True)


@dp.callback_query(F.data.startswith("nav_prev_"))
async def navigate_prev(callback: types.CallbackQuery):
    """Переход к предыдущему аккаунту"""
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    try:
        # Получаем индекс
        index = int(callback.data.replace("nav_prev_", ""))

        # Получаем все аккаунты
        accounts = db.get_shop_accounts_for_gallery()
        if not accounts:
            await callback.answer("❌ Нет доступных аккаунтов!", show_alert=True)
            return

        # Проверяем границы
        if index < 0:
            index = 0
        elif index >= len(accounts):
            index = len(accounts) - 1

        # Показываем аккаунт
        await show_account_details(callback, accounts, index)

    except Exception as e:
        logger.error(f"Ошибка навигации назад: {e}")
        await callback.answer("❌ Ошибка навигации!", show_alert=True)

    await callback.answer()


@dp.callback_query(F.data.startswith("nav_next_"))
async def navigate_next(callback: types.CallbackQuery):
    """Переход к следующему аккаунту"""
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    try:
        # Получаем индекс
        index = int(callback.data.replace("nav_next_", ""))

        # Получаем все аккаунты
        accounts = db.get_shop_accounts_for_gallery()
        if not accounts:
            await callback.answer("❌ Нет доступных аккаунтов!", show_alert=True)
            return

        # Проверяем границы
        if index < 0:
            index = 0
        elif index >= len(accounts):
            index = len(accounts) - 1

        # Показываем аккаунт
        await show_account_details(callback, accounts, index)

    except Exception as e:
        logger.error(f"Ошибка навигации вперед: {e}")
        await callback.answer("❌ Ошибка навигации!", show_alert=True)

    await callback.answer()









@dp.callback_query(F.data == "admin_clear_all_accounts")
async def admin_clear_all_accounts(callback: types.CallbackQuery):
    """Подтверждение удаления всех аккаунтов из магазина"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    # Получаем статистику перед удалением
    accounts = db.get_shop_accounts()
    active_count = len(accounts) if accounts else 0

    if active_count == 0:
        await callback.answer("✅ В магазине уже нет аккаунтов!", show_alert=True)
        await admin_shop_main(callback)
        return

    # Подробная информация об аккаунтах
    accounts_info = ""
    for i, acc in enumerate(accounts[:5], 1):
        try:
            acc_id = acc[0]
            server = acc[1] if len(acc) > 1 else "Без сервера"
            title = acc[2] if len(acc) > 2 else "Без названия"
            price = acc[4] if len(acc) > 4 else "0"

            # Форматируем цену
            try:
                if isinstance(price, (int, float)):
                    formatted_price = f"{int(price):,} ₽".replace(',', ' ')
                else:
                    formatted_price = str(price)
            except:
                formatted_price = str(price)

            accounts_info += f"{i}. #{acc_id} - {server} - {formatted_price}\n"
        except:
            continue

    if len(accounts) > 5:
        accounts_info += f"\n... и еще {len(accounts) - 5} аккаунтов"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить ВСЕ", callback_data="admin_clear_all_confirm"),
            InlineKeyboardButton(text="❌ Нет, отмена", callback_data="admin_shop_main")
        ]
    ])

    await callback.message.edit_text(
        f"⚠️ *ВНИМАНИЕ! КРИТИЧЕСКОЕ ДЕЙСТВИЕ!*\n\n"
        f"Вы собираетесь удалить ВСЕ аккаунты из магазина!\n\n"
        f"📊 *Будет удалено:* {active_count} аккаунтов\n\n"
        f"📋 *Примеры аккаунтов для удаления:*\n"
        f"{accounts_info}\n\n"
        f"🔥 *Это действие:*\n"
        f"• Удалит все активные аккаунты\n"
        f"• Нельзя будет восстановить\n"
        f"• Данные будут удалены из базы\n"
        f"• Затронет только таблицу accounts_shop\n"
        f"• Не затронет проданные аккаунты\n\n"
        f"🛑 *Вы уверены? Это действие нельзя отменить!*",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()





@dp.callback_query(F.data == "admin_shop_sold")
async def admin_shop_sold(callback: types.CallbackQuery):
    """Проданные аккаунты в магазине"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    sold_accounts = db.get_sold_shop_accounts()

    if not sold_accounts:
        await callback.message.edit_text(
            "💰 *ПРОДАННЫЕ АККАУНТЫ*\n\n"
            "📦 Проданных аккаунтов нет\n",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 Активные аккаунты", callback_data="admin_shop_list")],
                [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_shop_main")]
            ])
        )
    else:
        keyboard = InlineKeyboardBuilder()

        # Показываем проданные аккаунты
        sold_text = f"💰 *ПРОДАННЫЕ АККАУНТЫ*\n\n"
        sold_text += f"📦 Всего продано: {len(sold_accounts)}\n\n"

        for i, acc in enumerate(sold_accounts[:10], 1):
            try:
                acc_id = acc[0]
                server = acc[1] or "Без сервера"
                title = acc[2] or "Без названия"
                price = acc[3] or "0"
                sold_date = acc[5] or "Неизвестно"
                buyer_username = acc[6] or "нет"
                buyer_name = acc[7] or "Неизвестно"

                sold_text += f"{i}. #{acc_id} - {server} - {price} ₽\n"
                sold_text += f"   👤 {buyer_name} (@{buyer_username})\n"
                sold_text += f"   📅 {sold_date}\n\n"

                keyboard.row(
                    InlineKeyboardButton(
                        text=f"#{acc_id} - {server} - {price} ₽",
                        callback_data=f"admin_shop_view_sold_{acc_id}"
                    )
                )
            except Exception as e:
                logger.error(f"Ошибка обработки проданного аккаунта: {e}")
                continue

        if len(sold_accounts) > 10:
            sold_text += f"\n... и еще {len(sold_accounts) - 10} аккаунтов"

        keyboard.row(InlineKeyboardButton(text="◀️ Назад", callback_data="admin_shop_main"))

        await callback.message.edit_text(
            sold_text,
            parse_mode="Markdown",
            reply_markup=keyboard.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_shop_view_"))
async def admin_shop_view(callback: types.CallbackQuery):
    """Просмотр аккаунта в магазине"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    try:
        account_id = int(callback.data.replace("admin_shop_view_", ""))

        # Получаем аккаунт
        account = db.get_shop_account_by_id(account_id)

        if not account:
            await callback.answer("❌ Аккаунт не найден!", show_alert=True)
            return

        # Безопасно извлекаем данные
        try:
            acc_id = account[0]
            server = account[1] if len(account) > 1 else "Не указан"
            title = account[2] if len(account) > 2 else "Без названия"
            description = account[3] if len(account) > 3 else "Без описания"
            price = account[4] if len(account) > 4 else "0"
            category = account[5] if len(account) > 5 else "standart"
            level = account[6] if len(account) > 6 else 1
            virt_amount = account[7] if len(account) > 7 else ""
            bindings = account[8] if len(account) > 8 else ""
            contacts = account[9] if len(account) > 9 else ""
            photo_file_id = account[10] if len(account) > 10 else None
            created_at = account[11] if len(account) > 11 else ""
        except Exception as e:
            logger.error(f"Ошибка извлечения данных аккаунта: {e}")
            await callback.answer("❌ Ошибка данных аккаунта!", show_alert=True)
            return

        # Форматируем дату
        if created_at:
            if isinstance(created_at, str):
                created_date = created_at.split()[0]
            elif hasattr(created_at, 'strftime'):
                created_date = created_at.strftime('%Y-%m-%d')
            else:
                created_date = str(created_at)[:10]
        else:
            created_date = "Неизвестно"

        # Форматируем цену для отображения
        try:
            if isinstance(price, (int, float)):
                formatted_price = f"{int(price):,} ₽".replace(',', ' ')
            else:
                # Извлекаем цифры из строки
                price_clean = ''.join(filter(str.isdigit, str(price)))
                price_num = int(price_clean) if price_clean else 0
                formatted_price = f"{price_num:,} ₽".replace(',', ' ')
        except:
            formatted_price = str(price)

        account_text = f"""
🛍️ *АККАУНТ В МАГАЗИНЕ #{acc_id}*

🖥️ *Сервер:* {server}
💰 *Цена:* {formatted_price}
📅 *Добавлен:* {created_date}
📋 *Категория:* {category}
📊 *Уровень:* {level}

📝 *Заголовок:*
{title}

📝 *Описание:*
{description[:500]}{'...' if len(description) > 500 else ''}

🔗 *Привязки:* {bindings if bindings else 'Нет'}
💎 *Вирты:* {virt_amount if virt_amount else 'Не указано'}
📞 *Контакты:* {contacts if contacts else 'Не указаны'}
"""
        # Создаем клавиатуру с кнопками управления
        # В admin_shop_view измените клавиатуру на:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_shop_edit_{acc_id}"),
                InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"admin_shop_delete_{acc_id}")
            ],
            [InlineKeyboardButton(text="◀️ Назад к списку", callback_data="admin_shop_list")]
        ])

        try:
            if photo_file_id:
                # Отправляем фото с подписью
                await bot.send_photo(
                    chat_id=callback.from_user.id,
                    photo=photo_file_id,
                    caption=account_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                # Удаляем предыдущее сообщение
                await callback.message.delete()
            else:
                await callback.message.edit_text(
                    account_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
        except Exception as e:
            logger.error(f"Ошибка отправки сообщения: {e}")
            await callback.message.edit_text(
                account_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"Ошибка просмотра аккаунта: {e}")
        await callback.answer("❌ Ошибка загрузки аккаунта!", show_alert=True)
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_shop_delete_"))
async def admin_shop_delete_handler(callback: types.CallbackQuery):
    """Обработка удаления аккаунта из магазина"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    try:
        data = callback.data.replace("admin_shop_delete_", "")

        # Проверяем, если это подтверждение удаления (содержит "confirm_")
        if "confirm_" in data:
            account_id = int(data.replace("confirm_", ""))
            # Удаляем аккаунт
            if db.delete_shop_account(account_id):
                await callback.answer(f"✅ Аккаунт #{account_id} удален из магазина!", show_alert=True)

                # Возвращаемся к списку аккаунтов
                await admin_shop_list(callback)
            else:
                await callback.answer("❌ Ошибка удаления аккаунта!", show_alert=True)
        else:
            # Это запрос на подтверждение удаления - показываем подтверждение
            account_id = int(data)
            await admin_shop_view_for_delete(callback, account_id)

    except Exception as e:
        logger.error(f"Ошибка обработки удаления: {e}")
        await callback.answer("❌ Ошибка обработки!", show_alert=True)


async def admin_shop_view_for_delete(callback: types.CallbackQuery, account_id: int):
    """Показывает аккаунт с кнопкой подтверждения удаления"""
    # Получаем аккаунт
    account = db.get_shop_account_by_id(account_id)
    if not account:
        await callback.answer("❌ Аккаунт не найден!", show_alert=True)
        return

    # Безопасно извлекаем данные
    try:
        acc_id = account[0]
        server = account[1] if len(account) > 1 else "Не указан"
        title = account[2] if len(account) > 2 else "Без названия"
        description = account[3] if len(account) > 3 else "Без описания"
        price = account[4] if len(account) > 4 else "0"
        category = account[5] if len(account) > 5 else "standart"
        level = account[6] if len(account) > 6 else 1
        virt_amount = account[7] if len(account) > 7 else ""
        bindings = account[8] if len(account) > 8 else ""
        contacts = account[9] if len(account) > 9 else ""
        photo_file_id = account[10] if len(account) > 10 else None
        created_at = account[11] if len(account) > 11 else ""
    except Exception as e:
        logger.error(f"Ошибка извлечения данных аккаунта: {e}")
        await callback.answer("❌ Ошибка данных аккаунта!", show_alert=True)
        return

    # Форматируем дату
    if created_at:
        if isinstance(created_at, str):
            created_date = created_at.split()[0]
        elif hasattr(created_at, 'strftime'):
            created_date = created_at.strftime('%Y-%m-%d')
        else:
            created_date = str(created_at)[:10]
    else:
        created_date = "Неизвестно"

    # Форматируем цену для отображения
    try:
        if isinstance(price, (int, float)):
            formatted_price = f"{int(price):,} ₽".replace(',', ' ')
        else:
            # Извлекаем цифры из строки
            price_clean = ''.join(filter(str.isdigit, str(price)))
            price_num = int(price_clean) if price_clean else 0
            formatted_price = f"{price_num:,} ₽".replace(',', ' ')
    except:
        formatted_price = str(price)

    # Формируем текст сообщения
    account_text = f"""🗑️ *ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ АККАУНТА #{acc_id}*

🖥️ *Сервер:* {server}
💰 *Цена:* {formatted_price}
📅 *Добавлен:* {created_date}
📋 *Категория:* {category}
📊 *Уровень:* {level}

📝 *Заголовок:*
{title}

📝 *Описание:*
{description[:200]}{'...' if len(description) > 200 else ''}

🔗 *Привязки:* {bindings if bindings else 'Нет'}
💎 *Вирты:* {virt_amount if virt_amount else 'Не указано'}
📞 *Контакты:* {contacts if contacts else 'Не указаны'}
"""
    # Создаем клавиатуру с кнопками подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"admin_shop_delete_confirm_{acc_id}"),
            InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"admin_shop_view_{acc_id}")
        ],
        [InlineKeyboardButton(text="◀️ Назад к списку", callback_data="admin_shop_list")]
    ])

    try:
        if photo_file_id:
            # Отправляем фото с подписью
            await bot.send_photo(
                chat_id=callback.from_user.id,
                photo=photo_file_id,
                caption=account_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            # Удаляем предыдущее сообщение
            await callback.message.delete()
        else:
            await callback.message.edit_text(
                account_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Ошибка отправки сообщения: {e}")
        await callback.message.edit_text(
            account_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )


async def admin_shop_delete_confirm(callback: types.CallbackQuery, account_id: int):
    """Подтверждение удаления аккаунта"""
    try:
        # Удаляем аккаунт из базы данных
        if db.delete_shop_account(account_id):
            await callback.answer(f"✅ Аккаунт #{account_id} удален из магазина!", show_alert=True)

            # Уведомляем администраторов
            admin_text = f"""
🗑️ *АККАУНТ УДАЛЕН ИЗ МАГАЗИНА*

👤 Администратор: {callback.from_user.full_name}
🆔 ID: {callback.from_user.id}
📦 Аккаунт: #{account_id}
🕐 Время: {datetime.now().strftime('%H:%M:%S')}

Аккаунт полностью удален из магазина.
"""
            await notify_admins(admin_text)

            # Возвращаемся к списку аккаунтов
            await admin_shop_list(callback)
        else:
            await callback.answer("❌ Ошибка удаления аккаунта!", show_alert=True)
            await admin_shop_view(callback)

    except Exception as e:
        logger.error(f"Ошибка удаления аккаунта: {e}")
        await callback.answer("❌ Ошибка удаления аккаунта!", show_alert=True)
        await admin_shop_view(callback)





async def show_sold_account_details(callback: types.CallbackQuery, account):
    """Показывает детали проданного аккаунта"""
    try:
        # Распаковываем данные проданного аккаунта
        acc_id = account[0]
        server = account[1]
        title = account[2]
        description = account[3]
        price = account[4]
        category = account[5]
        level = account[6]
        sold_at = account[14] if len(account) > 14 else None
        buyer_username = account[15] if len(account) > 15 else "нет"
        buyer_name = account[16] if len(account) > 16 else "Неизвестно"

        # Форматируем дату продажи
        if sold_at:
            if isinstance(sold_at, str):
                sold_date = sold_at.split()[0]
            elif hasattr(sold_at, 'strftime'):
                sold_date = sold_at.strftime('%Y-%m-%d %H:%M')
            else:
                sold_date = str(sold_at)
        else:
            sold_date = "Неизвестно"

        account_text = f"""
💰 *ПРОДАННЫЙ АККАУНТ #{acc_id}*

🖥️ *Сервер:* {server}
💰 *Цена продажи:* {price:,} ₽
📅 *Дата продажи:* {sold_date}
👤 *Покупатель:* {buyer_name} (@{buyer_username})

📝 *Заголовок:*
{title}

📝 *Описание:*
{description[:200]}...
"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Связаться с покупателем",
                                  url=f"tg://user?id={account[13] if len(account) > 13 else ''}")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_shop_sold")]
        ])

        await callback.message.edit_text(
            account_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    except Exception as e:
        logger.error(f"Ошибка показа проданного аккаунта: {e}")
        await callback.answer("❌ Ошибка загрузки данных!", show_alert=True)


@dp.callback_query(F.data.startswith("admin_shop_edit_"))
async def admin_shop_edit(callback: types.CallbackQuery, state: FSMContext):
    """Начало редактирования аккаунта - выбор поля"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    account_id = int(callback.data.replace("admin_shop_edit_", ""))

    # Сохраняем ID аккаунта в состоянии
    await state.update_data(edit_account_id=account_id)
    await state.set_state(Form.edit_account_field)

    # Получаем информацию об аккаунте
    account = db.get_shop_account_by_id(account_id)
    if not account:
        await callback.answer("❌ Аккаунт не найден!", show_alert=True)
        return

    # Безопасно извлекаем данные
    title = account[2] if len(account) > 2 else "Без названия"
    price = account[4] if len(account) > 4 else "0"

    # Форматируем цену
    try:
        if isinstance(price, (int, float)):
            formatted_price = f"{int(price):,} ₽".replace(',', ' ')
        else:
            formatted_price = str(price)
    except:
        formatted_price = str(price)

    # Создаем клавиатуру для выбора поля
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Заголовок", callback_data=f"edit_field_title_{account_id}")],
        [InlineKeyboardButton(text="📋 Описание", callback_data=f"edit_field_description_{account_id}")],
        [InlineKeyboardButton(text="💰 Цена", callback_data=f"edit_field_price_{account_id}")],
        [InlineKeyboardButton(text="🖥️ Сервер", callback_data=f"edit_field_server_{account_id}")],
        [InlineKeyboardButton(text="📋 Категория", callback_data=f"edit_field_category_{account_id}")],
        [InlineKeyboardButton(text="📊 Уровень", callback_data=f"edit_field_level_{account_id}")],
        [InlineKeyboardButton(text="💎 Вирты", callback_data=f"edit_field_virts_{account_id}")],
        [InlineKeyboardButton(text="🔗 Привязки", callback_data=f"edit_field_bindings_{account_id}")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data=f"edit_field_contacts_{account_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_shop_view_{account_id}")]
    ])

    await callback.message.edit_text(
        f"✏️ *РЕДАКТИРОВАНИЕ АККАУНТА #{account_id}*\n\n"
        f"📝 Заголовок: {title[:50]}{'...' if len(title) > 50 else ''}\n"
        f"💰 Цена: {formatted_price}\n\n"
        f"Выберите поле для редактирования:",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("edit_field_"))
async def edit_field_selected(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора поля для редактирования"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    data = callback.data.replace("edit_field_", "")
    parts = data.split("_")

    if len(parts) < 2:
        await callback.answer("❌ Ошибка данных!", show_alert=True)
        return

    field = parts[0]
    account_id = int(parts[1])

    # Сохраняем выбранное поле и ID аккаунта в состоянии
    await state.update_data(
        edit_field=field,
        edit_account_id=account_id
    )
    await state.set_state(Form.edit_account_value)

    # Определяем подсказку в зависимости от поля
    prompts = {
        'title': "Введите новый заголовок (до 100 символов):",
        'description': "Введите новое описание:",
        'price': "Введите новую цену в рублях (только цифры):",
        'server': "Выберите новый сервер:",
        'category': "Введите новую категорию (standart, vip, premium):",
        'level': "Введите новый уровень (число):",
        'virts': "Введите количество виртов (например: 1.000.000 или 1kk):",
        'bindings': "Введите информацию о привязках:",
        'contacts': "Введите новые контакты:"
    }

    prompt = prompts.get(field, "Введите новое значение:")

    if field == 'server':
        # Для сервера показываем клавиатуру с серверами
        await callback.message.edit_text(
            f"✏️ *РЕДАКТИРОВАНИЕ СЕРВЕРА*\n\n"
            f"Выберите новый сервер для аккаунта #{account_id}:",
            parse_mode="Markdown",
            reply_markup=get_servers_keyboard(admin_mode=True, for_edit=True, account_id=account_id)
        )
    else:
        # Для других полей запрашиваем текст
        await callback.message.edit_text(
            f"✏️ *РЕДАКТИРОВАНИЕ {field.upper()}*\n\n"
            f"Аккаунт: #{account_id}\n"
            f"Поле: {field}\n\n"
            f"{prompt}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚫 Отмена", callback_data=f"admin_shop_edit_{account_id}")]
            ])
        )

    await callback.answer()


@dp.message(Form.edit_account_value)
async def process_edit_value(message: types.Message, state: FSMContext):
    """Обработка ввода нового значения для поля"""
    if not is_admin(message.from_user.id):
        return

    user_data = await state.get_data()
    field = user_data.get('edit_field')
    account_id = user_data.get('edit_account_id')

    if not field or not account_id:
        await message.answer("❌ Ошибка: данные не найдены", reply_markup=get_admin_menu())
        await state.clear()
        return

    value = message.text.strip()

    # Валидация в зависимости от поля
    if field == 'price':
        is_valid, price_num, error_msg = validate_price(value)
        if not is_valid:
            await message.answer(error_msg, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_shop_edit_{account_id}")]
            ]))
            return
        value = price_num

    elif field == 'level':
        if not value.isdigit():
            await message.answer("❌ Уровень должен быть числом!", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_shop_edit_{account_id}")]
            ]))
            return
        value = int(value)

    # Обновляем поле в базе данных с использованием нового метода
    try:
        if db.update_shop_account_field(account_id, field, value):
            await message.answer(
                f"✅ *Поле '{field}' обновлено!*\n\n"
                f"Аккаунт: #{account_id}\n"
                f"Новое значение: {value}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📋 К аккаунту", callback_data=f"admin_shop_view_{account_id}")],
                    [InlineKeyboardButton(text="🛍️ В магазин", callback_data="admin_shop_list")]
                ])
            )
        else:
            await message.answer(
                f"❌ Ошибка обновления поля '{field}'",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_shop_edit_{account_id}")]
                ])
            )

    except Exception as e:
        logger.error(f"Ошибка обновления поля {field}: {e}")
        await message.answer(
            f"❌ Ошибка обновления поля '{field}'\nОшибка: {str(e)}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_shop_edit_{account_id}")]
            ])
        )

    await state.clear()


async def send_admin_notification_for_account_order(order_id, account_id, user_id, username, full_name, server, price,
                                                    account_title):
    """Отправляет уведомление администраторам о покупке аккаунта"""
    try:
        logger.info(f"📢 Отправка уведомления о заказе #{order_id} на аккаунт #{account_id}")

        notification_text = f"""🆕 *НОВЫЙ ЗАКАЗ НА АККАУНТ #{order_id}*

📦 *Детали аккаунта:*
• ID аккаунта: #{account_id}
• Сервер: {server}
• Название: {account_title[:50]}{'...' if len(account_title) > 50 else ''}
• Цена: {price}

👤 *Покупатель:*
• Имя: {full_name}
• Юзернейм: @{username or 'нет'}
• ID: {user_id}

📅 *Время заказа:* {datetime.now().strftime('%H:%M:%S %d.%m.%Y')}
⚠️ *Статус:* Ожидает оплаты
ℹ️ *Примечание:* Аккаунт НЕ помечен как проданный до подтверждения оплаты администратором!"""

        # Получаем детали аккаунта для более полной информации
        try:
            account = db.get_shop_account_by_id(account_id)
            if account and len(account) > 3:
                description = account[3] if len(account) > 3 else "Без описания"
                notification_text += f"\n\n📝 *Описание аккаунта:*\n{description[:200]}..."
        except Exception as e:
            logger.error(f"Ошибка получения деталей аккаунта: {e}")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Подтвердить оплату",
                                     callback_data=f"admin_confirm_account_payment_{order_id}_{account_id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject_order_{order_id}")
            ],
            [
                InlineKeyboardButton(text="💬 Связаться с покупателем", url=f"tg://user?id={user_id}"),
                InlineKeyboardButton(text="📋 К заказам", callback_data="admin_manage_orders")
            ],
            [InlineKeyboardButton(text="🛍️ Посмотреть аккаунт", callback_data=f"admin_shop_view_{account_id}")]
        ])

        # Отправляем всем администраторам
        sent_count = 0
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=notification_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                sent_count += 1
                logger.info(f"✅ Уведомление отправлено администратору {admin_id}")

                # Небольшая задержка между отправками
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"❌ Ошибка отправки уведомления администратору {admin_id}: {e}")
                continue

        logger.info(f"📢 Уведомления отправлены {sent_count}/{len(ADMIN_IDS)} администраторам")

        # Дополнительно логируем в консоль для отладки
        print(f"\n{'=' * 60}")
        print(f"📢 НОВЫЙ ЗАКАЗ НА АККАУНТ!")
        print(f"🆔 Заказ: #{order_id}")
        print(f"📦 Аккаунт: #{account_id}")
        print(f"👤 Покупатель: {full_name} (@{username})")
        print(f"💰 Цена: {price}")
        print(f"📅 Время: {datetime.now().strftime('%H:%M:%S')}")
        print(f"✅ Уведомления отправлены {sent_count} админам")
        print(f"{'=' * 60}\n")

        return sent_count > 0

    except Exception as e:
        logger.error(f"❌ Критическая ошибка отправки уведомления администраторам: {e}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        return False










@dp.callback_query(F.data == "admin_shop_add")
async def admin_shop_add(callback: types.CallbackQuery, state: FSMContext):
    """Начало добавления аккаунта в магазин"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    # Устанавливаем флаг, что это для магазина
    await state.update_data(is_shop=True)
    await state.set_state(Form.admin_add_account_server)

    await callback.message.edit_text(
        "🛍️ *ДОБАВЛЕНИЕ АККАУНТА В МАГАЗИН*\n\n"
        "Этот аккаунт появится в разделе '🛍️ Купить аккаунт'\n\n"
        "1️⃣ *Выберите сервер:*",
        parse_mode="Markdown",
        reply_markup=get_servers_keyboard(admin_mode=True)
    )
    await callback.answer()



@dp.callback_query(F.data.startswith("admin_accept_request_"))
async def admin_accept_request(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    request_id = int(callback.data.replace("admin_accept_request_", ""))
    request = db.get_sell_request_by_id(request_id)

    if not request:
        await callback.answer("❌ Заявка не найдена!", show_alert=True)
        return

    # Извлекаем данные из заявки
    req_id, user_id, username, full_name, server, description, price, contacts, photo_file_id, status, created_at = request

    # Добавляем в таблицу accounts_for_sale (публичные объявления)
    account_id = db.add_account_for_sale(
        server=server,
        description=description,
        price=price,
        contacts=contacts,
        photo_file_id=photo_file_id
    )

    if account_id:
        # Обновляем статус заявки
        db.update_sell_request_status(request_id, 'accepted')

        # Уведомляем пользователей о новом объявлении
        asyncio.create_task(notify_about_new_account(account_id, server, price, description))

        await callback.answer("✅ Заявка принята и опубликована!", show_alert=True)

        # Уведомляем пользователя
        try:
            await bot.send_message(
                chat_id=user_id,
                text=f"🎉 *ВАША ЗАЯВКА ПРИНЯТА!*\n\n"
                     f"Ваш аккаунт опубликован в разделе '🛍️ Купить аккаунт'.\n\n"
                     f"📋 Детали:\n"
                     f"• Объявление: #{account_id}\n"
                     f"• Сервер: {server}\n"
                     f"• Цена: {price}\n\n"
                     f"✅ Теперь все игроки могут видеть ваше объявление!",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    else:
        await callback.answer("❌ Ошибка публикации объявления!", show_alert=True)

    await admin_manage_requests(callback)


async def notify_about_new_account(account_id, server, price, description):
    """Уведомляет активных пользователей о новом аккаунте"""
    try:
        # Получаем всех пользователей (ограничиваем чтобы не спамить)
        users = db.get_all_users()

        # Берем только последних 1000 активных пользователей
        recent_users = users[:1000] if len(users) > 1000 else users

        notification_text = f"""🆕 *НОВЫЙ АККАУНТ В ПРОДАЖЕ!*

🆔 Объявление: #{account_id}
🖥️ Сервер: {server}
💰 Цена: {price}

📝 Краткое описание:
{description[:200]}{'...' if len(description) > 200 else ''}

🏃‍♂️ Успейте купить первым!
Нажмите '🛍️ Купить аккаунт' для просмотра."""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛍️ Смотреть аккаунт", callback_data=f"view_account_{account_id}")],
            [InlineKeyboardButton(text="🏃‍♂️ Купить сейчас", callback_data="buy_account")]
        ])

        # Отправляем ограниченному числу пользователей
        sent_count = 0
        for user in recent_users[:200]:  # Отправляем максимум 200 уведомлений
            try:
                user_id = user[0]
                await bot.send_message(
                    chat_id=user_id,
                    text=notification_text,
                    parse_mode="Markdown",
                    reply_markup=keyboard
                )
                sent_count += 1
                await asyncio.sleep(0.05)  # Задержка чтобы не спамить
            except Exception:
                continue

        logger.info(f"✅ Уведомление о новом аккаунте #{account_id} отправлено {sent_count} пользователям")

    except Exception as e:
        logger.error(f"Ошибка отправки уведомлений: {e}")



@dp.callback_query(F.data.startswith("admin_reject_request_"))
async def admin_reject_request(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    request_id = int(callback.data.replace("admin_reject_request_", ""))

    db.update_sell_request_status(request_id, 'rejected')

    await callback.answer("❌ Заявка отклонена!", show_alert=True)
    await admin_manage_requests(callback)


@dp.callback_query(F.data == "admin_add_account")
async def admin_add_account_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    await state.set_state(Form.admin_add_account_server)
    await callback.message.edit_text(
        "➕ *ДОБАВЛЕНИЕ ОБЪЯВЛЕНИЯ*\n\n"
        "Выберите сервер:",
        parse_mode="Markdown",
        reply_markup=get_servers_keyboard(admin_mode=True)
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("admin_server_"))
async def admin_server_selected(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    server = callback.data.replace("admin_server_", "")
    await state.update_data(server=server)
    await state.set_state(Form.admin_add_account_description)

    await callback.message.edit_text(
        f"➕ *ДОБАВЛЕНИЕ ОБЪЯВЛЕНИЯ*\n\n"
        f"Сервер: *{server}*\n\n"
        f"Опишите аккаунт:\n"
        f"• Уровень \n• Привязки\n• Имущество\n• Цена в описании тоже\n• Другие характеристики\n\n"
        f"Пример:\n"
        f"Уровень: 50\n"
        f"Виртов: 10.000.000\n"
        f"Привязка: есть\n"
        f"Имущество: 3 дома, 5 машин",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@dp.message(Form.admin_add_account_description)
async def admin_process_desc(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    description = message.text.strip()
    if not description:
        await message.answer("❌ Описание не может быть пустым!", reply_markup=get_cancel_keyboard())
        return

    await state.update_data(description=description)
    await state.set_state(Form.admin_add_account_photo)

    await message.answer(
        f"➕ *ДОБАВЛЕНИЕ ОБЪЯВЛЕНИЯ*\n\n"
        f"✅ Описание сохранено\n\n"
        f"Теперь отправьте фото аккаунта (скриншот):\n\n"
        f"📷 *Важно:*\n"
        f"• Фото должно быть четким\n"
        f"• На фото должно быть видно данные аккаунта\n"
        f"• Можно отправить несколько фото поочередно\n\n"
        f"Или нажмите 'Пропустить фото':",
        reply_markup=get_photo_keyboard()
    )


@dp.callback_query(F.data == "send_photo")
async def send_photo_prompt(callback: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    if not current_state:
        return

    await callback.message.edit_text(
        "📷 Отправьте фото аккаунта (скриншот):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚫 Отмена", callback_data="cancel")]
        ])
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("back_to_order_"))
async def back_to_order(callback: types.CallbackQuery):
    """Вернуться к заказу"""
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    try:
        order_id = int(callback.data.replace("back_to_order_", ""))

        await callback.message.edit_text(
            f"📋 *Ваш заказ*\n\n"
            f"🆔 Номер заказа: #{order_id}\n\n"
            f"{get_payment_details()}\n"
            f"После оплаты нажмите '📄 Отправить чек'",
            parse_mode="Markdown",
            reply_markup=get_receipt_keyboard(order_id)
        )
    except Exception as e:
        logger.error(f"Ошибка возврата к заказу: {e}")
        await callback.answer("❌ Ошибка загрузки заказа!", show_alert=True)

    await callback.answer()





@dp.callback_query(F.data == "skip_photo")
async def skip_photo(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(photo_file_id=None)
    await state.set_state(Form.admin_add_account_price)

    await callback.message.edit_text(
        f"➕ *ДОБАВЛЕНИЕ ОБЪЯВЛЕНИЯ*\n\n"
        f"✅ Фото пропущено\n\n"
        f"Введите цену в рублях:\n\n"
        f"💰 *Примеры:*\n"
        f"• 1000\n"
        f"• 2500\n"
        f"• 5000\n"
        f"• 10000",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@dp.message(Form.admin_add_account_photo, F.photo)
async def handle_photo_for_admin_account(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_file_id)
    await state.set_state(Form.admin_add_account_price)

    await message.answer(
        f"➕ *ДОБАВЛЕНИЕ ОБЪЯВЛЕНИЯ*\n\n"
        f"✅ Фото сохранено\n\n"
        f"Введите цену в рублях:\n\n"
        f"💰 *Примеры:*\n"
        f"• 1000\n"
        f"• 2500\n"
        f"• 5000\n"
        f"• 10000",
        reply_markup=get_cancel_keyboard()
    )


@dp.message(Form.admin_add_account_price)
async def admin_process_price(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    price_text = message.text.strip()
    is_valid, price_num, error_msg = validate_price(price_text)

    if not is_valid:
        await message.answer(error_msg, reply_markup=get_cancel_keyboard())
        return

    await state.update_data(price=f"{price_num:,} ₽".replace(',', ' '))
    await state.set_state(Form.admin_add_account_contacts)

    await message.answer(
        f"➕ *ДОБАВЛЕНИЕ ОБЪЯВЛЕНИЯ*\n\n"
        f"✅ Цена сохранена: {price_num:,} ₽\n\n"
        f"Введите контакты для связи:\n\n"
        f"📞 *Примеры:*\n"
        f"• @username\n"
        f"• +79991234567\n"
        f"• t.me/username",
        reply_markup=get_cancel_keyboard()
    )


@dp.message(Form.admin_add_account_contacts)
async def admin_process_contacts(message: types.Message, state: FSMContext):
    logger.info(f"admin_process_contacts вызван! Сообщение: '{message.text}'")

    if not is_admin(message.from_user.id):
        await message.answer("❌ Нет доступа!")
        return

    contacts = message.text.strip()
    if not contacts:
        await message.answer("❌ Контакты не могут быть пустыми!", reply_markup=get_cancel_keyboard())
        return

    logger.info(f"Контакты после очистки: '{contacts}'")

    user_data = await state.get_data()
    logger.info(f"Данные из состояния: {user_data}")

    # Проверяем, что все необходимые данные есть
    if not user_data:
        await message.answer("❌ Ошибка: данные не найдены. Начните заново.", reply_markup=get_admin_menu())
        await state.clear()
        return

    is_from_shop = user_data.get('is_shop', False)
    logger.info(f"is_from_shop: {is_from_shop}")

    if is_from_shop:
        # Добавляем в магазин (таблица accounts_shop)
        price_str = user_data.get('price', '0')

        # Проверяем, что цена есть
        if not price_str:
            await message.answer("❌ Ошибка: цена не найдена. Начните заново.", reply_markup=get_admin_menu())
            await state.clear()
            return

        # Извлекаем число из строки цены
        price_clean = ''.join(filter(str.isdigit, price_str))
        if not price_clean:
            price_clean = '0'
        price = int(price_clean)

        # Создаем заголовок из описания
        description = user_data.get('description', '')
        title = description[:30] + ('...' if len(description) > 30 else '')

        account_id = db.add_account_to_shop(
            server=user_data.get('server', 'Не указан'),
            title=title,  # ПЕРЕДАВАЙТЕ ТАКЖЕ TITLE!
            description=description,
            price=price,
            contacts=contacts,
            category='standart',
            level=1,
            virt_amount='',
            bindings='',
            photo_file_id=user_data.get('photo_file_id')
        )

        if account_id:
            await message.answer(
                f"✅ *АККАУНТ ДОБАВЛЕН В МАГАЗИН!*\n\n"
                f"🆔 ID: #{account_id}\n"
                f"🖥️ Сервер: {user_data.get('server', 'Не указан')}\n"
                f"💰 Цена: {price:,} ₽\n"
                f"📞 Контакты: {contacts}\n\n"
                f"📊 Теперь аккаунт доступен в разделе '🛍️ Купить аккаунт'.",
                parse_mode="Markdown",
                reply_markup=get_admin_menu()
            )

            # Уведомление другим админам
            try:
                admin_text = f"""
🆕 *НОВЫЙ АККАУНТ В МАГАЗИНЕ #{account_id}*

👤 Добавил: {message.from_user.full_name}
🖥️ Сервер: {user_data.get('server', 'Не указан')}
💰 Цена: {price:,} ₽
📞 Контакты: {contacts}

📝 Описание:
{description[:100]}...
"""
                await notify_admins(admin_text)
            except Exception as e:
                logger.error(f"Ошибка уведомления админов: {e}")
        else:
            await message.answer(
                "❌ Ошибка добавления аккаунта в магазин!\n"
                "Проверьте logs для подробностей.",
                reply_markup=get_admin_menu()
            )
    else:
        # Старая система - добавляем в accounts_for_sale
        account_id = db.add_account_for_sale(
            server=user_data.get('server', 'Не указан'),
            description=user_data.get('description', ''),
            price=user_data.get('price', '0 ₽'),
            contacts=contacts,
            photo_file_id=user_data.get('photo_file_id')
        )

        if account_id:
            await message.answer(
                f"✅ *ОБЪЯВЛЕНИЕ #{account_id} ДОБАВЛЕНО*\n\n"
                f"📋 *Детали объявления:*\n"
                f"🖥️ Сервер: {user_data.get('server', 'Не указан')}\n"
                f"💰 Цена: {user_data.get('price', '0 ₽')}\n"
                f"📞 Контакты: {contacts}\n\n"
                f"✅ *Объявление теперь доступно в разделе '🛍️ Купить аккаунт'*",
                parse_mode="Markdown",
                reply_markup=get_admin_menu()
            )
        else:
            await message.answer(
                "❌ Ошибка добавления объявления! Попробуйте еще раз.",
                reply_markup=get_admin_menu()
            )

    await state.clear()


def delete_shop_account(self, account_id):
    """Удаляет аккаунт из магазина"""
    try:
        # Удаляем аккаунт из таблицы accounts_shop
        self.cursor.execute("DELETE FROM accounts_shop WHERE id = ?", (account_id,))
        self.conn.commit()

        deleted = self.cursor.rowcount > 0

        if deleted:
            logger.info(f"✅ Аккаунт #{account_id} успешно удален из магазина")
        else:
            logger.error(f"❌ Не удалось удалить аккаунт #{account_id}")

        return deleted
    except Exception as e:
        logger.error(f"❌ Ошибка удаления аккаунта #{account_id}: {e}")
        import traceback
        logger.error(f"Трассировка: {traceback.format_exc()}")
        return False



@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    try:
        # Сначала получаем статистику
        stats = db.get_statistics()

        # Проверяем, что статистика получена
        if stats is None:
            logger.error("Статистика вернула None")
            stats_text = "📊 *СТАТИСТИКА БОТА*\n\n❌ Ошибка: не удалось получить данные статистики"
        else:
            # Формируем текст статистики с безопасными проверками
            stats_text = f"""📊 *СТАТИСТИКА БОТА*

👥 *Пользователи:*
• Всего пользователей: {stats.get('total_users', 0)}
• Подписавшихся на канал: {stats.get('subscribed_users', 0)}
• С рефералами: {stats.get('users_with_referrals', 0)}
• Всего рефералов: {stats.get('total_referrals', 0)}

📦 *Заказы:*
• Всего заказов: {stats.get('total_orders', 0)}
• Новых заказов: {stats.get('new_orders', 0)}
• Выполненных: {stats.get('completed_orders', 0)}
• Отклоненных: {stats.get('rejected_orders', 0)}
• Общая выручка: {stats.get('total_revenue', 0):,} ₽

🛍️ *Объявления:*
• Активных объявлений: {stats.get('active_accounts', 0)}

📋 *Заявки:*
• Ожидающих заявок: {stats.get('pending_requests', 0)}

💰 *Реферальные награды:*
• Ожидающих выплат: {stats.get('pending_rewards_count', 0)}
• Сумма выплат: {stats.get('pending_rewards_amount', 0):,} ₽"""

    except Exception as e:
        logger.error(f"Критическая ошибка в admin_stats: {e}", exc_info=True)
        stats_text = f"📊 *СТАТИСТИКА БОТА*\n\n❌ Критическая ошибка получения статистики"

    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_stats")],
        [InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu")]
    ])

    # Отправляем сообщение
    try:
        await callback.message.edit_text(
            stats_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения: {e}")
        # Если не удалось отредактировать, отправляем новое
        await callback.message.answer(
            stats_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

    await callback.answer()


@dp.callback_query(F.data == "admin_all_users")
async def admin_all_users(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    users = db.get_all_users()

    if not users:
        await callback.message.edit_text(
            "👥 *ПОЛЬЗОВАТЕЛИ*\n\n"
            "❌ *Нет пользователей*\n\n"
            "В базе данных пока нет пользователей.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu")]
            ])
        )
    else:
        users_text = f"👥 *ВСЕ ПОЛЬЗОВАТЕЛИ*\n\nВсего пользователей: {len(users)}\n\n"

        for i, user in enumerate(users[:15], 1):
            user_id, username, full_name, reg_date, referral_count = user
            reg_date_str = reg_date[:10] if isinstance(reg_date, str) else reg_date.strftime('%Y-%m-%d') if hasattr(
                reg_date, 'strftime') else str(reg_date)

            users_text += f"{i}. {full_name} (@{username or 'нет'}) - ID: {user_id}"
            if referral_count and referral_count > 0:
                users_text += f" 👥{referral_count}"
            users_text += f"\n   📅 {reg_date_str}\n"

        if len(users) > 15:
            users_text += f"\n... и еще {len(users) - 15} пользователей"

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu")]
        ])

        await callback.message.edit_text(
            users_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    await callback.answer()


@dp.callback_query(F.data == "admin_manage_accounts")
async def admin_manage_accounts(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    accounts = db.get_active_accounts()

    if not accounts:
        await callback.message.edit_text(
            "🗑️ *УПРАВЛЕНИЕ ОБЪЯВЛЕНИЯМИ*\n\n"
            "✅ Нет активных объявлений\n",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu")]
            ])
        )
    else:
        keyboard = InlineKeyboardBuilder()
        for acc in accounts[:10]:
            # Проверяем структуру данных
            if acc and len(acc) >= 6:
                acc_id, server, description, price, contacts, photo_file_id = acc
                keyboard.row(
                    InlineKeyboardButton(
                        text=f"#{acc_id} - {server} - {price}",
                        callback_data=f"view_account_{acc_id}"
                    )
                )
        keyboard.row(InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu"))

        await callback.message.edit_text(
            f"🗑️ *УПРАВЛЕНИЕ ОБЪЯВЛЕНИЯМИ*\n\n"
            f"Активных объявлений: {len(accounts)}\n\n"
            f"Выберите объявление для просмотра или удаления:",
            parse_mode="Markdown",
            reply_markup=keyboard.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data == "cancel")
async def cancel_handler(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.clear()

        user = callback.from_user

        if is_admin(user.id):
            keyboard = get_main_menu_for_admin()
            text = "🛒 *Shop Kornycod*\n\nВыберите раздел:"
        else:
            keyboard = get_main_menu()
            text = "🛒 *Shop Kornycod*\n\nВыберите раздел:"

        try:
            await callback.message.edit_text(
                text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except:
            await callback.message.answer(
                text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"Ошибка в cancel_handler: {e}")
        try:
            await callback.message.answer(
                "🛒 *Shop Kornycod*\n\nВыберите раздел:",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
        except:
            pass

    await callback.answer()

@dp.callback_query(F.data.startswith("view_account_"))
async def view_account_details(callback: types.CallbackQuery, state: FSMContext):
    if not await check_access(callback):
        await callback.answer("❌ Сначала подпишитесь на канал!", show_alert=True)
        return

    account_id = int(callback.data.replace("view_account_", ""))
    account = db.get_account_by_id(account_id)

    if not account:
        await callback.answer("❌ Объявление не найдено!", show_alert=True)
        return

    acc_id, server, description, price, contacts, photo_file_id = account

    account_text = f"""
🛍️ *ПРОСМОТР АККАУНТА*

🆔 Номер: #{acc_id}
🖥️ Сервер: {server}
💰 Цена: {price}
📞 Контакты продавца: {contacts}

📝 Описание:
{description}"""

    # Разные клавиатуры для админов и обычных пользователей
    if is_admin(callback.from_user.id):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💸 Купить этот аккаунт", callback_data=f"buy_account_confirm_{acc_id}")],
            [InlineKeyboardButton(text="🗑️ Удалить объявление", callback_data=f"admin_delete_account_{acc_id}")],
            [InlineKeyboardButton(text="◀️ Назад к списку", callback_data="buy_account")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu")]
        ])
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💸 Купить этот аккаунт", callback_data=f"buy_account_confirm_{acc_id}")],
            [InlineKeyboardButton(text="◀️ Назад к списку", callback_data="buy_account")],
            [InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu")]
        ])

    if photo_file_id:
        try:
            await bot.send_photo(
                chat_id=callback.from_user.id,
                photo=photo_file_id,
                caption=account_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            await callback.message.delete()
        except Exception as e:
            logger.error(f"Ошибка отправки фото: {e}")
            await callback.message.edit_text(
                account_text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    else:
        await callback.message.edit_text(
            account_text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    await callback.answer()


@dp.callback_query(F.data.startswith("edit_servers_"))
async def edit_servers_pagination(callback: types.CallbackQuery):
    """Пагинация серверов при редактировании"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    try:
        # Формат: edit_servers_страница_accountid
        data = callback.data.replace("edit_servers_", "")
        parts = data.split("_")

        if len(parts) < 2:
            await callback.answer("❌ Ошибка данных!", show_alert=True)
            return

        page = int(parts[0])
        account_id = int(parts[1])

        await callback.message.edit_reply_markup(
            reply_markup=get_servers_keyboard(
                page=page,
                admin_mode=True,
                for_edit=True,
                account_id=account_id
            )
        )
    except Exception as e:
        logger.error(f"Ошибка пагинации при редактировании: {e}")
        await callback.answer("❌ Ошибка!", show_alert=True)

    await callback.answer()



@dp.callback_query(F.data.startswith("admin_delete_account_"))
async def admin_delete_account(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    account_id = int(callback.data.replace("admin_delete_account_", ""))

    # Подтверждение удаления
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"admin_delete_confirm_{account_id}"),
            InlineKeyboardButton(text="❌ Нет, отмена", callback_data=f"view_account_{account_id}")
        ]
    ])

    await callback.message.edit_text(
        f"🗑️ *УДАЛЕНИЕ ОБЪЯВЛЕНИЯ #{account_id}*\n\n"
        f"Вы уверены, что хотите удалить это объявление?\n"
        f"Это действие нельзя отменить!",
        parse_mode="Markdown",
        reply_markup=keyboard
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("admin_delete_confirm_"))
async def admin_delete_confirm(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    account_id = int(callback.data.replace("admin_delete_confirm_", ""))

    success = db.delete_account(account_id)  # Из accounts_for_sale

    if success:
        await callback.message.edit_text(
            f"✅ *Объявление #{account_id} удалено!*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 К объявлениям", callback_data="buy_account")],
                [InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu")]
            ])
        )

        # Уведомляем администраторов
        admin_text = f"""
🗑️ *ОБЪЯВЛЕНИЕ УДАЛЕНО*

👤 Администратор: {callback.from_user.full_name}
🆔 ID: {callback.from_user.id}
📦 Объявление: #{account_id}
🕐 Время: {datetime.now().strftime('%H:%M:%S')}

Объявление удалено из старой системы.
"""
        await notify_admins(admin_text)
    else:
        await callback.message.edit_text(
            f"❌ *Ошибка удаления объявления #{account_id}*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data=f"view_account_{account_id}")],
                [InlineKeyboardButton(text="🏠 В меню", callback_data="to_menu")]
            ])
        )
    await callback.answer()


@dp.callback_query(F.data == "admin_manage_accounts")
async def admin_manage_accounts(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Нет доступа!", show_alert=True)
        return

    accounts = db.get_active_accounts()

    if not accounts:
        await callback.message.edit_text(
            "🗑️ *УПРАВЛЕНИЕ ОБЪЯВЛЕНИЯМИ*\n\n"
            "✅ Нет активных объявлений\n",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu")]
            ])
        )
    else:
        keyboard = InlineKeyboardBuilder()
        for acc in accounts[:10]:
            if acc and len(acc) >= 6:
                acc_id, server, description, price, contacts, photo_file_id = acc
                button_text = f"#{acc_id} - {server} - {price}"
                if len(button_text) > 50:
                    button_text = button_text[:47] + "..."

                keyboard.row(
                    InlineKeyboardButton(
                        text=button_text,
                        callback_data=f"view_account_{acc_id}"
                    )
                )

        # Кнопки навигации если много объявлений
        if len(accounts) > 10:
            keyboard.row(
                InlineKeyboardButton(text="▶️ Показать еще", callback_data="admin_manage_accounts_page_1")
            )

        keyboard.row(InlineKeyboardButton(text="◀️ В админ меню", callback_data="to_admin_menu"))

        await callback.message.edit_text(
            f"🗑️ *УПРАВЛЕНИЕ ОБЪЯВЛЕНИЯМИ*\n\n"
            f"Активных объявлений: {len(accounts)}\n\n"
            f"Выберите объявление для просмотра или удаления:",
            parse_mode="Markdown",
            reply_markup=keyboard.as_markup()
        )
    await callback.answer()


@dp.callback_query(F.data == "to_menu")
async def to_menu(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.clear()

        user = callback.from_user

        if is_admin(user.id):
            # Админам показываем меню с кнопкой в админку
            keyboard = get_main_menu_for_admin()
            text = "🛒 *Shop Kornycod*\n\nВыберите раздел:"
        else:
            keyboard = get_main_menu()
            text = "🛒 *Shop Kornycod*\n\nВыберите раздел:"

        try:
            await callback.message.edit_text(
                text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except:
            await callback.message.answer(
                text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"Ошибка в to_menu: {e}")
        try:
            await callback.message.answer(
                "🛒 *Shop Kornycod*\n\nВыберите раздел:",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
        except:
            pass

    await callback.answer()




@dp.message()
async def handle_unknown(message: types.Message, state: FSMContext):
    if not await check_access(message):
        await message.answer(
            f"⚠️ *Доступ ограничен!*\n\n"
            f"Для использования бота необходимо подпишитесь на наш канал:\n"
            f"{CHANNEL_LINK}\n\n"
            f"После подписки нажмите '✅ Проверить подписку'",
            parse_mode="Markdown",
            reply_markup=get_subscription_keyboard()
        )
        return

    current_state = await state.get_state()

    if current_state:
        await message.answer(
            "❌ Пожалуйста, следуйте инструкциям выше или нажмите 'Отмена'",
            reply_markup=get_cancel_keyboard()
        )
    else:
        if is_admin(message.from_user.id):
            await message.answer(
                "👑 *АДМИН ПАНЕЛЬ*\n\n"
                "Выберите действие:",
                parse_mode="Markdown",
                reply_markup=get_admin_menu()
            )
        else:
            await message.answer(
                "🛒 *Shop Kornycod*\n\n"
                "Выберите раздел:",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )

def get_main_menu_for_admin():
    """Главное меню для админов (с кнопкой в админку)"""
    keyboard = InlineKeyboardBuilder()
    keyboard.row(
        InlineKeyboardButton(text="💎 Продать вирты", callback_data="sell_currency"),
        InlineKeyboardButton(text="🛒 Купить вирты", callback_data="buy_currency")
    )
    keyboard.row(
        InlineKeyboardButton(text="👤 Продать аккаунт", callback_data="sell_account"),
        InlineKeyboardButton(text="🛍️ Купить аккаунт", callback_data="buy_account")
    )
    keyboard.row(
        InlineKeyboardButton(text="⚡ Купить софт", callback_data="buy_software")
    )
    keyboard.row(
        InlineKeyboardButton(text="👥 Реферальная система", callback_data="referral_system")
    )
    keyboard.row(InlineKeyboardButton(text="👑 Админ панель", callback_data="to_admin_menu"))  # Кнопка для админов
    return keyboard.as_markup()


@dp.callback_query(F.data == "to_shop_menu")
async def to_shop_menu(callback: types.CallbackQuery, state: FSMContext):
    try:
        await state.clear()

        user = callback.from_user

        if is_admin(user.id):
            keyboard = get_main_menu_for_admin()
            text = "🛒 *Shop Kornycod*\n\nДобро пожаловать в магазин!\nВыберите раздел:"
        else:
            keyboard = get_main_menu()
            text = "🛒 *Shop Kornycod*\n\nДобро пожаловать в магазин!\nВыберите раздел:"

        try:
            await callback.message.edit_text(
                text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
        except:
            await callback.message.answer(
                text,
                parse_mode="Markdown",
                reply_markup=keyboard
            )

    except Exception as e:
        logger.error(f"Ошибка в to_shop_menu: {e}")
        try:
            await callback.message.answer(
                "🛒 *Shop Kornycod*\n\nЧто вас интересует?",
                reply_markup=get_main_menu()
            )
        except:
            pass

    await callback.answer()


async def main():
    logger.info("🛒 Shop Kornycod запускается...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())


