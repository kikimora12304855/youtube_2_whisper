from pathlib import Path
from typing import Optional, Dict, Any
import yt_dlp
from yt_dlp.utils import download_range_func

from models import VideoInfo, TimeSegment
from utils import sanitize_filename


class AudioDownloader:
    """Класс для загрузки и обработки аудио с видео платформ."""

    # Параметры постобработки аудио для оптимального качества транскрипции
    AUDIO_POSTPROCESSOR_ARGS = [
        "-ar",
        "24000",  # Sample rate 24kHz (оптимально для речи)
        "-ac",
        "1",  # Моно канал
        "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=11,aformat=sample_fmts=s16:channel_layouts=mono",  # Нормализация громкости
        "-compression_level",
        "12",  # Максимальное сжатие FLAC
    ]

    def __init__(self, quiet: bool = True):
        """
        Инициализация загрузчика.

        Args:
            quiet: Подавлять вывод yt-dlp
        """
        self.quiet = quiet

    def get_video_info(self, video_url: str) -> VideoInfo:
        """
        Получает метаданные видео без загрузки.

        Args:
            video_url: URL видео

        Returns:
            VideoInfo: Объект с информацией о видео

        Raises:
            Exception: При ошибке получения информации
        """
        ydl_opts = {"quiet": self.quiet, "no_warnings": True}

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)

            # Санитизация ID видео
            video_id = sanitize_filename(info["id"])

            # Определяем speaker_id из channel_id или uploader_id
            speaker_id = info.get("channel_id") or info.get("uploader_id") or video_id

            return VideoInfo(
                video_id=video_id,
                duration=info.get("duration", 0),
                speaker_id=speaker_id,
                channel_name=info.get("channel", "unknown"),
            )

    def download_audio(
        self, video_url: str, output_path: Path, segment: Optional[TimeSegment] = None
    ) -> Path:
        """
        Загружает аудио из видео и конвертирует в FLAC.

        Args:
            video_url: URL видео
            output_path: Путь для сохранения (без расширения)
            segment: Временной сегмент для загрузки (None = полное видео)

        Returns:
            Path: Путь к созданному FLAC файлу

        Raises:
            Exception: При ошибке загрузки
        """
        ydl_opts = self._build_ydl_options(output_path, segment)

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])

        # Проверяем создание файла
        flac_file = output_path.with_suffix(".flac")
        if not flac_file.exists():
            raise FileNotFoundError(f"FLAC файл не был создан: {flac_file}")

        return flac_file

    def _build_ydl_options(
        self, output_path: Path, segment: Optional[TimeSegment] = None
    ) -> Dict[str, Any]:
        """
        Формирует параметры для yt-dlp.

        Args:
            output_path: Путь для сохранения
            segment: Временной сегмент (опционально)

        Returns:
            Dict: Конфигурация yt-dlp
        """
        opts = {
            "format": "bestaudio/best",  # Лучшее качество аудио
            "outtmpl": str(output_path),
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "flac",  # Без потерь для транскрипции
                }
            ],
            "postprocessor_args": self.AUDIO_POSTPROCESSOR_ARGS,
            "quiet": self.quiet,
            "no_warnings": True,
        }

        # Если указан сегмент - загружаем только его
        if segment is not None:
            opts["download_ranges"] = download_range_func(
                None, [(segment.start, segment.end)]
            )
            opts["force_keyframes_at_cuts"] = True
        else:
            # Для полного видео используем альтернативные клиенты
            opts["extractor_args"] = {"youtube": {"player_client": ["android", "web"]}}

        return opts

    @staticmethod
    def generate_filename(
        video_info: VideoInfo,
        segment: Optional[TimeSegment] = None,
        start_str: Optional[str] = None,
        end_str: Optional[str] = None,
    ) -> str:
        """
        Генерирует имя файла на основе видео и сегмента.

        Args:
            video_info: Информация о видео
            segment: Временной сегмент
            start_str: Строка начала (для имени файла)
            end_str: Строка конца (для имени файла)

        Returns:
            str: Имя файла без расширения
        """
        if segment is None or (start_str is None and end_str is None):
            # Полное видео
            return video_info.video_id

        # Сегмент видео
        start_safe = sanitize_filename(start_str or str(segment.start))
        end_safe = sanitize_filename(end_str or str(segment.end))

        return f"{video_info.video_id}_{start_safe}_{end_safe}"
