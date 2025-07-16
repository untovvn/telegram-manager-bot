# Telegram Bot: Менеджер-Клиент

## Описание

Этот проект — Telegram-бот на базе aiogram 3.x для организации диалога между клиентом и менеджером. Бот:
- Ведёт диалог с клиентом по сценарию (FSM).
- После запроса клиента отправляет его "карточку" менеджеру.
- Все последующие сообщения клиента пересылаются менеджеру.
- Менеджер может отвечать клиенту через reply или прямым сообщением.
- Доступ к режиму менеджера только у пользователей с определёнными user_id.

---

## Быстрый старт

1.  **Склонируйте репозиторий и установите зависимости:**
    ```bash
    git clone [<repo_url>](https://github.com/untovvn/telegram-manager-bot)
    cd <project_folder>
    python -m venv venv
    source venv/bin/activate  # или venv\Scripts\activate для Windows
    pip install -r requirements.txt
    ```

2.  **С��здайте файл `.env` в корне проекта:**
    ```env
    TELEGRAM_BOT_TOKEN=ваш_токен_бота
    MANAGER_IDS=123456789,987654321  # user_id менеджеров через запятую
    MANAGER_CHAT_ID=123456789        # user_id основного менеджера (для уведомлений)
    ```
    -   `TELEGRAM_BOT_TOKEN` — API ключ вашего Telegram-бота (получить у @BotFather).
    -   `MANAGER_IDS` — список user_id всех менеджеров, которым разрешён доступ к режиму менеджера.
    -   `MANAGER_CHAT_ID` — user_id менеджера, которому будут приходить карточки клиентов (обычно совпадает с одним из MANAGER_IDS).

3.  **Запустите бота:**
    ```bash
    python main.py
    ```

---

## Как работает бот (Подробно)

Бот построен на фреймворке `aiogram 3.x` и использует концепции конечных автоматов (FSM) для управления диалогами с клиентами, а также специализированные сервисы для маршрутизации сообщений между клиентами и менеджерами.

**Основные компоненты и их роли:**

*   **`main.py`**: Главный файл, который инициализирует бота, диспетчер, хранилище состояний (MemoryStorage для FSM) и все сервисные классы (`UserSession`, `NotificationService`, `MessageMap`, `ManagerStore`). Здесь же происходит регистрация всех обработчиков сообщений (хендлеров) для различных команд, состояний FSM и пересылки сообщений.
*   **`fsm_handlers.py`**: Содержит логику для сценариев FSM. Это функции, которые обрабатывают сообщения пользователя в зависимости от его текущего состояния (например, приветствие, вопросы о домах, ипотеке и т.д.). Здесь определены функции `send_welcome`, `process_start`, `process_houses`, `process_questions`, `process_house_choice`, `stop_chain_and_call_manager` и логика напоминаний (`wait_for_reply`, `send_second_reminder`, `send_third_reminder`).
*   **`manager_auth.py`**: Отвечает за проверку прав доступа менеджеров. Содержит класс `ManagerStore` для хранения ID менеджеров и функцию `check_manager_command` для обработки команды `/manager`.
*   **`notification_service.py`**: Сервис, отвечающий за отправку уведомлений и "карточек" клиентов менеджерам. Использует `MANAGER_CHAT_ID` из `.env` для определения, куда отправлять уведомления.
*   **`user_session.py`**: Простой сервис для отслеживания "активного" пользователя. Когда менеджер пишет прямое сообщение (не реплай), оно отправляется последнему клиенту, с которым менеджер взаимодействовал.
*   **`message_map.py`**: **Ключевой компонент для общения менеджера с несколькими клиентами.** Этот сервис хранит сопоставление между `message_id` сообщений, отправленных менеджеру (например, "карточек" клиентов или пересланных сообщений клиента), и `user_id` соответствующего к��иента.
    *   Когда клиент пишет боту, и его сообщение пересылается менеджеру (`user_to_manager`), `message_map` записывает `message_id` пересланного сообщения и `user_id` клиента.
    *   Когда менеджер отвечает на *конкретное сообщение* (делает reply) в своем чате, функция `manager_to_user` извлекает `message_id` исходного сообщения из `message.reply_to_message.message_id`. Затем `message_map` используется для поиска `user_id` клиента, связанного с этим `message_id`. Сообщение менеджера отправляется *только* этому конкретному `user_id`. Это обеспечивает точную маршрутизацию ответов.
