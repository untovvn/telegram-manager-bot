# Telegram Bot: Менеджер-Клиент

## Описание проекта

Этот проект представляет собой Telegram-бота, разработанного на базе фреймворка `aiogram 3.x` для автоматизации взаимодействия между клиентами и менеджерами. Бот предназначен для упрощения коммуникации, маршрутизации запросов клиентов и обеспечения эффективного ответа со стороны менеджеров.

**Основные функции:**

*   **Автоматизированный диалог с клиентами:** Бот ведет клиентов по заранее определенному сценарию (Finite State Machine - FSM), собирая необходимую информацию.
*   **Передача "карточек" клиентов менеджерам:** После завершения FSM-сценария или по запросу клиента, бот формирует и отправляет "карточку" клиента назначенному менеджеру.
*   **��вусторонняя связь:** Все последующие сообщения от клиента автоматически пересылаются менеджеру. Менеджер может отвечать клиенту, используя функцию "Ответить" (Reply) в Telegram, что гарантирует доставку сообщения конкретному клиенту. Также менеджер может отправлять прямые сообщения последнему активному клиенту.
*   **Контроль доступа для менеджеров:** Доступ к функциям менеджера ограничен определенными `user_id`, настроенными в файле конфигурации.

## Технологии

*   Python 3.10+
*   aiogram 3.x (асинхронный фреймворк для Telegram Bot API)
*   python-dotenv (для управления переменными окружения)

## Установка и запуск

1.  **Клонируйте репозиторий:**
    ```bash
    git clone https://github.com/your_username/your_repo_name.git # Замените на актуальный URL
    cd your_repo_name
    ```
2.  **Создайте виртуальное окружени�� и установите зависимости:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Для Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  **Настройка переменных окружения:**
    Создайте файл `.env` в корневой директории проекта со следующим содержимым:
    ```env
    TELEGRAM_BOT_TOKEN=ВАШ_ТОКЕН_БОТА
    MANAGER_IDS=ID_МЕНЕДЖЕРА_1,ID_МЕНЕДЖЕРА_2 # Через запятую, без пробелов
    MANAGER_CHAT_ID=ID_ОСНОВНОГО_МЕНЕДЖЕРА # ID менеджера для получения карточек
    ```
    *   `TELEGRAM_BOT_TOKEN`: Получите его у @BotFather в Telegram.
    *   `MANAGER_IDS`: Список Telegram `user_id` всех менеджеров, которым разрешен доступ к функциям бота.
    *   `MANAGER_CHAT_ID`: `user_id` менеджера, который будет получать уведомления о новых клиентах и их "карточки".

4.  **Запуск бота:**
    ```bash
    python main.py
    ```

## Изменение API, ID менеджера и текста бота

*   **API токен и ID мене��жеров:** Изменяются в файле `.env` (см. выше). После изменения перезапустите бота.
*   **Текст сообщений бота и название канала:**
    *   Большинство текстов сообщений, используемых в FSM-сценариях (приветствие, вопросы, напоминания), а также название канала (`@название_канала`), находятся в файле `fsm_handlers.py`.
    *   Тексты сообщений, пересылаемых между клиентом и менеджером, находятся в файле `main.py` (функции `user_to_manager` и `manager_to_user`).
    *   Для изменения отредактируйте соответствующие строковые литералы в этих файлах и перезапустите бота.

---

# Telegram Bot: Manager-Client

## Project Description

This project is a Telegram bot developed using the `aiogram 3.x` framework, designed to automate interactions between clients and managers. The bot aims to streamline communication, route client inquiries, and ensure efficient responses from managers.

**Key Features:**

*   **Automated Client Dialogue:** The bot guides clients through a predefined scenario (Finite State Machine - FSM), collecting necessary information.
*   **Client "Card" Transfer to Managers:** Upon completion of the FSM scenario or at the client's request, the bot generates and sends a client "card" to the designated manager.
*   **Two-Way Communication:** All subsequent messages from the client are automatically forwarded to the manager. Managers can respond to clients using Telegram's "Reply" function, ensuring the message is delivered to the specific client. Managers can also send direct messages to the last active client.
*   **Access Control for Managers:** Access to manager functions is restricted to specific `user_id`s configured in the environment file.

## Technologies

*   Python 3.10+
*   aiogram 3.x (asynchronous framework for Telegram Bot API)
*   python-dotenv (for environment variable management)

## Installation and Running

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your_username/your_repo_name.git # Replace with your actual URL
    cd your_repo_name
    ```
2.  **Create a virtual environment and install dependencies:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # For Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  **Configure Environment Variables:**
    Create a `.env` file in the project's root directory with the following content:
    ```env
    TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN
    MANAGER_IDS=MANAGER_ID_1,MANAGER_ID_2 # Comma-separated, no spaces
    MANAGER_CHAT_ID=MAIN_MANAGER_ID # ID of the manager to receive client cards
    ```
    *   `TELEGRAM_BOT_TOKEN`: Obtain this from @BotFather on Telegram.
    *   `MANAGER_IDS`: A comma-separated list of Telegram `user_id`s for all managers allowed to access bot functions.
    *   `MANAGER_CHAT_ID`: The `user_id` of the manager who will receive notifications about new clients and their "cards".

4.  **Run the bot:**
    ```bash
    python main.py
    ```

## Changing API, Manager IDs, and Bot Text

*   **API Token and Manager IDs:** These are changed in the `.env` file (see above). Restart the bot after making changes.
*   **Bot Message Text and Channel Name:**
    *   Most message texts used in FSM scenarios (welcome, questions, reminders), as well as the channel name (`@channel_name`), are located in `fsm_handlers.py`.
    *   Texts for messages forwarded between the client and manager are in `main.py` (functions `user_to_manager` and `manager_to_user`).
    *   To change, edit the corresponding string literals in these files and restart the bot.
