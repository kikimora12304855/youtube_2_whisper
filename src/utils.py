import re
from typing import Union


# Константы
MAX_FILENAME_LENGTH = 200


def sanitize_filename(filename: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    """
    Удаляет или заменяет недопустимые символы в имени файла.

    Заменяет символы < > : " / \\ | ? * на подчеркивание.
    Обрезает имя до максимальной длины.

    Args:
        filename: Исходное имя файла
        max_length: Максимальная длина имени файла

    Returns:
        str: Санитизированное имя файла

    Example:
        >>> sanitize_filename("video:test/2024")
        "video_test_2024"
    """
    # Заменяем недопустимые символы на подчеркивание
    clean_name = re.sub(r'[<>:"/\\\\|?*]', "_", filename).strip()

    # Обрезаем до максимальной длины
    if len(clean_name) > max_length:
        clean_name = clean_name[:max_length]

    return clean_name


def parse_time(time_str: Union[str, int, float]) -> float:
    """
    Парсит временную метку в секунды.

    Поддерживаемые форматы:
    - 45 -> 45.0 секунд
    - 1:30 -> 90.0 секунд (1 минута 30 секунд)
    - 1:2:30 -> 3750.0 секунд (1 час 2 минуты 30 секунд)
    - 1:2:30:500 -> 3750.5 секунд (+ 500 миллисекунд)

    Args:
        time_str: Строка времени или число

    Returns:
        float: Время в секундах

    Raises:
        ValueError: Если формат времени неверный

    Examples:
        >>> parse_time("45")
        45.0
        >>> parse_time("1:30")
        90.0
        >>> parse_time("1:0:0")
        3600.0
    """
    time_str = str(time_str).strip()

    # Простой числовой формат
    if ":" not in time_str:
        return float(time_str)

    # Разбиваем по двоеточию
    parts = list(map(float, time_str.split(":")))

    # Обработка разных форматов
    if len(parts) == 2:
        # MM:SS -> минуты * 60 + секунды
        return parts[0] * 60 + parts[1]

    elif len(parts) == 3:
        # HH:MM:SS -> часы * 3600 + минуты * 60 + секунды
        return parts[0] * 3600 + parts[1] * 60 + parts[2]

    elif len(parts) == 4:
        # HH:MM:SS:MSS -> + миллисекунды / 1000
        return parts[0] * 3600 + parts[1] * 60 + parts[2] + parts[3] / 1000

    else:
        raise ValueError(
            f"Неверный формат времени: {time_str}. "
            f"Ожидается: секунды, MM:SS, HH:MM:SS или HH:MM:SS:MSS"
        )


def normalize_text_simple(text: str) -> str:
    """
    Простая нормализация текста.

    Выполняет:
    - Приведение к нижнему регистру
    - Удаление множественных пробелов
    - Удаление начальных/конечных пробелов

    Args:
        text: Исходный текст

    Returns:
        str: Нормализованный текст

    Example:
        >>> normalize_text_simple("  Привет   Мир  ")
        "привет мир"
    """
    # Удаляем множественные пробелы и приводим к нижнему регистру
    normalized = re.sub(r"\\s+", " ", text.strip().lower())
    return normalized


def format_time(seconds: float) -> str:
    """
    Форматирует секунды в читаемый формат HH:MM:SS.

    Args:
        seconds: Время в секундах

    Returns:
        str: Форматированное время

    Example:
        >>> format_time(3661)
        "01:01:01"
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def validate_time_range(start: float, end: float, max_duration: float = None) -> bool:
    """
    Валидирует временной диапазон.

    Args:
        start: Время начала
        end: Время конца
        max_duration: Максимальная допустимая длительность (опционально)

    Returns:
        bool: True если диапазон валиден
    """
    if start < 0:
        return False

    if end <= start:
        return False

    if max_duration is not None and end > max_duration:
        return False

    return True