*   **`states.py`**: Определяет состояния FSM для клиента (например, `Form.waiting_for_start`, `Form.waiting_for_houses`).
*   **`keyboards.py`**: Содержит определения ReplyKeyboardMarkup для кнопок, используемых в диалоге с клиентом.

**Сценарий взаимодействия:**

1.  **Клиент начинает ди��лог (`/start`)**: Бот приветствует клиента (`send_welcome`), устанавливает начальное состояние FSM (`Form.waiting_for_start`) и предлагает нажать кнопку "Начать".
2.  **Клиент нажимает "Начать"**: Бот задает первый вопрос (`process_start`) и переводит клиента в состояние `Form.waiting_for_houses`. Запускается таймер напоминания.
3.  **Клиент отвечает на вопросы FSM**: В зависимости от ответов, бот переводит клиента по состояниям (`process_houses`, `process_questions`, `process_house_choice`).
4.  **Завершение FSM и вызов менеджера**: После прохождения сценария FSM (или при определенных ответах), функция `stop_chain_and_call_manager` очищает состояние FSM, уведомляет клиента о вызове менеджера и устанавливает клиента как "активного" в `user_session`.
5.  **Отправка "карточки" клиента менеджеру**: Функция `_send_manager_card_if_needed` (вызываемая из FSM-хенд��еров) формирует "карточку" с информацией о клиенте и отправляет ее менеджеру (в чат, указанный в `MANAGER_CHAT_ID`). ID этого сообщения менеджера и ID клиента сохраняются в `message_map`.
6.  **Прямое сообщение клиента менеджеру**: Если клиент пишет сообщение, находясь вне FSM-сценария, оно перехватывается хендлером `user_to_manager`. Это сообщение пересылается менеджеру, и его `message_id` также сохраняется в `message_map` вместе с `user_id` клиента.
7.  **Ответ менеджера клиенту (через reply)**: Менеджер отвечает на любое сообщение, полученное от бота (будь то "карточка" клиента или пересланное сообщение клиента), используя функцию "Ответить" (Reply) в Telegram. Хендлер `manager_to_user` перехватывает это сообщение, использует `message.reply_to_message.message_id` для поиска `user_id` клиента в `message_map` и отправляет от��ет *только* этому клиенту.
8.  **Прямое сообщение менеджера клиенту (без reply)**: Если менеджер просто пишет сообщение в чат с ботом (не делая reply), хендлер `manager_to_user` отправляет это сообщение последнему "активному" клиенту, чей `user_id` хранится в `user_session`.

---

## Как изменить переменные API бота, ID менеджера

Все основные конфигурационные переменные хранятся в файле `.env` в корне проекта. Для их изменения достаточно отредактировать этот файл:

*   **`TELEGRAM_BOT_TOKEN`**: Замените `ваш_токен_бота` на актуальный токен, полученный у @BotFather.
*   **`MANAGER_IDS`**: Укажите user_id всех менеджеров, которым разрешен доступ к команде `/manager`. Если у вас несколько менеджеров, перечислите их ID через запятую, без пробелов (например, `123456789,987654321`).
*   **`MANAGER_CHAT_ID`**: Укажите user_id менеджера, ��оторому будут приходить уведомления о новых клиентах ("карточки"). Обычно это один из ID, указанных в `MANAGER_IDS`.

После изменения `.env` необходимо перезапустить бота, чтобы изменения вступили в силу.

---

## Как изменить название канала и текст сообщений

Тексты сообщений и название канала жестко закодированы в файлах Python. Для их изменения необходимо отредактировать соответствующие строки кода.

*   **Название канала (`@название_канала`)**:
    *   Откройте файл `fsm_handlers.py`.
    *   Найдите функцию `send_welcome`.
    *   Внутри этой функции найдите строку, содержащую `Я чат-менеджер канала @название_канала` и измените `@название_канала` на актуальное название вашего канала.

