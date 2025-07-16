import pytest

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    results = {
        'send_message': 'Функция "Отправка сообщений"',
        'manager_login': 'Функция "Входа в режим менеджера"',
        'manager_receive': 'Функция "Получение сообщения менеджером"',
        'client_receive': 'Функция "Получение сообщения клиентом"',
        'fsm_flow': 'Функция "FSM сценарии"',
    }
    status_map = {True: 'РАБОТАЕТ', False: 'НЕ РАБОТАЕТ'}
    passed = {k: False for k in results}

    # Проверяем, существуют ли отчеты о пройденных тестах
    if 'passed' not in terminalreporter.stats:
        return

    for rep in terminalreporter.stats['passed']:
        name = rep.nodeid.lower() # Приводим имя к нижнему регистру для надежности

        # Проверка получения сообщения менеджером (когда пользователь пишет боту)
        if 'test_user_to_manager' in name:
            passed['manager_receive'] = True

        # Проверка получения сообщения клиентом (когда менеджер отвечает)
        if 'test_manager_to_user' in name:
            passed['client_receive'] = True

        # Проверка FSM сценария (отправка карточки и сброс состояния)
        if 'test_process_houses' in name:
            passed['fsm_flow'] = True

        # Проверка отправки сообщений (общая)
        if passed['manager_receive'] and passed['client_receive']:
            passed['send_message'] = True

        # Проверка входа менеджера (оставим старую логику, если она актуальна)
        if 'test_manager_command' in name or 'test_manager_promotion' in name:
            passed['manager_login'] = True

    terminalreporter.write_sep("=", "\nРЕЗУЛЬТАТЫ ФУНКЦИОНАЛЬНЫХ ТЕСТОВ:")
    for k, v in results.items():
        terminalreporter.write_line(f"{v} - статус: {status_map[passed[k]]}") 