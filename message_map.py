"""
Модуль для сопоставления сообщений.

Ключевой сервис, который позволяет связывать сообщения, отправленные
менеджеру, с исходным пользователем. Это делает возможным
корректную работу функции "Ответ" (reply).
"""

class MessageMap:
    """
    Хранит в памяти сопоставление ID сообщения в чате менеджера
    с ID пользователя, который инициировал это сообщение.

    Структура: {manager_message_id: user_id}
    """
    def __init__(self):
        self._msg_to_user: dict[int, int] = {}

    def add(self, manager_msg_id: int, user_id: int) -> None:
        """
        Добавляет новую связь "сообщение менеджера -> пользователь".
        """
        self._msg_to_user[manager_msg_id] = user_id

    def get_user(self, manager_msg_id: int) -> int | None:
        """
        Возвращает ID пользователя по ID сообщения в чате менеджера.
        """
        return self._msg_to_user.get(manager_msg_id)

    def clear(self, manager_msg_id: int) -> None:
        """
        Удаляет связь из хранилища. Может быть полезно,
        когда диалог считается завершенным.
        """
        if manager_msg_id in self._msg_to_user:
            del self._msg_to_user[manager_msg_id]
 