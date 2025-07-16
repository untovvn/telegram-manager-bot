import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils import executor
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from dotenv import load_dotenv
except ImportError:
    raise ImportError('Для работы с переменными окружения установите пакет python-dotenv: pip install python-dotenv')

# pip install python-dotenv
load_dotenv()
API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not API_TOKEN:
    raise ValueError('TELEGRAM_BOT_TOKEN is not set in the environment variables!')

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

CHANNEL_NAME = "@название_канала"  # <-- замените на ваш канал

# Состояния для FSM
class Form(StatesGroup):
    waiting_for_start = State()
    waiting_for_houses = State()
    waiting_for_questions = State()
    waiting_for_house_choice = State()
    stopped = State()

# Клавиатуры
start_kb = ReplyKeyboardMarkup(resize_keyboard=True)
start_kb.add(KeyboardButton("Начать"))

yes_no_kb = ReplyKeyboardMarkup(resize_keyboard=True)
yes_no_kb.add(KeyboardButton("ДА"), KeyboardButton("НЕТ"))

location_ipo_kb = ReplyKeyboardMarkup(resize_keyboard=True)
location_ipo_kb.add(KeyboardButton("Узнать локацию"), KeyboardButton("Узнать про ипотеку"))

house_choice_kb = ReplyKeyboardMarkup(resize_keyboard=True)
house_choice_kb.add(KeyboardButton("Подходит"), KeyboardButton("А какие еще есть дома?"))

# Хендлер старта
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message, state: FSMContext):
    await state.finish()
    text = (
        "Что умеет этот бот?\n"
        "Приветствую 👋 Я чат-менеджер канала {channel}\n\n"
        "Нажмите НАЧАТЬ и мы ответим на ваши вопросы в ближайшее время 🙌"
    ).format(channel=CHANNEL_NAME)
    await message.answer(text, reply_markup=start_kb)
    await Form.waiting_for_start.set()

# Обработка кнопки "Начать"
@dp.message_handler(Text(equals="Начать"), state=Form.waiting_for_start)
async def process_start(message: types.Message, state: FSMContext):
    user_name = message.from_user.first_name or "друг"
    text = (
        f"Здравствуйте, {user_name}!\n"
        "Спасибо, что вы с нами ❤️\n\n"
        "Рассказать вам о наших готовых домах?"
    )
    await message.answer(text, reply_markup=yes_no_kb)
    await Form.waiting_for_houses.set()
    # Запускаем таймер на 5 минут
    asyncio.create_task(wait_for_reply(message.chat.id, state, Form.waiting_for_houses, 300, send_second_reminder))

# Обработка ДА/НЕТ и любого текста
@dp.message_handler(state=Form.waiting_for_houses)
async def process_houses(message: types.Message, state: FSMContext):
    await stop_chain_and_call_manager(message, state)

# Вторая напоминалка через 5 минут
async def send_second_reminder(chat_id, state: FSMContext):
    data = await state.get_data()
    current_state = await state.get_state()
    if current_state == Form.waiting_for_houses.state:
        user = await bot.get_chat(chat_id)
        user_name = user.first_name or "друг"
        text = (
            f"{user_name}, может быть у вас уже появились какие-то вопросы? "
            "Например, про локацию или условия покупки?"
        )
        await bot.send_message(chat_id, text, reply_markup=location_ipo_kb)
        await Form.waiting_for_questions.set()
        asyncio.create_task(wait_for_reply(chat_id, state, Form.waiting_for_questions, 300, send_third_reminder))

# Обработка кнопок и текста на втором этапе
@dp.message_handler(state=Form.waiting_for_questions)
async def process_questions(message: types.Message, state: FSMContext):
    await stop_chain_and_call_manager(message, state)

# Третья напоминалка через еще 5 минут
async def send_third_reminder(chat_id, state: FSMContext):
    data = await state.get_data()
    current_state = await state.get_state()
    if current_state == Form.waiting_for_questions.state:
        text = (
            "С платежом 55 190 руб на весь срок у нас можно приобрести такой готовый дом. "
            "Вам подходит такой вариант или хотели бы площадь побольше?"
        )
        photo_url = "https://i.imgur.com/4M34hi2.jpg"  # <-- замените на фото вашего дома
        await bot.send_photo(chat_id, photo=photo_url, caption=text, reply_markup=house_choice_kb)
        await Form.waiting_for_house_choice.set()

# Обработка кнопок и текста на третьем этапе
@dp.message_handler(state=Form.waiting_for_house_choice)
async def process_house_choice(message: types.Message, state: FSMContext):
    await stop_chain_and_call_manager(message, state)

# Функция остановки цепочки и вызова менеджера
async def stop_chain_and_call_manager(message: types.Message, state: FSMContext):
    await state.set_state(Form.stopped.state)
    await message.answer(
        "Зову менеджера, он подключиться к диалогу в ближайшее время",
        reply_markup=types.ReplyKeyboardRemove()
    )

# Функция ожидания ответа пользователя
async def wait_for_reply(chat_id, state: FSMContext, expected_state, timeout, callback):
    await asyncio.sleep(timeout)
    current_state = await state.get_state()
    if current_state == expected_state.state:
        await callback(chat_id, state)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
