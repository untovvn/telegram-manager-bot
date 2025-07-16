
"""
Сервис для отправки уведомлений менеджеру.

Этот модуль содержит класс `NotificationService`, который инкапсулирует
логику отправки сообщений в чат с менеджером.
"""
import logging
import os
from aiogram import Bot
from aiogram.types import User
from dotenv import load_dotenv

# Загружаем ID чата менеджера из переменных окружения
load_dotenv()
MANAGER_CHAT_ID = int(os.getenv("MANAGER_CHAT_ID", "0"))


def build_manager_message(user: User) -> str:
    """
    Создаетформатированный текст ("карточку клиента") для отправки м��неджеру.
    """
    username = f"@{user.username}" if user.username else "не указан"
    return (
        f"❗ Новый клиент:\n"
        f"Username: {username}\n"
        f"Имя: {user.first_name}\n"
        f"ID: {user.id}\n\n"
        f'Чтобы ответить клиенту, используйте функцию "Ответ" на это сообщение.'
    )


class NotificationService:
    """
    Класс, отвечающий за отправку уведомлений менеджеру.
    """
    def __init__(self, bot: Bot):
        """
        Инициализирует сервис.

        :param bot: Экземпляр aiogram.Bot для отправки сообщений.
        """
        self.bot = bot
        self.manager_chat_id = MANAGER_CHAT_ID

    async def notify_manager(self, user: User) -> bool:
        """
        Отправляет менеджеру уведомление о новом пользователе.

        :param user: Объект пользователя, о котором нужно уведомить.
        :return: True, если сообщение успешно отправлено, иначе False.
        """
        text = build_manager_message(user)
        try:
            await self.bot.send_message(self.manager_chat_id, text)
            return True
        except Exception as e:
            logging.error(f"Ошибка при отправке уведомления менеджеру: {e}")
            return False
 