"""
Главный модуль приложения youtube-2-whisper.

Точка входа в программу с CLI интерфейсом.
"""

import sys
import argparse
from pathlib import Path

from config import config
from youtube_downloader import AudioDownloader
from whisper_client import WhisperClient, LLMNormalizer, TranscriptionService
from whisper_client import PODCAST_PROMPT, AUDIOBOOK_PROMPT, LECTURE_PROMPT
from processor import VideoProcessor


def create_parser() -> argparse.ArgumentParser:
    """
    Создает парсер аргументов командной строки.

    Returns:
        argparse.ArgumentParser: Настроенный парсер
    """
    parser = argparse.ArgumentParser(
        description="🎙️  youtube-2-whisper - Транскрипция видео через Whisper API",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Примеры использования:

  # Полное видео
  python main.py "https://youtube.com/watch?v=VIDEO_ID"

  # Фрагмент видео (с 1:30 до 5:45)
  python main.py "https://youtube.com/watch?v=VIDEO_ID" 1:30 5:45

  # С описанием голоса и типом источника
  python main.py "URL" --type podcast --description "Мужской голос, низкий тембр"

  # С LLM нормализацией (если включена в .env)
  python main.py "URL" --llm-prompt podcast

  # Сохранение в определенную директорию
  python main.py "URL" -o /path/to/output
        """,
    )

    # Обязательные аргументы
    parser.add_argument(
        "url", help="URL видео (YouTube, и другие платформы поддерживаемые yt-dlp)"
    )

    parser.add_argument(
        "start",
        nargs="?",
        default=None,
        help="Время начала фрагмента (опционально)\nФорматы: 45, 1:30, 1:2:30, 1:2:30:500",
    )

    parser.add_argument(
        "end", nargs="?", default=None, help="Время конца фрагмента (опционально)"
    )

    # Опциональные параметры
    parser.add_argument(
        "-l",
        "--lang",
        type=str,
        default="ru-RU",
        help="Язык аудио (по умолчанию: ru-RU)",
    )

    parser.add_argument(
        "-t",
        "--type",
        type=str,
        default="youtube",
        choices=["youtube", "podcast", "audiobook", "dataset", "lecture"],
        help="Тип источника аудио (по умолчанию: youtube)",
    )

    parser.add_argument(
        "-d", "--description", type=str, default=None, help="Описание голоса говорящего"
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        type=str,
        default=".",
        help="Директория для сохранения файлов (по умолчанию: текущая)",
    )

    # Параметры LLM нормализации
    parser.add_argument(
        "--llm-prompt",
        type=str,
        choices=["default", "podcast", "audiobook", "lecture", "custom"],
        default=None,
        help="Тип промпта для LLM нормализации (требует LLM_ENABLED=true в .env)",
    )

    parser.add_argument(
        "--llm-custom-prompt",
        type=str,
        default=None,
        help="Кастомный системный промпт для LLM (используется с --llm-prompt custom)",
    )

    parser.add_argument(
        "--disable-llm",
        action="store_true",
        help="Отключить LLM нормализацию даже если включена в конфиге",
    )

    return parser


def setup_llm_normalizer(args: argparse.Namespace) -> LLMNormalizer:
    """
    Настраивает LLM нормализатор на основе аргументов.

    Args:
        args: Аргументы командной строки

    Returns:
        Optional[LLMNormalizer]: Настроенный нормализатор или None
    """
    # Проверяем что LLM включен
    if args.disable_llm or not config.llm_enabled:
        return None

    # Определяем промпт
    prompt_map = {
        "podcast": PODCAST_PROMPT,
        "audiobook": AUDIOBOOK_PROMPT,
        "lecture": LECTURE_PROMPT,
        "custom": args.llm_custom_prompt,
        "default": None,  # Использует DEFAULT_SYSTEM_PROMPT
    }

    system_prompt = None
    if args.llm_prompt:
        system_prompt = prompt_map.get(args.llm_prompt)

        if args.llm_prompt == "custom" and not args.llm_custom_prompt:
            print("⚠️  --llm-prompt custom требует --llm-custom-prompt")
            return None

    # Создаем нормализатор
    normalizer = LLMNormalizer(
        api_url=config.whisper_api_url,
        api_key=config.whisper_api_key,
        model_name=config.llm_model_name,
        system_prompt=system_prompt,
    )

    return normalizer


def main():
    """Точка входа в программу."""

    # Загрузка конфигурации
    config.load()

    # Парсинг аргументов
    parser = create_parser()
    args = parser.parse_args()

    # Вывод информации о запуске
    print("\n" + "=" * 60)
    print("🎙️  youtube-2-whisper")
    print("=" * 60)
    print(f"📍 URL: {args.url}")
    if args.start and args.end:
        print(f"⏱️  Сегмент: {args.start} → {args.end}")
    print(f"🌍 Язык: {args.lang}")
    print(f"📁 Выходная директория: {args.output_dir}")
    print("=" * 60 + "\n")

    # Инициализация компонентов
    try:
        # Загрузчик аудио
        downloader = AudioDownloader(quiet=True)

        # Whisper клиент
        whisper = WhisperClient(
            api_url=config.whisper_api_url,
            api_key=config.whisper_api_key,
            model_name=config.whisper_model_name,
        )

        # LLM нормализатор (опционально)
        llm = setup_llm_normalizer(args)

        # Сервис транскрипции
        transcription_service = TranscriptionService(
            whisper_client=whisper, llm_normalizer=llm
        )

        # Процессор
        processor = VideoProcessor(
            downloader=downloader,
            transcription_service=transcription_service,
            output_dir=Path(args.output_dir),
        )

    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        sys.exit(1)

    # Обработка видео
    try:
        result_path = processor.process(
            video_url=args.url,
            start_str=args.start,
            end_str=args.end,
            lang=args.lang,
            source_type=args.type,
            voice_desc=args.description,
        )

        if result_path is None:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Прервано пользователем")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
