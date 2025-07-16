import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock, ANY

# Добавляем путь к корневой папке проекта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fsm_handlers import process_houses
from states import Form

@pytest.mark.asyncio
async def test_process_houses_sends_card_and_clears_state():
    """
    Тест проверяет, что `process_houses`:
    1. Отправляет карточку клиента менеджеру, если она еще не была отправлена.
    2. Добавляет ID сообщения в `message_map`.
    3. Обновляет состояние FSM, помечая, что карточка отправлена.
    4. Корректно вызывает `stop_chain_and_call_manager`, который сбрасывает состояние.
    5. Устанавливает активного пользователя.
    """
    # --- Mocks ---
    message = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = 12345
    message.answer = AsyncMock()

    state = AsyncMock()
    state.get_data.return_value = {}  # Карточка еще не отправлена

    user_session = MagicMock()
    notification_service = MagicMock()
    notification_service.manager_chat_id = 98765

    message_map = MagicMock()

    # Мок для объекта бота и его метода send_message
    bot = AsyncMock()
    sent_message = MagicMock()
    sent_message.message_id = 54321
    bot.send_message.return_value = sent_message

    # --- Call ---
    await process_houses(
        message=message,
        state=state,
        user_session=user_session,
        notification_service=notification_service,
        message_map=message_map,
        bot=bot
    )

    # --- Assertions ---
    # 1. Проверяем отправку карточки
    bot.send_message.assert_awaited_once_with(
        notification_service.manager_chat_id,
        ANY  # Проверяем, что какой-то текст был отправлен
    )

    # 2. Проверяем добавление в message_map
    message_map.add.assert_called_once_with(sent_message.message_id, message.from_user.id)

    # 3. Проверяем обновление данных состояния
    state.update_data.assert_awaited_once_with(card_sent=True)

    # 4. Проверяем, что состояние было очищено (через вызов stop_chain_and_call_manager)
    state.clear.assert_awaited_once()

    # 5. Проверяем, что пользователю отправили сообщение о вызове менеджера
    message.answer.assert_awaited_once_with(
        "Зову менеджера, он подключиться к диалогу в ближайшее время",
        reply_markup=ANY
    )

    # 6. Проверяем, что активный пользователь был установлен
    user_session.set_active_user.assert_called_once_with(message.from_user.id)

@pytest.mark.asyncio
async def test_process_houses_card_already_sent():
    """
    Тест проверяет, что `process_houses` не отправляет карточку повторно,
    если она уже была отправлена.
    """
    # --- Mocks ---
    message = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = 12345
    message.answer = AsyncMock()

    state = AsyncMock()
    # Устанавливаем, что карточка уже отправлена
    state.get_data.return_value = {"card_sent": True}

    user_session = MagicMock()
    notification_service = MagicMock()
    message_map = MagicMock()
    bot = AsyncMock()

    # --- Call ---
    await process_houses(
        message=message,
        state=state,
        user_session=user_session,
        notification_service=notification_service,
        message_map=message_map,
        bot=bot
    )

    # --- Assertions ---
    # Убеждаемся, что send_message не вызывался
    bot.send_message.assert_not_awaited()
    message_map.add.assert_not_called()
    state.update_data.assert_not_awaited()

    # Но состояние все равно должно быть очищено, и пользователь уведомлен
    state.clear.assert_awaited_once()
    message.answer.assert_awaited_once_with(
        "Зову менеджера, он подключиться к диалогу в ближайшее время",
        reply_markup=ANY
    )
    user_session.set_active_user.assert_called_once_with(message.from_user.id)