*   **Тексты сообщений бота (FSM-сценарии)**:
    *   Все сообщения, которые бот отправляет ��лиенту в рамках FSM-сценариев (приветствие, вопросы, напоминания), находятся в файле `fsm_handlers.py`.
    *   Ищите функции:
        *   `send_welcome`: Приветственное сообщение.
        *   `process_start`: Сообщение после нажатия "Начать".
        *   `stop_chain_and_call_manager`: Сообщение о вызове менеджера.
        *   `send_second_reminder`: Текст второго напоминания.
        *   `send_third_reminder`: Текст третьего напоминания.
    *   Изменяйте текст внутри строковых литералов.

*   **Тексты сообщений для пересылки (клиент-менеджер, менеджер-клиент)**:
    *   Эти сообщения находятся в файле `main.py`.
    *   Ищите функции:
        *   `user_to_manager`: Формат сообщения, которое клиент отправляет менеджеру.
        *   `manager_to_user`: Формат сообщения, которое менеджер отправляет клиенту.
    *   Изменяйте текст внутри строковых литералов.

По��ле изменения любого из этих файлов необходимо перезапустить бота, чтобы изменения вступили в силу.

---

## Как добавить менеджера

-   Узнайте user_id менеджера (например, через @userinfobot в Telegram).
-   Откройте файл `.env` в корне проекта.
-   Добавьте user_id нового менеджера в переменную `MANAGER_IDS`. Если там уже есть ID, добавьте новый через запятую (например, `MANAGER_IDS=123456789,987654321,НОВЫЙ_ID_МЕНЕДЖЕРА`).
-   Если вы хотите, чтобы этот менеджер получал "карточки" новых клиентов, убедитесь, что его user_id указан в переменной `MANAGER_CHAT_ID` (или измените `MANAGER_CHAT_ID` на его ID, если он будет основным получателем).
-   Перезапустите бота.

---

## Тестирование

-   Все юнит-тесты находятся в папке `tests/`.
-   Для запуска тестов используйте:
    ```bash
    pytest tests
    ```
-   После завершения тестов выводится итоговый статус по основным функциям.

---

## Структура проекта

-   `main.py` — точка входа, инициализация, регистрация хендлеров, запуск бота.
-   `fsm_handlers.py` — бизнес-логика сценариев FSM, обработчики состояний.
-   `manager_auth.py` — логика авторизации менеджера, хранение ID менеджеров.
-   `notification_service.py` — сервис для отправки уведомлений и "карточек" менеджерам.
-   `user_session.py` — хранение ID последнего активного пользователя для прямых сообщений.
-   `message_map.py` — сопоставление ID сообщений менеджера с ID клиентов для ответов.
-   `states.py` — определения состояний FSM.
-   `keyboards.py` — определения ReplyKeyboardMarkup для кнопок.
-   `tests/` — все юнит-тесты.

---

## Контакты

Вопросы и предложения приветствуются

---

# Telegram Bot: Manager-Client

## Description

This project is a Telegram bot built on the aiogram 3.x framework for organizing dialogue between clients and managers. The bot:
- Guides the client through a scenario (FSM).
- Sends a client "card" to the manager after the client's request.
- All subsequent client messages are forwarded to the manager.
- The manager can reply to the client via reply or direct message.
- Access to manager mode is restricted to users with specific user_ids.

---

## Quick Start

1.  **Clone the repository and install dependencies:**
    ```bash
    git clone <repo_url>
    cd <project_folder>
    python -m venv venv
    source venv/bin/activate  # or venv\Scripts\activate for Windows
    pip install -r requirements.txt
    ```

2.  **Create a `.env` file in the project root:**
    ```env
    TELEGRAM_BOT_TOKEN=your_bot_token
    MANAGER_IDS=123456789,987654321  # comma-separated user_ids of managers
    MANAGER_CHAT_ID=123456789        # user_id of the main manager (for notifications)
    ```
    -   `TELEGRAM_BOT_TOKEN` — Your Telegram bot's API key (get it from @BotFather).
    -   `MANAGER_IDS` — A list of user_ids for all managers allowed to access manager mode.
    -   `MANAGER_CHAT_ID` — The user_id of the manager who will receive client cards (usually matches one of MANAGER_IDS).

