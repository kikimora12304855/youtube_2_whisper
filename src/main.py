import sys
import os
import json
import re
import hashlib
import argparse
from pathlib import Path
from typing import Optional, Dict, Any
import yt_dlp
from openai import OpenAI
from yt_dlp.utils import download_range_func
from dotenv import load_dotenv

# --- КОНФИГУРАЦИЯ ПУТЕЙ ---
APP_NAME = "youtube-2-whisper"

ENV_PATHS = [
    Path.cwd() / ".env",  # 1. Текущая директория (высший приоритет)
    Path.home() / f".{APP_NAME}" / ".env",  # 2. ~/.youtube-2-whisper/.env
    Path.home()
    / ".config"
    / APP_NAME
    / ".env",  # 3. ~/.config/youtube-2-whisper/.env (XDG)
]


def create_default_config():
    """Создает конфигурационный файл с помощью интерактивного диалога."""
    config_dir = Path.home() / ".config" / APP_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / ".env"

    print("\n🔧 Первая настройка youtube-2-whisper")
    print("=" * 50)
    url = input("Введите WHISPER_API_URL: ").strip()
    key = input("Введите WHISPER_API_KEY: ").strip()
    model = input("Введите WHISPER_MODEL_NAME [stt]: ").strip() or "stt"

    with open(config_file, "w") as f:
        f.write(f"WHISPER_API_URL={url}\n")
        f.write(f"WHISPER_API_KEY={key}\n")
        f.write(f"WHISPER_MODEL_NAME={model}\n")

    print(f"\n✅ Конфиг сохранен: {config_file}")
    load_dotenv(config_file)


def load_config():
    """Загружает конфигурацию из .env файлов или системных переменных."""
    env_loaded = False

    for env_path in ENV_PATHS:
        if env_path.exists():
            load_dotenv(
                env_path, override=False
            )  # Не перезаписываем системные переменные
            print(f"✅ Загружен конфиг: {env_path}")
            env_loaded = True
            break

    # Проверяем наличие обязательных переменных
    whisper_url = os.getenv("WHISPER_API_URL")
    api_key = os.getenv("WHISPER_API_KEY")

    if not whisper_url or not api_key:
        if not env_loaded:
            print("\n⚠️  Файл .env не найден. Искал в:")
            for path in ENV_PATHS:
                print(f"    - {path}")

        print("\n❌ Ошибка: Не указаны WHISPER_API_URL и/или WHISPER_API_KEY")
        print("\n📋 Варианты решения:")
        print("1. Создайте .env файл в текущей директории")
        print("2. Создайте ~/.config/youtube-2-whisper/.env")
        print("3. Установите системные переменные:")
        print("   export WHISPER_API_URL='your_url'")
        print("   export WHISPER_API_KEY='your_key'")

        # Предлагаем создать конфиг
        try:
            choice = input("\n❓ Хотите создать конфиг сейчас? (y/n): ").strip().lower()
            if choice in ["y", "yes", "д", "да"]:
                create_default_config()
                return
        except (KeyboardInterrupt, EOFError):
            print("\n")

        sys.exit(1)

    if not env_loaded:
        # Переменные найдены в системном окружении
        print("✅ Используются системные переменные окружения")


# --- ЗАГРУЗКА КОНФИГУРАЦИИ ---
load_config()

# --- КОНСТАНТЫ ИЗ .ENV ---
WHISPER_API_URL = os.getenv("WHISPER_API_URL")
API_KEY = os.getenv("WHISPER_API_KEY")
MODEL_NAME = os.getenv("WHISPER_MODEL_NAME", "stt")

MAX_FILENAME_LENGTH = 200
DEFAULT_VOICE_DESC = (
    "Голос: unknown, unknown, телосложение: unknown; "
    "тембр — яркость: unknown, шероховатость: unknown, придыхательность: unknown."
)

