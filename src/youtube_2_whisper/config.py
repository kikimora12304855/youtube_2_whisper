import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import NoReturn


class ConfigPaths:
    """Класс для управления путями к конфигурационным файлам."""

    APP_NAME: str = "youtube-2-whisper"

    @classmethod
    def get_env_paths(cls) -> list[Path]:
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

    def __init__(self) -> None:
        """Инициализация менеджера конфигурации."""
        self.whisper_api_url: str = ""
        self.whisper_api_key: str = ""
        self.whisper_model_name: str = "stt"
        self.llm_model_name: str = "llm"  # Для будущей интеграции LLM
        self.llm_enabled: bool = False  # Флаг включения LLM нормализации
        self.llm_temperature: float = 0.3
        self.llm_top_k: int = 40
        self.llm_top_p: float = 0.9

    def create_interactive_config(self) -> None:
        """
        Создает конфигурационный файл через интерактивный диалог.

        Запрашивает у пользователя:
        - URL Whisper API
        - API ключ
        - Имя модели (опционально)
        """
        config_path: Path = ConfigPaths.get_default_config_path()
        config_path.parent.mkdir(parents=True, exist_ok=True)

        print("\n🔧 Первая настройка youtube-2-whisper")
        print("=" * 60)

        # Основные параметры Whisper
        url: str = input("Введите WHISPER_API_URL: ").strip()
        key: str = input("Введите WHISPER_API_KEY: ").strip()
        model: str = input("Введите WHISPER_MODEL_NAME [stt]: ").strip() or "stt"

        # Параметры LLM (опционально)
        print("\n--- Настройки LLM нормализации (опционально) ---")
        llm_enabled: str = (
            input("Включить LLM нормализацию текста? (y/n) [n]: ").strip().lower()
        )

        with open(config_path, "w", encoding="utf-8") as f:
            _ = f.write(f"WHISPER_API_URL={url}\n")
            _ = f.write(f"WHISPER_API_KEY={key}\n")
            _ = f.write(f"WHISPER_MODEL_NAME={model}\n")

            if llm_enabled in ["y", "yes", "д", "да"]:
                llm_model: str = input("Введите LLM_MODEL_NAME [llm]: ").strip() or "llm"
                _ = f.write("LLM_ENABLED=true\n")
                _ = f.write(f"LLM_MODEL_NAME={llm_model}\n")

        print(f"\n✅ Конфиг сохранен: {config_path}")
        _ = load_dotenv(config_path)

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
        env_loaded: bool = False
        loaded_path: Path | None = None

        # Ищем .env файл
        for env_path in ConfigPaths.get_env_paths():
            if env_path.exists():
                _ = load_dotenv(env_path, override=False)
                env_loaded = True
                loaded_path = env_path
                break

        # Загружаем переменные
        whisper_url: str | None = os.getenv("WHISPER_API_URL")
        whisper_key: str | None = os.getenv("WHISPER_API_KEY")

        # Валидация обязательных параметров
        if not whisper_url or not whisper_key:
            self._handle_missing_config(env_loaded)

        self.whisper_api_url = whisper_url
        self.whisper_api_key = whisper_key
        self.whisper_model_name = os.getenv("WHISPER_MODEL_NAME", "stt")
        self.llm_model_name = os.getenv("LLM_MODEL_NAME", "llm")
        self.llm_enabled = os.getenv("LLM_ENABLED", "false").lower() in [
            "true",
            "1",
            "yes",
        ]
        self.llm_temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        self.llm_top_p = float(os.getenv("LLM_TOP_P", "0.9"))

        # Вывод информации о загруженной конфигурации
        if loaded_path:
            print(f"✅ Загружен конфиг: {loaded_path}")
        else:
            print("✅ Используются системные переменные окружения")

        if self.llm_enabled:
            print(f"🤖 LLM нормализация: включена (модель: {self.llm_model_name})")

    def _handle_missing_config(self, env_loaded: bool) -> NoReturn:
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
            choice: str = input("\n❓ Хотите создать конфиг сейчас? (y/n): ").strip().lower()
            if choice in ["y", "yes", "д", "да"]:
                self.create_interactive_config()
                self.load()  # Перезагружаем конфиг
        except (KeyboardInterrupt, EOFError):
            print("\n")

        sys.exit(1)


# Глобальный экземпляр менеджера конфигурации
config: ConfigManager = ConfigManager()
