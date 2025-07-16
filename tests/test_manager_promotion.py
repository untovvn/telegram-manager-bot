import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from unittest.mock import AsyncMock, MagicMock
from manager_auth import ManagerStore, check_manager_command

@pytest.mark.asyncio
async def test_manager_access_granted(monkeypatch):
    # Мокаем список ID менеджеров
    monkeypatch.setenv("MANAGER_IDS", "12345,67890")
    store = ManagerStore()
    user_id = 12345
    message = MagicMock()
    message.from_user.id = user_id
    message.text = "/manager"
    message.answer = AsyncMock()

    result = await check_manager_command(message, store)
    assert result is True
    assert store.is_manager(user_id)
    message.answer.assert_awaited_with("Вы успешно стали менеджером!")

@pytest.mark.asyncio
async def test_manager_access_denied(monkeypatch):
    monkeypatch.setenv("MANAGER_IDS", "12345,67890")
    store = ManagerStore()
    user_id = 55555
    message = MagicMock()
    message.from_user.id = user_id
    message.text = "/manager"
    message.answer = AsyncMock()

    result = await check_manager_command(message, store)
    assert result is False
    assert not store.is_manager(user_id)
    message.answer.assert_awaited_with("У вас нет доступа к режиму менеджера.") 