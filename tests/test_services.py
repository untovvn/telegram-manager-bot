import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from notification_service import NotificationService, build_manager_message
from message_map import MessageMap

@pytest.mark.asyncio
async def test_notify_manager_sends_message():
    """
    Проверяет, что сервис уведомлений корректно вызывает
    метод send_message у бота с правильными аргументами.
    """
    mock_bot = AsyncMock()
    manager_id = 123456789
    
    service = NotificationService(mock_bot)
    service.manager_chat_id = manager_id # Принудительно устанавливаем ID для теста
    
    user = MagicMock()
    user.username = "testuser"
    user.first_name = "Test"
    user.id = 42

    result = await service.notify_manager(user)

    # Проверяем, что метод был вызван один раз
    mock_bot.send_message.assert_awaited_once()
    # Получаем аргументы, с которыми он был вызван
    args, kwargs = mock_bot.send_message.await_args
    
    # Проверяем, что сообщение отправлено правильному менеджеру
    assert args[0] == manager_id
    # Проверяем, что текст сообщения содержит нужную информацию
    assert "@testuser" in args[1]
    assert "Test" in args[1]
    assert "42" in args[1]
    # Проверяем, что метод вернул True в случае успеха
    assert result is True

def test_message_map_functionality():
    """
    Проверяет базовые операции (добавление, получение, удаление)
    в классе MessageMap.
    """
    m = MessageMap()
    m.add(100, 200)
    assert m.get_user(100) == 200
    m.clear(100)
    assert m.get_user(100) is None

def test_build_manager_message():
    """
    Проверяет, что карточка клиента генерируется
    с правильной информацией и форматом.
    """
    user = MagicMock()
    user.username = "ClientName"
    user.first_name = "Имя"
    user.id = 123
    
    msg = build_manager_message(user)
    
    assert "Username: @ClientName" in msg
    assert "Имя: Имя" in msg
    assert "ID: 123" in msg
    assert msg.startswith("❗ Новый клиент:")
    assert 'функцию "Ответ"' in msg

def test_build_manager_message_no_username():
    """
    Проверяет, что карточка клиента корректно генерируется,
    даже если у пользователя нет username.
    """
    user = MagicMock()
    user.username = None
    user.first_name = "Лариса"
    user.id = 7754893189
    
    msg = build_manager_message(user)
    
    assert "Username: не указан" in msg
    assert "Имя: Лариса" in msg
    assert "ID: 7754893189" in msg

