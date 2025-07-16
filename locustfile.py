"""
Нагрузочный тест с использованием Locust.

Этот тест не будет подключаться к Telegram, а будет напрямую "атаковать"
внутреннюю логику бота (диспетчер), чтобы измерить, как быстро
он может обрабатывать входящие сообщения.
"""
import asyncio
from locust import User, task, constant

# --- Настройка для импорта компонентов бота ---
from aiogram import Dispatcher, Bot
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update, Message, User as AiogramUser, Chat

# Импортируем всю логику так же, как в системном тесте
from main import user_to_manager, manager_to_user, send_welcome, process_start, process_houses
from manager_auth import ManagerStore
from message_map import MessageMap
from notification_service import NotificationService
from states import Form
from user_session import UserSession

# --- Глобальная настройка компонентов бота ---
# Мы инициализируем их один раз, чтобы не делать это для каждого пользователя.

bot_mock = Bot(token="fake-token-for-locust")
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

user_session = UserSession()
notification_service = NotificationService(bot_mock)
message_map = MessageMap()
manager_store = ManagerStore()

# --- Регистрация хендлеров ---
dp.message.register(send_welcome, commands=["start"])
dp.message.register(process_start, Form.waiting_for_start)
dp.message.register(
    lambda msg, state: process_houses(msg, state, user_session, notification_service, message_map, bot_mock),
    Form.waiting_for_houses
)
# ... можно зарегистрировать и остальные для более полного теста

def create_locust_update(text: str, user_id: int) -> Update:
    """Создает фейковый Update для Locust."""
    user = AiogramUser(id=user_id, is_bot=False, first_name=f"LocustUser{user_id}")
    chat = Chat(id=user_id, type="private")
    message = Message(message_id=abs(hash(text)), chat=chat, from_user=user, text=text)
    return Update(update_id=abs(hash(text)), message=message)

class BotUser(User):
    """
    Класс, представляющий одного виртуального пользов��теля (locust).
    """
    wait_time = constant(1)  # Пауза 1 секунда между выполнением задач

    def __init__(self, environment):
        super().__init__(environment)
        self.user_id = self.environment.runner.user_count # Уникальный ID для каждого пользователя

    @task
    def run_fsm_flow(self):
        """
        Основная задача: эмулировать прохождение FSM-сценария.
        """
        async def _run():
            # Создаем фейковые сообщения
            start_update = create_locust_update("/start", self.user_id)
            nachat_update = create_locust_update("Начать", self.user_id)
            da_update = create_locust_update("Да", self.user_id)

            # Прогоняем их через диспетчер
            await dp.feed_update(bot_mock, start_update)
            await dp.feed_update(bot_mock, nachat_update)
            await dp.feed_update(bot_mock, da_update)

        # Запускаем асинхронный сценарий
        asyncio.run(_run())