3.  **Run the bot:**
    ```bash
    python main.py
    ```

---

## How the Bot Works (Detailed)

The bot is built on the `aiogram 3.x` framework and uses Finite State Machine (FSM) concepts to manage client dialogues, as well as specialized services for routing messages between clients and managers.

**Key Components and Their Roles:**

*   **`main.py`**: The main file that initializes the bot, dispatcher, state storage (MemoryStorage for FSM), and all service classes (`UserSession`, `NotificationService`, `MessageMap`, `ManagerStore`). This is also where all message handlers for various commands, FSM states, and message forwarding are registered.
*   **`fsm_handlers.py`**: Contains the logic for FSM scenarios. These are functions that process user messages based on their current state (e.g., welcome, questions about houses, mortgages, etc.). This file defines `send_welcome`, `process_start`, `process_houses`, `process_questions`, `process_house_choice`, `stop_chain_and_call_manager`, and reminder logic (`wait_for_reply`, `send_second_reminder`, `send_third_reminder`).
*   **`manager_auth.py`**: Responsible for checking manager access rights. Contains the `ManagerStore` class for storing manager IDs and the `check_manager_command` function for handling the `/manager` command.
*   **`notification_service.py`**: A service responsible for sending notifications and client "cards" to managers. Uses `MANAGER_CHAT_ID` from `.env` to determine where to send notifications.
*   **`user_session.py`**: A simple service for tracking the "active" user. When a manager sends a direct message (not a reply), it is sent to the last client the manager interacted with.
*   **`message_map.py`**: **A key component for manager-to-multiple-client communication.** This service stores a mapping between the `message_id` of messages sent to the manager (e.g., client "cards" or forwarded client messages) and the `user_id` of the corresponding client.
    *   When a client messages the bot and their message is forwarded to the manager (`user_to_manager`), `message_map` records the `message_id` of the forwarded message and the client's `user_id`.
    *   When a manager replies to a *specific message* (uses the reply function) in their chat, the `manager_to_user` function retrieves the original message's `message_id` from `message.reply_to_message.message_id`. `message_map` is then used to find the client's `user_id` associated with that `message_id`. The manager's message is sent *only* to that specific `user_id`. This ensures accurate reply routing.
*   **`states.py`**: Defines the FSM states for the client (e.g., `Form.waiting_for_start`, `Form.waiting_for_houses`).
*   **`keyboards.py`**: Contains ReplyKeyboardMarkup definitions for buttons used in the client dialogue.

**Interaction Scenario:**

1.  **Client starts dialogue (`/start`)**: The bot greets the client (`send_welcome`), sets the initial FSM state (`Form.waiting_for_start`), and prompts them to press the "Start" button.
2.  **Client presses "Start"**: The bot asks the first question (`process_start`) and transitions the client to the `Form.waiting_for_houses` state. A reminder timer is started.
3.  **Client answers FSM questions**: Depending on the answers, the bot guides the client through FSM states (`process_houses`, `process_questions`, `process_house_choice`).
4.  **FSM completion and manager call**: After completing the FSM scenario (or based on specific answers), the `stop_chain_and_call_manager` function clears the FSM state, notifies the client that a manager is being called, and sets the client as "active" in `user_session`.
5.  **Sending client "card" to manager**: The `_send_manager_card_if_needed` function (called from FSM handlers) forms a "card" with client information and sends it to the manager (to the chat specified in `MANAGER_CHAT_ID`). The message ID of this manager message and the client's user ID are stored in `message_map`.
6.  **Client's direct message to manager**: If the client sends a message while outside an FSM scenario, it's intercepted by the `user_to_manager` handler. This message is forwarded to the manager, and its `message_id` also stored in `message_map` along with the client's `user_id`.
7.  **Manager's reply to client (via reply)**: The manager replies to any message received from the bot (whether it's a client "card" or a forwarded client message) using Telegram's "Reply" function. The `manager_to_user` handler intercepts this message, uses `message.reply_to_message.message_id` to find the client's `user_id` in `message_map`, and sends the reply *only* to that specific client.
8.  **Manager's direct message to client (without reply)**: If the manager simply sends a message to the bot's chat (without replying), the `manager_to_user` handler sends this message to the last "active" client whose `user_id` is stored in `user_session`.

