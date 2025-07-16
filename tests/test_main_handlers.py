import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, ANY

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import user_to_manager, manager_to_user
from states import Form

@pytest.mark.asyncio
async def test_user_to_manager_no_fsm_state():
    """
    Проверяет, что сообщение от пользователя без FSM-состояния
    корректно пересылается менеджеру.
    """
    # --- Mocks ---
    message = MagicMock()
    message.from_user = MagicMock(id=123, first_name='Test')
    message.text = "Hello manager"

    state = AsyncMock()
    state.get_state.return_value = None  # Пользователь не в FSM

    user_session = MagicMock()
    notification_service = MagicMock(manager_chat_id=999)
    message_map = MagicMock()

    bot = AsyncMock()
    sent_message = MagicMock(message_id=555)
    bot.send_message.return_value = sent_message

    # --- Call ---
    # Модифицируем main.py, чтобы передавать зависимости в хендлеры
    # В данном тесте мы передаем их напрямую
    await user_to_manager(
        message, state, bot, notification_service, user_session, message_map
    )

    # --- Assertions ---
    bot.send_message.assert_awaited_once_with(
        notification_service.manager_chat_id,
        ANY
    )
    user_session.set_active_user.assert_called_once_with(123)
    message_map.add.assert_called_once_with(555, 123)

@pytest.mark.asyncio
async def test_user_to_manager_with_fsm_state():
    """
    Проверяет, что сообщение от пользователя в FSM-состоянии
    игнорируется и не пересылается менеджеру.
    """
    # --- Mocks ---
    message = MagicMock()
    state = AsyncMock()
    state.get_state.return_value = Form.waiting_for_houses  # Пользователь в FSM

    bot = AsyncMock()
    # ... другие моки не должны быть вызваны
    notification_service = MagicMock()
    user_session = MagicMock()
    message_map = MagicMock()

    # --- Call ---
    await user_to_manager(
        message, state, bot, notification_service, user_session, message_map
    )

    # --- Assertions ---
    bot.send_message.assert_not_awaited()
    user_session.set_active_user.assert_not_called()
    message_map.add.assert_not_called()

@pytest.mark.asyncio
async def test_manager_to_user_reply():
    """
    Проверяет, что ответ менеджера (reply) корректно
    отправляется нужному пользователю.
    """
    # --- Mocks ---
    message = MagicMock()
    message.text = "Here is your answer"
    message.reply_to_message = MagicMock(message_id=555)
    message.answer = AsyncMock()

    message_map = MagicMock()
    message_map.get_user.return_value = 123  # Находим ID пользователя

    bot = AsyncMock()

    # --- Call ---
    await manager_to_user(message, bot, message_map, MagicMock())

    # --- Assertions ---
    message_map.get_user.assert_called_once_with(555)
    bot.send_message.assert_awaited_once_with(123, "Менеджер: Here is your answer")
    message.answer.assert_not_awaited() # Не должно быть сообщений об ошибке

@pytest.mark.asyncio
async def test_manager_to_user_direct_message():
    """
    Проверяет, что прямое сообщение менеджера (не reply)
    отправляется последнему активному пользователю.
    """
    # --- Mocks ---
    message = MagicMock()
    message.text = "A general message"
    message.reply_to_message = None  # Это не reply
    message.answer = AsyncMock()

    user_session = MagicMock()
    user_session.get_active_user.return_value = 123 # Есть активный пользователь

    bot = AsyncMock()

    # --- Call ---
    await manager_to_user(message, bot, MagicMock(), user_session)

    # --- Assertions ---
    user_session.get_active_user.assert_called_once()
    bot.send_message.assert_awaited_once_with(123, "Менеджер: A general message")
    message.answer.assert_not_awaited()