# Общие параметры постобработки аудио
COMMON_POSTPROCESSOR_ARGS = [
    "-ar",
    "24000",
    "-ac",
    "1",
    "-af",
    "loudnorm=I=-16:TP=-1.5:LRA=11,aformat=sample_fmts=s16:channel_layouts=mono",
    "-compression_level",
    "12",
]

# Инициализация клиента
client = OpenAI(api_key=API_KEY, base_url=WHISPER_API_URL)


def sanitize_filename(filename: str) -> str:
    """Удаляет или заменяет недопустимые символы в имени файла."""
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename).strip()
    return (
        filename[:MAX_FILENAME_LENGTH]
        if len(filename) > MAX_FILENAME_LENGTH
        else filename
    )


def parse_time(time_str: str) -> float:
    """Парсит время в секунды. Форматы: 45, 1:30, 1:2:30, 1:2:30:500"""
    time_str = str(time_str).strip()

    if ":" not in time_str:
        return float(time_str)

    parts = list(map(float, time_str.split(":")))

    time_calculations = {
        2: lambda p: p[0] * 60 + p[1],
        3: lambda p: p[0] * 3600 + p[1] * 60 + p[2],
        4: lambda p: p[0] * 3600 + p[1] * 60 + p[2] + p[3] / 1000,
    }

    if len(parts) in time_calculations:
        return time_calculations[len(parts)](parts)

    raise ValueError(f"Неверный формат времени: {time_str}")


def normalize_text(text: str) -> str:
    """Простая нормализация текста."""
    return re.sub(r"\s+", " ", text.strip().lower())


def make_hash_id(video_id: str, start_time: float, end_time: float) -> str:
    """Создает SHA256 хеш для уникального ID сегмента."""
    return hashlib.sha256(
        f"{video_id}:{start_time}:{end_time}".encode("utf-8")
    ).hexdigest()


def get_video_info(video_url: str) -> Dict[str, Any]:
    """Получает информацию о видео."""
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        info = ydl.extract_info(video_url, download=False)

        video_id = sanitize_filename(info["id"])
        speaker_source_id = (
            info.get("channel_id") or info.get("uploader_id") or video_id
        )

        return {
            "video_id": video_id,
            "duration": info.get("duration", 0),
            "speaker_id": speaker_source_id,
            "channel_name": info.get("channel", "unknown"),
        }


def get_ydl_options(
    filename_base: str,
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
) -> Dict[str, Any]:
    """Формирует параметры для yt-dlp."""
    opts = {
        "format": "bestaudio/best",
        "outtmpl": filename_base,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "flac",
            }
        ],
        "postprocessor_args": COMMON_POSTPROCESSOR_ARGS,
        "quiet": True,
        "no_warnings": True,
    }

    if start_time is not None and end_time is not None:
        opts["download_ranges"] = download_range_func(None, [(start_time, end_time)])
        opts["force_keyframes_at_cuts"] = True
    else:
        opts["extractor_args"] = {"youtube": {"player_client": ["android", "web"]}}

    return opts


def download_audio(
    video_url: str, ydl_opts: Dict[str, Any], filename_flac: str
) -> bool:
    """Скачивает аудио и возвращает успешность операции."""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
        return Path(filename_flac).exists()
    except Exception as e:
        print(f"❌ Ошибка скачивания: {e}")
        return False


def transcribe_audio(filename_flac: str) -> Optional[str]:
    """Отправляет аудио на Whisper и возвращает транскрипцию."""
    try:
        with open(filename_flac, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model=MODEL_NAME, file=audio_file, response_format="json"
            )
        return transcription.text
    except Exception as e:
        print(f"❌ Ошибка транскрипции: {e}")
        return None


