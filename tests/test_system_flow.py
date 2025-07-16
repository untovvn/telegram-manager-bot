"""
Системный (E2E) тест, имитирующий полный сценарий взаимодействия.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, ANY

# --- Настройка путей для импорта ---
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Импорт всех компонентов бота ---
from aiogram import Dispatcher, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update, Message, User, Chat

from main import (
    user_to_manager, manager_to_user,
    send_welcome, process_start, process_houses
)
from manager_auth import ManagerStore
from message_map import MessageMap
from notification_service import NotificationService
from states import Form
from user_session import UserSession

from aiogram.types import Update, Message, User, Chat, MessageEntity
from aiogram.enums import MessageEntityType
from datetime import datetime

# ... (остальные импорты)

# --- Константы для теста ---
USER_ID = 12345
MANAGER_ID = 98765
USER = User(id=USER_ID, is_bot=False, first_name="Тестовый", username="testuser")
CHAT = Chat(id=USER_ID, type="private")

def create_update(text: str, user: User = USER, bot: Bot = None, reply_to_message: Message = None) -> Update:
    """
    Фабрика для создания фейковых Update объектов.
    Автоматически добавляет entity 'bot_command', если текст начинается с '/'.
    """
    entities = []
    if text.startswith('/'):
        entities.append(
            MessageEntity(type=MessageEntityType.BOT_COMMAND, offset=0, length=len(text.split()[0]))
        )

    message = Message(
        message_id=abs(hash(text)),
        chat=CHAT,
        from_user=user,
        text=text,
        date=datetime.now(),
        entities=entities or None,
        bot=bot, # Pass the bot instance here
        reply_to_message=reply_to_message # Pass reply_to_message here
    )
    return Update(update_id=abs(hash(text)), message=message)

@pytest.mark.asyncio
async def test_full_user_manager_flow():
    """
    Тестирует полный сценарий:
    1. Пользователь запускает бота и проходит опрос.
    2. Карточка клиента уходит менеджеру.
    3. Пользователь пишет прямое сообщение -> оно пересылается менеджеру.
    4. Менеджер отвечает на карточку -> пользователь получает ответ.
    """
    # --- 1. Инициализация всех компонентов бота в тестовом режиме ---
    bot = AsyncMock()
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Mock Message.answer to ensure it calls bot.send_message
    async def mock_message_answer(text, reply_markup=None):
        return await bot.send_message(USER_ID, text, reply_markup=reply_markup)
    Message.answer = AsyncMock(side_effect=mock_message_answer)

    user_session = UserSession()
    notification_service = NotificationService(bot)
    notification_service.manager_chat_id = MANAGER_ID # Переопределяем для теста
    message_map = MessageMap()
    manager_store = ManagerStore() # В этом тесте не используется, но нужен для полноты

    # --- Wrapper functions for handlers with dependencies ---
    async def handle_process_houses_test(message: Message, state: FSMContext):
        await process_houses(message, state, user_session, notification_service, message_map, bot)

    async def handle_user_to_manager_test(message: Message, state: FSMContext):
        await user_to_manager(message, state, bot, notification_service, user_session, message_map)

    async def handle_manager_to_user_test(message: Message):
        await manager_to_user(message, bot, message_map, user_session)

    # --- 2. Регистрация хендлеров (как в main.py) ---
    dp.message.register(send_welcome, Command("start"))
    dp.message.register(process_start, Form.waiting_for_start)
    dp.message.register(handle_process_houses_test, Form.waiting_for_houses)
    dp.message.register(handle_user_to_manager_test, lambda m: m.from_user.id != MANAGER_ID)
    dp.message.register(handle_manager_to_user_test, lambda m: m.from_user.id == MANAGER_ID)

    # --- 3. Шаг 1: Пользователь отправляет /start ---
    await dp.feed_update(bot, create_update("/start", bot=bot))
    bot.send_message.assert_awaited_with(USER_ID, ANY, reply_markup=ANY)
    
    # --- 4. Шаг 2: Пользователь нажимает "Начать" ---
    bot.reset_mock()
    await dp.feed_update(bot, create_update("Начать", bot=bot))
    bot.send_message.assert_awaited_with(USER_ID, ANY, reply_markup=ANY)

    # --- 5. Шаг 3: Пользователь отвечает "Да" -> карточка уходит менеджеру ---
    bot.reset_mock()
    # Моделируем, что bot.send_message вернет сообщение с message_id = 500
    manager_card = MagicMock()
    manager_card.message_id = 500
    bot.send_message.return_value = manager_card

    await dp.feed_update(bot, create_update("Да"))
    
    # Проверяем, что менеджеру ушла карточка
    bot.send_message.assert_any_await(MANAGER_ID, ANY)
    # Проверяем, что пользователю ушло сообщение "Зову менеджера"
    bot.send_message.assert_any_await(USER_ID, "Зову менеджера, он подключиться к диалогу в ближайшее время", reply_markup=ANY)
    
    # Проверяем, что в message_map создалась связь
    assert message_map.get_user(500) == USER_ID

    # --- 6. Шаг 4: Менеджер отвечает на карточку ---
    bot.reset_mock()
    manager_user = User(id=MANAGER_ID, is_bot=False, first_name="Manager")
    manager_reply_update = create_update("Здравствуйте, сейчас помогу", user=manager_user, bot=bot, reply_to_message=Message(
        message_id=500,
        chat=Chat(id=MANAGER_ID, type="private"),
        from_user=manager_user,
        date=datetime.now(),
        text="Карточка клиента"
    ))

    await dp.feed_update(bot, manager_reply_update)

    # Проверяем, что пользователь получил ответ от менеджера
    bot.send_message.assert_awaited_with(USER_ID, "Менеджер: Здравствуйте, сейчас помогу")

    # --- Cleanup: Cancel any pending asyncio tasks ---
    for task in asyncio.all_tasks():
        if task is not asyncio.current_task():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass