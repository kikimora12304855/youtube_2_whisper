import sys
from pathlib import Path
from typing import List, Optional
from dotenv import load_dotenv
import os


class ConfigPaths:
    """Класс для управления путями к конфигурационным файлам."""

    APP_NAME = "youtube-2-whisper"

    @classmethod
    def get_env_paths(cls) -> List[Path]:
        """
        Возвращает список путей для поиска .env файла в порядке приоритета.

        Returns:
            List[Path]: Список путей в порядке убывания приоритета
        """
        return [
            Path.cwd() / ".env",  # Текущая директория (высший приоритет)
            Path.home() / f".{cls.APP_NAME}" / ".env",  # ~/.youtube-2-whisper/.env
            Path.home() / ".config" / cls.APP_NAME / ".env",  # XDG стандарт
        ]

    @classmethod
    def get_default_config_path(cls) -> Path:
        """Возвращает путь для создания нового конфига по умолчанию."""
        return Path.home() / ".config" / cls.APP_NAME / ".env"


class ConfigManager:
    """Менеджер конфигурации приложения."""

    def __init__(self):
        """Инициализация менеджера конфигурации."""
        self.whisper_api_url: Optional[str] = None
        self.whisper_api_key: Optional[str] = None
        self.whisper_model_name: str = "stt"
        self.llm_model_name: str = "llm"  # Для будущей интеграции LLM
        self.llm_enabled: bool = False  # Флаг включения LLM нормализации

    def create_interactive_config(self) -> None:
        """
        Создает конфигурационный файл через интерактивный диалог.

        Запрашивает у пользователя:
        - URL Whisper API
        - API ключ
        - Имя модели (опционально)
        """
        config_path = ConfigPaths.get_default_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        print("\n🔧 Первая настройка youtube-2-whisper")
        print("=" * 60)

        # Основные параметры Whisper
        url = input("Введите WHISPER_API_URL: ").strip()
        key = input("Введите WHISPER_API_KEY: ").strip()
        model = input("Введите WHISPER_MODEL_NAME [stt]: ").strip() or "stt"

        # Параметры LLM (опционально)
        print("\n--- Настройки LLM нормализации (опционально) ---")
        llm_enabled = (
            input("Включить LLM нормализацию текста? (y/n) [n]: ").strip().lower()
        )

        with open(config_path, "w", encoding="utf-8") as f:
            f.write(f"WHISPER_API_URL={url}\n")
            f.write(f"WHISPER_API_KEY={key}\n")
            f.write(f"WHISPER_MODEL_NAME={model}\n")

            if llm_enabled in ["y", "yes", "д", "да"]:
                llm_model = input("Введите LLM_MODEL_NAME [llm]: ").strip() or "llm"
                f.write(f"LLM_ENABLED=true\n")
                f.write(f"LLM_MODEL_NAME={llm_model}\n")

        print(f"\n✅ Конфиг сохранен: {config_path}")
        load_dotenv(config_path)

    def load(self) -> None:
        """
        Загружает конфигурацию из .env файлов или системных переменных.

        Порядок приоритета:
        1. Системные переменные окружения
        2. .env в текущей директории
        3. ~/.youtube-2-whisper/.env
        4. ~/.config/youtube-2-whisper/.env

        Raises:
            SystemExit: Если обязательные параметры не найдены
        """
        env_loaded = False
        loaded_path = None

        # Ищем .env файл
        for env_path in ConfigPaths.get_env_paths():
            if env_path.exists():
                load_dotenv(env_path, override=False)
                env_loaded = True
                loaded_path = env_path
                break

        # Загружаем переменные
        self.whisper_api_url = os.getenv("WHISPER_API_URL")
        self.whisper_api_key = os.getenv("WHISPER_API_KEY")
        self.whisper_model_name = os.getenv("WHISPER_MODEL_NAME", "stt")
        self.llm_model_name = os.getenv("LLM_MODEL_NAME", "llm")
        self.llm_enabled = os.getenv("LLM_ENABLED", "false").lower() in [
            "true",
            "1",
            "yes",
        ]

        # Валидация обязательных параметров
        if not self.whisper_api_url or not self.whisper_api_key:
            self._handle_missing_config(env_loaded)
            return

        # Вывод информации о загруженной конфигурации
        if loaded_path:
            print(f"✅ Загружен конфиг: {loaded_path}")
        else:
            print("✅ Используются системные переменные окружения")

        if self.llm_enabled:
            print(f"🤖 LLM нормализация: включена (модель: {self.llm_model_name})")

    def _handle_missing_config(self, env_loaded: bool) -> None:
        """
        Обрабатывает ситуацию отсутствия конфигурации.

        Args:
            env_loaded: Был ли загружен какой-либо .env файл
        """
        if not env_loaded:
            print("\n⚠️  Файл .env не найден. Искал в:")
            for path in ConfigPaths.get_env_paths():
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
                self.create_interactive_config()
                self.load()  # Перезагружаем конфиг
                return
        except (KeyboardInterrupt, EOFError):
            print("\n")

        sys.exit(1)


# Глобальный экземпляр менеджера конфигурации
config = ConfigManager()
