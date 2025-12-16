from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import hashlib


@dataclass
class VideoInfo:
    """Информация о видео."""

    video_id: str  # Уникальный идентификатор видео
    duration: float  # Длительность в секундах
    speaker_id: str  # ID канала/источника (используется как speaker_id)
    channel_name: str  # Название канала

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь."""
        return asdict(self)


@dataclass
class TimeSegment:
    """Временной сегмент аудио."""

    start: float  # Время начала в секундах
    end: float  # Время конца в секундах

    @property
    def duration(self) -> float:
        """Возвращает длительность сегмента."""
        return self.end - self.start

    def is_valid(self) -> bool:
        """Проверяет валидность временного сегмента."""
        return self.start >= 0 and self.end > self.start

    def to_dict(self) -> Dict[str, float]:
        """Преобразует сегмент в словарь."""
        return {"start": self.start, "end": self.end, "duration_sec": self.duration}


@dataclass
class TranscriptionText:
    """Текст транскрипции в разных форматах."""

    raw: str  # Исходный текст от Whisper
    normalized: Optional[str] = None  # Нормализованный текст (простой или через LLM)

    def to_dict(self) -> Dict[str, str]:
        """Преобразует объект в словарь."""
        return {"raw": self.raw, "normalized": self.normalized or self.raw}


@dataclass
class Speaker:
    """Информация о говорящем."""

    id: str  # Уникальный идентификатор говорящего
    voice_description: str  # Описание голоса

    @staticmethod
    def get_default_description() -> str:
        """Возвращает описание голоса по умолчанию."""
        return (
            "Голос: unknown, unknown, телосложение: unknown; "
            "тембр — яркость: unknown, шероховатость: unknown, придыхательность: unknown."
        )

    def to_dict(self) -> Dict[str, str]:
        """Преобразует объект в словарь."""
        return asdict(self)


@dataclass
class Source:
    """Информация об источнике аудио."""

    type: str  # Тип источника: youtube, podcast, audiobook, dataset
    id: str  # ID источника (video_id)
    segment: TimeSegment  # Временной сегмент

    def to_dict(self) -> Dict[str, Any]:
        """Преобразует объект в словарь."""
        return {"type": self.type, "id": self.id, "segment_sec": self.segment.to_dict()}


@dataclass
class TranscriptionResult:
    """Полный результат транскрипции."""

    id: str  # Уникальный хеш-идентификатор
    lang: str  # Язык аудио
    text: TranscriptionText  # Текст транскрипции
    source: Source  # Информация об источнике
    speaker: Speaker  # Информация о говорящем

    @staticmethod
    def generate_id(video_id: str, start_time: float, end_time: float) -> str:
        """
        Генерирует уникальный ID на основе SHA256 хеша.

        Args:
            video_id: ID видео
            start_time: Время начала сегмента
            end_time: Время конца сегмента

        Returns:
            str: SHA256 хеш строки "{video_id}:{start_time}:{end_time}"
        """
        hash_input = f"{video_id}:{start_time}:{end_time}"
        return hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """
        Преобразует результат в словарь для JSON сериализации.

        Returns:
            Dict: Структурированный словарь с результатами
        """
        return {
            "id": self.id,
            "lang": self.lang,
            "text": self.text.to_dict(),
            "source": self.source.to_dict(),
            "speaker": self.speaker.to_dict(),
        }

    @classmethod
    def create(
        cls,
        video_info: VideoInfo,
        segment: TimeSegment,
        raw_text: str,
        lang: str,
        source_type: str,
        voice_desc: Optional[str] = None,
        normalized_text: Optional[str] = None,
    ) -> "TranscriptionResult":
        """
        Фабричный метод для создания результата транскрипции.

        Args:
            video_info: Информация о видео
            segment: Временной сегмент
            raw_text: Исходный текст транскрипции
            lang: Язык
            source_type: Тип источника
            voice_desc: Описание голоса (опционально)
            normalized_text: Нормализованный текст (опционально)

        Returns:
            TranscriptionResult: Новый объект результата
        """
        result_id = cls.generate_id(video_info.video_id, segment.start, segment.end)

        text = TranscriptionText(raw=raw_text, normalized=normalized_text)

        source = Source(type=source_type, id=video_info.video_id, segment=segment)

        speaker = Speaker(
            id=video_info.speaker_id,
            voice_description=voice_desc or Speaker.get_default_description(),
        )

        return cls(id=result_id, lang=lang, text=text, source=source, speaker=speaker)