---

## How to Change Bot API Variables, Manager IDs

All main configuration variables are stored in the `.env` file in the project root. To change them, simply edit this file:

*   **`TELEGRAM_BOT_TOKEN`**: Replace `your_bot_token` with the actual token obtained from @BotFather.
*   **`MANAGER_IDS`**: Specify the user_ids of all managers allowed to access the `/manager` command. If you have multiple managers, list their IDs separated by commas, without spaces (e.g., `123456789,987654321`).
*   **`MANAGER_CHAT_ID`**: The user_id of the manager who will receive notifications about new clients ("cards"). This is usually one of the IDs listed in `MANAGER_IDS`.

After changing `.env`, you must restart the bot for the changes to take effect.

---

## How to Change Channel Name and Message Text

Message texts and the channel name are hardcoded in the Python files. To change them, you need to edit the corresponding lines of code.

*   **Channel Name (`@channel_name`)**:
    *   Open the `fsm_handlers.py` file.
    *   Find the `send_welcome` function.
    *   Inside this function, locate the string containing `Я чат-менеджер канала @название_канала` and change `@название_канала` to your actual channel name.

*   **Bot Message Texts (FSM Scenarios)**:
    *   All messages the bot sends to the client within FSM scenarios (welcome, questions, reminders) are located in `fsm_handlers.py`.
    *   Look for the functions:
        *   `send_welcome`: Welcome message.
        *   `process_start`: Message after pressing "Start".
        *   `stop_chain_and_call_manager`: Message about calling a manager.
        *   `send_second_reminder`: Text of the second reminder.
        *   `send_third_reminder`: Text of the third reminder.
    *   Edit the text within the string literals.

*   **Message Forwarding Texts (Client-Manager, Manager-Client)**:
    *   These messages are located in `main.py`.
    *   Look for the functions:
        *   `user_to_manager`: Format of the message the client sends to the manager.
        *   `manager_to_user`: Format of the message the manager sends to the client.
    *   Edit the text within the string literals.

After changing any of these files, you must restart the bot for the changes to take effect.

---

## How to Add a Manager

-   Find out the manager's user_id (e.g., via @userinfobot in Telegram).
-   Open the `.env` file in the project root.
-   Add the new manager's user_id to the `MANAGER_IDS` variable. If there are already IDs, add the new one separated by a comma (e.g., `MANAGER_IDS=123456789,987654321,NEW_MANAGER_ID`).
-   If you want this manager to receive new client "cards", ensure their user_id is specified in the `MANAGER_CHAT_ID` variable (or change `MANAGER_CHAT_ID` to their ID if they will be the primary recipient).
-   Restart the bot.

---

## Testing

-   All unit tests are located in the `tests/` folder.
-   To run tests, use:
    ```bash
    pytest tests
    ```
-   After tests complete, a summary status for key functions is displayed.

---

## Project Structure

-   `main.py` — Entry point, initialization, handler registration, bot launch.
-   `fsm_handlers.py` — FSM scenario business logic, state handlers.
-   `manager_auth.py` — Manager authorization logic, manager ID storage.
-   `notification_service.py` — Service for sending notifications and "cards" to managers.
-   `user_session.py` — Stores the ID of the last active user for direct messages.
-   `message_map.py` — Maps manager message IDs to client IDs for replies.
-   `states.py` — FSM state definitions.
-   `keyboards.py` — ReplyKeyboardMarkup definitions for buttons.
-   `tests/` — All unit tests.

---

## Important

-   Do not publish your `.env` file or bot token publicly!
-   The bot requires Python 3.10+ and aiogram 3.x to run.

---

## Contacts

Questions and suggestions are welcome.
