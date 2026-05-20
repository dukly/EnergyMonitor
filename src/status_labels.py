STATUS_LABELS: dict[int, str] = {
    0: 'Ожидание',
    1: 'Нормальная работа',
    2: 'Предупреждение',
    3: 'Ошибка',
    4: 'Отключён',
}

ERROR_LABELS: dict[int, str] = {
    0: 'Нет ошибки',
    1: 'Перегрев',
    2: 'Ошибка сети',
    3: 'Ошибка DC',
    4: 'Ошибка связи RS485',
    5: 'Внутренняя ошибка',
}


def decode_status(code: int | None) -> str | None:
    if code is None:
        return None
    return STATUS_LABELS.get(code, f'Неизвестный статус ({code})')


def decode_error(code: int | None) -> str | None:
    if code is None:
        return None
    return ERROR_LABELS.get(code, f'Неизвестная ошибка ({code})')
