
"""
Главный файл приложения.

Отвечает за:
1. Инициализацию всех сервисов и объектов бота.
2. Регистрацию обработчиков сообщений (хендлеров).
3. Запуск бота.
"""
import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from dotenv import load_dotenv

from fsm_handlers import (process_house_choice, process_houses,
                          process_questions, process_start, send_welcome)
from manager_auth import ManagerStore, check_manager_command
from message_map import MessageMap
from notification_service import NotificationService
from states import Form
from user_session import UserSession

# --- 1. Конфигурация и инициализация ---

# Загружаем переменные окружения из файла .env
load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("Не найден TELEGRAM_BOT_TOKEN в переменных окружения!")

# Настраиваем базовое логирование
logging.basicConfig(level=logging.INFO)

# Создаем основные объекты aiogram
# `storage=MemoryStorage()` означает, что все состояния FSM будут храниться в оперативной памяти.
# Для production-окружения рекомендуется использовать более надежное хранилище, например, Redis.
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Создаем экземпляры наших сервисных классов.
# Эти объекты будут использоваться в обработчиках для выполнения бизнес-логики.
# Такой подход (создание объектов здесь и передача их в хендлеры) называется
# Dependency Injection (Внедрение зависимостей) и упрощает тестирование.
user_session = UserSession()
notification_service = NotificationService(bot)
message_map = MessageMap()
manager_store = ManagerStore()


# --- 2. Обработчики для пересылки сообщений ---

async def user_to_manager(
    message: Message,
    state: FSMContext,
    bot: Bot,
    notification_service: NotificationService,
    user_session: UserSession,
    message_map: MessageMap
):
    """
    Пересылает сообщение от обычного пользователя менеджеру.
    Срабатывает только если пользователь не находится ни в одном из состояний FSM.
    """
    current_state = await state.get_state()
    if current_state is not None:
        # Если пользователь в FSM-сценарии, этот хендлер не должен срабатывать.
        # Его сообщения будут обработаны FSM-хендлерами.
        return

    if message.from_user and message.from_user.id:
        user_id = message.from_user.id
        first_name = message.from_user.first_name
        user_session.set_active_user(user_id)

        # Пересылаем текстовое сообщение менеджеру
        sent_message = await bot.send_message(
            notification_service.manager_chat_id,
            f"Сообщение от {first_name} ({user_id}):\n{message.text}"
        )
        # Сохраняем связь между сообщением и пользователем для ответа
        message_map.add(sent_message.message_id, user_id)


async def manager_to_user(
    message: Message,
    bot: Bot,
    message_map: MessageMap,
    user_session: UserSession
):
    """
    Обрабатывает сообщение от менеджера и пересылает его клиенту.
    """
    # Если менеджер отвечает на конкретное сообщение (делает reply)
    if message.reply_to_message and message.reply_to_message.message_id:
        # Находим ID пользователя, которому предназначался ответ
        user_id = message_map.get_user(message.reply_to_message.message_id)
        if user_id:
            try:
                await bot.send_message(user_id, f"Менеджер: {message.text}")
            except Exception as e:
                logging.error(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
                await message.answer(f"Не удалось отправить сообщение пользователю: {e}")
        else:
            await message.answer("Не удалось определить пользователя для ответа. Ответьте на сообщение пользователя.")
    else:
        # Если менеджер пишет обычное сообщение, оно отправляется последнему активному пользователю
        active_user_id = user_session.get_active_user()
        if active_user_id:
            try:
                await bot.send_message(active_user_id, f"Менеджер: {message.text}")
            except Exception as e:
                logging.error(f"Не удалось отправить сообщение последнему активному пользователю {active_user_id}: {e}")
                await message.answer(f"Не удалось отправить сообщение пользователю: {e}")
        else:
            await message.answer("Нет активного чата с пользователем.")


# --- 3. Основная функция и регистрация хендлеров ---

async def main():
    """
    Главная асинхронная функция.
    Создает обертки для хендлеров и регистрирует их в диспетчере.
    """

    # --- Обертки для хендлеров с зависимостями ---
    # Создаем небольшие асинхронные функции, которые "замыкают" в себе
    # нужные зависимости (bot, user_session и т.д.) и вызывают
    # основную логику из других файлов.
    # Это позволяет держать код чистым и тестируемым.

    async def handle_process_houses(message: Message, state: FSMContext):
        await process_houses(message, state, user_session, notification_service, message_map, bot)

    async def handle_process_questions(message: Message, state: FSMContext):
        await process_questions(message, state, user_session, notification_service, message_map, bot)

    async def handle_process_house_choice(message: Message, state: FSMContext):
        await process_house_choice(message, state, user_session, notification_service, message_map, bot)

    async def handle_manager_command(message: Message):
        await check_manager_command(message, manager_store)

    async def handle_manager_to_user(message: Message):
        await manager_to_user(message, bot, message_map, user_session)

    async def handle_user_to_manager(message: Message, state: FSMContext):
        await user_to_manager(message, state, bot, notification_service, user_session, message_map)

    # --- Регистрация хендлеров в диспетчере ---
    # Порядок регистрации имеет значение! aiogram проверяет фильтры по очереди.

    # 1. Хендлеры для команд и старта FSM
    dp.message(Command("start"))(send_welcome)
    dp.message(F.text == "Начать", Form.waiting_for_start)(process_start)

    # 2. Хендлеры для состояний FSM
    dp.message(Form.waiting_for_houses)(handle_process_houses)
    dp.message(Form.waiting_for_questions)(handle_process_questions)
    dp.message(Form.waiting_for_house_choice)(handle_process_house_choice)

    # 3. Хендлер для команды /manager
    dp.message(Command("manager"))(handle_manager_command)

    # 4. Хендлеры для пересылки сообщений.
    # Они должны идти в конце, так как их фильтры более "широкие".
    # Сначала проверяем, не пишет ли нам менеджер.
    dp.message(lambda m: m.from_user.id == notification_service.manager_chat_id)(handle_manager_to_user)
    # Если нет, то это обычный пользователь.
    dp.message(lambda m: m.from_user.id != notification_service.manager_chat_id)(handle_user_to_manager)

    # Запускаем polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
 