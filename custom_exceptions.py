class FailedRequestError(Exception):
    """Ошибка запроса к API."""

    pass


class FailedStatusError(Exception):
    """Ошибка статуса запроса к API."""

    pass


class FailedJSONDecodeError(Exception):
    """Ошибка декодирования ответа."""

    pass


class EmptyError(Exception):
    """Ответ пустой."""

    pass


class TelegramMessageError(Exception):
    """Ошибка отправки сообщения."""

    pass
