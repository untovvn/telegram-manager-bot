import sys
import os
from aiogram import Bot
from notification_service import NotificationService
from dotenv import load_dotenv
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

load_dotenv()

token = os.getenv("TELEGRAM_BOT_TOKEN")
manager_id = int(os.getenv("MANAGER_CHAT_ID", "0"))
if not token:
    raise RuntimeError("TELEGRAM_BOT_TOKEN не задан")
if not manager_id:
    raise RuntimeError("MANAGER_CHAT_ID не задан")
token: str = token  # type: ignore

async def main():
    bot = Bot(token=token)
    service = NotificationService(bot)
    service.manager_chat_id = manager_id

    class DummyUser:
        username = "testuser"
        first_name = "Test"
        id = 42

    user = DummyUser()
    result = await service.notify_manager(user)
    print(f"Результат отправки: {result}")

if __name__ == "__main__":
    asyncio.run(main()) 