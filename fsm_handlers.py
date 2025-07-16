
"""
Этот модуль отвечает за управление конечным автоматом (FSM)
и реализует основной сценарий взаимодействия с пользователем:
от приветствия до передачи диалога менеджеру.
"""
import asyncio
from aiogram import Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from keyboards import start_kb, yes_no_kb, location_ipo_kb, house_choice_kb
from message_map import MessageMap
from notification_service import NotificationService, build_manager_message
from states import Form
from user_session import UserSession


async def _send_manager_card_if_needed(
    message: Message,
    state: FSMContext,
    bot: Bot,
    notification_service: NotificationService,
    message_map: MessageMap
) -> None:
    """
    Приватная функция-хелпер.

    Проверяет, была ли уже отправлена карточка клиента менеджеру.
    Если нет, отправляет ее и сохраняет связь между ID сообщения
    менеджеру и ID пользователя для последующих ответов.
    """
    data = await state.get_data()
    if not data.get("card_sent"):
        user = message.from_user
        if user and user.id:
            # Отправляем карточку с информацией о клиенте менеджеру
            card = await bot.send_message(
                notification_service.manager_chat_id,
                build_manager_message(user)
            )
            # Сохраняем ID сообщения и ID пользователя, чтобы связать их для ответа
            message_map.add(card.message_id, user.id)
            # Помечаем в состоянии, что карточка была отправлена
            await state.update_data(card_sent=True)


async def stop_chain_and_call_manager(
    message: Message,
    state: FSMContext,
    user_session: UserSession
) -> None:
    """
    Завершает сценарий FSM и переводит пользователя в режим чата с менеджером.

    - Очищает состояние FSM.
    - Отправляет пользователю уведомление о вызове менеджера.
    - Устанавливает пользователя как последнего активного для сообщений от менеджера.
    """
    await state.clear()  # Сброс состояния FSM
    await message.answer(
        "Зову менеджера, он подключиться к диалогу в ближайшее время",
        reply_markup=ReplyKeyboardRemove()
    )
    if message.from_user and message.from_user.id:
        user_session.set_active_user(message.from_user.id)
    else:
        # Этот случай маловероятен, но лучше его обработать
        await message.answer("Ошибка: не удалось определить ваш ID.")


async def send_welcome(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /start. Приветствует пользователя.
    """
    await state.clear()
    text = (
        "Что умеет этот бот?\n"
        "Приветствую 👋 Я чат-менеджер канала @название_канала\n\n"
        "Нажмите НАЧАТЬ и мы ответим на ваши вопросы в ближайшее время 🙌"
    )
    await message.answer(text, reply_markup=start_kb)
    await state.set_state(Form.waiting_for_start)


async def process_start(message: Message, state: FSMContext) -> None:
    """
    Обрабатывает нажатие кнопки "Начать". Задает первый вопрос
    и запускает таймер для напоминания.
    """
    user_name = message.from_user.first_name if message.from_user else "друг"
    text = (
        f"Здравствуйте, {user_name}!\n"
        "Спасибо, что вы с нами ❤️\n\n"
        "Рассказать вам о наших готовых домах?"
    )
    await message.answer(text, reply_markup=yes_no_kb)
    await state.set_state(Form.waiting_for_houses)
    # Запускаем задачу, которая сработает через 5 минут, если пользователь не ответит
    asyncio.create_task(
        wait_for_reply(message.chat.id, state, Form.waiting_for_houses, 300, send_second_reminder, message.bot)
    )


async def process_houses(
    message: Message,
    state: FSMContext,
    user_session: UserSession,
    notification_service: NotificationService,
    message_map: MessageMap,
    bot: Bot
) -> None:
    """
    Обрабатывает ответ на вопрос о домах.
    Отправляет карточку менеджеру и завершает FSM.
    """
    await _send_manager_card_if_needed(message, state, bot, notification_service, message_map)
    await stop_chain_and_call_manager(message, state, user_session)


async def process_questions(
    message: Message,
    state: FSMContext,
    user_session: UserSession,
    notification_service: NotificationService,
    message_map: MessageMap,
    bot: Bot
) -> None:
    """
    Обрабатывает ответ на вопрос о локации/ипотеке.
    Отправляет карточку менеджеру и завершает FSM.
    """
    await _send_manager_card_if_needed(message, state, bot, notification_service, message_map)
    await stop_chain_and_call_manager(message, state, user_session)


async def process_house_choice(
    message: Message,
    state: FSMContext,
    user_session: UserSession,
    notification_service: NotificationService,
    message_map: MessageMap,
    bot: Bot
) -> None:
    """
    Обрабатывает ответ на вопрос о выборе дома.
    Отправляет карточку менеджеру и завершает FSM.
    """
    await _send_manager_card_if_needed(message, state, bot, notification_service, message_map)
    await stop_chain_and_call_manager(message, state, user_session)


async def wait_for_reply(
    chat_id: int,
    state: FSMContext,
    expected_state: Form,
    timeout: int,
    callback,
    bot: Bot
) -> None:
    """

    Ожидает ответ от пользователя в течение `timeout` секунд.
    Если пользователь не отвечает и состояние не изменилось,
    вызывает `callback` для отправки напоминания.
    """
    await asyncio.sleep(timeout)
    current_state = await state.get_state()
    # Если состояние все еще то, которого мы ждали, значит, пользователь не ответил
    if current_state == expected_state.state:
        await callback(chat_id, state, bot)


async def send_second_reminder(chat_id: int, state: FSMContext, bot: Bot):
    """
    Отправляет второе напоминание пользователю и переводит
    его на следующий шаг FSM.
    """
    user = await bot.get_chat(chat_id)
    user_name = user.first_name or "друг"
    text = (
        f"{user_name}, может быть у вас уже появились какие-то вопросы? "
        "Наприм��р, про локацию или условия покупки?"
    )
    await bot.send_message(chat_id, text, reply_markup=location_ipo_kb)
    await state.set_state(Form.waiting_for_questions)
    # Запускаем таймер для третьего напоминания
    asyncio.create_task(
        wait_for_reply(chat_id, state, Form.waiting_for_questions, 300, send_third_reminder, bot)
    )


async def send_third_reminder(chat_id: int, state: FSMContext, bot: Bot):
    """
    Отправляет третье, финальное, напоминание с предложением
    конкретного дома.
    """
    text = (
        "С платежом 55 190 руб на весь срок у нас можно приобрести такой готовый дом. "
        "Вам подходит такой вариант или хотели бы площадь побольше?"
    )
    photo_url = "https://i.imgur.com/4M34hi2.jpg"
    await bot.send_photo(chat_id, photo=photo_url, caption=text, reply_markup=house_choice_kb)
    await state.set_state(Form.waiting_for_house_choice)
 