def create_result_json(
    video_id: str,
    start_time: float,
    end_time: float,
    raw_text: str,
    speaker_id: str,
    lang: str,
    source_type: str,
    voice_desc: str,
) -> Dict[str, Any]:
    """Формирует JSON результата."""
    return {
        "id": make_hash_id(video_id, start_time, end_time),
        "lang": lang,
        "text": {
            "raw": raw_text,
            "normalized": normalize_text(raw_text),
        },
        "source": {
            "type": source_type,
            "id": video_id,
            "segment_sec": {
                "start": start_time,
                "end": end_time,
                "duration_sec": end_time - start_time,
            },
        },
        "speaker": {
            "id": speaker_id,
            "voice_description": voice_desc or DEFAULT_VOICE_DESC,
        },
    }


def process_video_segment(
    video_url: str,
    start_str: Optional[str] = None,
    end_str: Optional[str] = None,
    lang: str = "ru-RU",
    source_type: str = "youtube",
    voice_desc: Optional[str] = None,
    output_dir: str = ".",
) -> None:
    """Основная функция обработки видео."""

    print("🔍 Получаю информацию о видео...")
    try:
        info = get_video_info(video_url)
        print(f"📺 Канал: {info['channel_name']} (ID: {info['speaker_id']})")
    except Exception as e:
        print(f"❌ Не удалось получить информацию о видео: {e}")
        return

    is_full_video = start_str is None or end_str is None
    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)

    if is_full_video:
        print(f"📹 Режим: скачивание всего видео (длительность: {info['duration']}s)")
        filename_base = info["video_id"]
        start_time, end_time = 0, info["duration"]
    else:
        start_time = parse_time(start_str)
        end_time = parse_time(end_str)

        if start_time >= end_time:
            print("❌ Ошибка: Время начала должно быть меньше времени конца")
            return

        print(f"✂️  Режим: скачивание фрагмента [{start_str} - {end_str}]")
        filename_base = f"{info['video_id']}_{sanitize_filename(start_str)}_{sanitize_filename(end_str)}"

    filename_full_path = str(output_path / filename_base)
    filename_flac = str(output_path / f"{filename_base}.flac")
    filename_json = str(output_path / f"{filename_base}.json")

    print(f"⏳ Скачиваю: {filename_flac} (24kHz моно, нормализация)...")
    ydl_opts = get_ydl_options(
        filename_full_path,
        None if is_full_video else start_time,
        None if is_full_video else end_time,
    )

    if not download_audio(video_url, ydl_opts, filename_flac):
        print(f"❌ Файл {filename_flac} не создался")
        return

    print("🚀 Отправляю на Whisper сервер...")
    raw_text = transcribe_audio(filename_flac)
    if not raw_text:
        return

    result = create_result_json(
        info["video_id"],
        start_time,
        end_time,
        raw_text,
        info["speaker_id"],
        lang,
        source_type,
        voice_desc,
    )

    with open(filename_json, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("\n✅ РЕЗУЛЬТАТ:")
    print("------------------------------------------------")
    print(raw_text)
    print("------------------------------------------------")
    print(f"💾 Сохранено в: {filename_json}")
    print(f"🎤 Speaker ID: {info['speaker_id']}")


def main():
    """Точка входа в программу."""
    parser = argparse.ArgumentParser(
        description="Скачивание и транскрипция видео/аудио с YouTube",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("url", help="URL видео (YouTube и т.д.)")
    parser.add_argument(
        "start",
        nargs="?",
        default=None,
        help="Время начала (опционально): 45, 1:30, 1:2:30",
    )
    parser.add_argument(
        "end", nargs="?", default=None, help="Время конца (опционально)"
    )
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
        choices=["youtube", "podcast", "audiobook", "dataset"],
        help="Тип источника (по умолчанию: youtube)",
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

    args = parser.parse_args()

    try:
        process_video_segment(
            video_url=args.url,
            start_str=args.start,
            end_str=args.end,
            lang=args.lang,
            source_type=args.type,
            voice_desc=args.description,
            output_dir=args.output_dir,
        )
    except ValueError as e:
        print(f"❌ Ошибка парсинга времени: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
