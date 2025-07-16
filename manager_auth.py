"""
Модуль для аутентификации и авторизации менеджеров.
"""
import os
from aiogram.types import Message
from dotenv import load_dotenv

# Загружаем переменные окружения при старте модуля
load_dotenv()


def get_manager_ids() -> set[int]:
    """
    Читает переменную окружения MANAGER_IDS, парсит ее
    и возвращает множество (set) с ID менеджеров.
    """
    ids_str = os.getenv("MANAGER_IDS", "")
    if not ids_str:
        return set()
    
    ids = set()
    for i in ids_str.split(","):
        if i.strip().isdigit():
            ids.add(int(i.strip()))
    return ids


class ManagerStore:
    """
    Класс для хранения и проверки ID авторизованных менеджеров.
    """
    def __init__(self):
        """
        Инициализирует хранилище, загружая ID менеджеров из .env файла.
        """
        self._managers = get_manager_ids()

    def is_manager(self, user_id: int) -> bool:
        """
        Проверяет, является ли пользователь с данным ID менеджером.
        """
        return user_id in self._managers


async def check_manager_command(message: Message, store: ManagerStore) -> bool:
    """
    Обрабатывает команду /manager.

    Проверяет, есть ли ID пользователя в списке менеджеров,
    и отправляет соответствующий ответ.
    """
    if message.from_user and store.is_manager(message.from_user.id):
        await message.answer("Вы успешно стали менеджером!")
        return True
    else:
        await message.answer("У вас нет доступа к режиму менеджера.")
        return False 