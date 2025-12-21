import json
from pathlib import Path

from youtube_2_whisper.models import VideoInfo, TimeSegment, TranscriptionResult
from youtube_2_whisper.youtube_downloader import AudioDownloader
from youtube_2_whisper.whisper_client import TranscriptionService
from youtube_2_whisper.utils import parse_time, validate_time_range


class VideoProcessor:
    """
    Процессор для обработки видео: загрузка, транскрипция, сохранение.
    """

    def __init__(
        self,
        downloader: AudioDownloader,
        transcription_service: TranscriptionService,
        output_dir: Path,
    ) -> None:
        """
        Инициализация процессора.

        Args:
            downloader: Загрузчик аудио
            transcription_service: Сервис транскрипции
            output_dir: Директория для сохранения результатов
        """
        self.downloader: AudioDownloader = downloader
        self.transcription_service: TranscriptionService = transcription_service
        self.output_dir: Path = output_dir

        # Создаем директорию если не существует
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process(
        self,
        video_url: str,
        start_str: str | None = None,
        end_str: str | None = None,
        lang: str = "ru-RU",
        source_type: str = "youtube",
        voice_desc: str | None = None,
    ) -> Path | None:
        """
        Обрабатывает видео: загрузка аудио, транскрипция, сохранение.

        Args:
            video_url: URL видео
            start_str: Время начала (строка, опционально)
            end_str: Время конца (строка, опционально)
            lang: Язык аудио
            source_type: Тип источника
            voice_desc: Описание голоса

        Returns:
            Path | None: Путь к JSON файлу с результатом или None при ошибке
        """
        # Шаг 1: Получение информации о видео
        print("🔍 Получаю информацию о видео...")
        try:
            video_info: VideoInfo = self.downloader.get_video_info(video_url)
            print(f"📺 Канал: {video_info.channel_name} (ID: {video_info.speaker_id})")
        except Exception as e:
            print(f"❌ Не удалось получить информацию о видео: {e}")
            return None

        # Шаг 2: Определение временного сегмента
        segment, is_full_video = self._parse_time_segment(
            start_str, end_str, video_info
        )

        if segment is None:
            return None

        # Вывод информации о режиме
        if is_full_video:
            print(f"📹 Режим: полное видео (длительность: {video_info.duration:.1f}s)")
        else:
            print(
                f"✂️  Режим: фрагмент [{start_str} - {end_str}] ({segment.duration:.1f}s)"
            )

        # Шаг 3: Формирование путей к файлам
        filename_base: str = AudioDownloader.generate_filename(
            video_info=video_info, segment=None if is_full_video else segment, start_str=start_str, end_str=end_str
        )

        audio_path: Path = self.output_dir / filename_base
        flac_path: Path = self.output_dir / f"{filename_base}.flac"
        json_path: Path = self.output_dir / f"{filename_base}.json"

        # Шаг 4: Загрузка аудио
        print(f"⏳ Скачиваю аудио: {flac_path.name}")
        print("   (24kHz моно, loudnorm, FLAC)")

        try:
           _ = self.downloader.download_audio(
                video_url=video_url, output_path=audio_path, segment=None if is_full_video else segment
            )
        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")
            return None

        # Шаг 5: Транскрипция и нормализация
        try:
            raw_text, normalized_text = self.transcription_service.process(
                audio_file_path=flac_path)
        except Exception as e:
            print(f"❌ Ошибка транскрипции: {e}")
            return None

        # Шаг 6: Формирование и сохранение результата
        result = TranscriptionResult.create(
            video_info=video_info,
            segment=segment,
            raw_text=raw_text,
            lang=lang,
            source_type=source_type,
            voice_desc=voice_desc,
            normalized_text=normalized_text,
        )

        self._save_result(result, json_path)

        # Вывод результата
        self._print_result(raw_text, normalized_text, json_path, video_info.speaker_id)

        return json_path

    def _parse_time_segment(
        self, start_str: str | None, end_str: str | None, video_info: VideoInfo
    ) -> tuple[TimeSegment | None, bool]:
        """
        Парсит временной сегмент из строк.

        Args:
            start_str: Строка времени начала
            end_str: Строка времени конца
            video_info: Информация о видео

        Returns:
            tuple: (TimeSegment, is_full_video) или (None, False) при ошибке
        """
        # Если время не указано - полное видео
        if start_str is None or end_str is None:
            segment = TimeSegment(start=0, end=video_info.duration)
            return segment, True

        # Парсим время
        try:
            start_time: float = parse_time(time_parse_str=start_str)
            end_time: float = parse_time(time_parse_str=end_str)
        except ValueError as e:
            print(f"❌ Ошибка парсинга времени: {e}")
            return None, False

        # Валидация
        if not validate_time_range(start_time, end_time, video_info.duration):
            print(f"❌ Неверный временной диапазон: [{start_time} - {end_time}]")
            print(f"   Длительность видео: {video_info.duration}s")
            return None, False

        segment = TimeSegment(start=start_time, end=end_time)
        return segment, False

    def _save_result(self, result: TranscriptionResult, json_path: Path) -> None:
        """
        Сохраняет результат в JSON файл.

        Args:
            result: Результат транскрипции
            json_path: Путь к JSON файлу
        """
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, ensure_ascii=False, indent=2)

    def _print_result(
        self,
        raw_text: str,
        normalized_text: str | None,
        json_path: Path,
        speaker_id: str,
    ) -> None:
        """
        Выводит результат в консоль.

        Args:
            raw_text: Исходный текст
            normalized_text: Нормализованный текст
            json_path: Путь к JSON
            speaker_id: ID говорящего
        """
        print("\n" + "=" * 60)
        print("✅ РЕЗУЛЬТАТ ТРАНСКРИПЦИИ")
        print("=" * 60)

        print("\n📝 Исходный текст:")
        print("-" * 60)
        print(raw_text)

        if normalized_text and normalized_text != raw_text.lower().strip():
            print("\n✨ Нормализованный текст:")
            print("-" * 60)
            print(normalized_text)

        print("\n" + "=" * 60)
        print(f"💾 Сохранено: {json_path}")
        print(f"🎤 Speaker ID: {speaker_id}")
        print("=" * 60)
