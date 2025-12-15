```html
<div align="center">
  <a href="README_RU.md">
    🇷🇺 Русская версия
  </a>
</div>
<br>
```


# YouTube-2-Whisper 🎙️

**YouTube-2-Whisper** is a CLI tool for automating dataset creation and transcription workflows. The script downloads audio from YouTube (or other platforms), processes it (loudness normalization, conversion to 24kHz FLAC), and sends it for transcription via an OpenAI-compatible API (e.g., local Whisper, OpenAI API, or runpod).

## ✨ Features

*   📥 **Downloading:** Support for YouTube and other video hosting services via `yt-dlp`.
*   ✂️ **Segmentation:** Ability to download entire videos or precise time segments.
*   🎚️ **Audio Processing:** Automatic loudness normalization (Loudnorm) and conversion to mono FLAC (24kHz) for perfect compatibility with training models (e.g., VITS/Bert-VITS).
*   🤖 **Interactive Setup:** First-run wizard to generate the configuration file.
*   📄 **Metadata:** Generates detailed JSON containing speaker info, timings, raw text, and normalized text.
*   🆔 **Uniqueness:** Generates a SHA256 hash for each segment to prevent duplicates.

## ⚙️ Requirements

To run the script, you need to install:

1.  **uv**
2.  **FFmpeg** (must be installed on the system and available via the PATH variable).

### Installing Dependencies

#### Installing uv
This script automatically downloads the required `uv` binary and adds it to your path.
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Installing FFmpeg
Installation for Ubuntu
```bash
sudo apt update
sudo apt install ffmpeg
```

Installation for Arch
```bash
sudo pacman -Syu
sudo pacman -S ffmpeg
```

### Installation
```bash
git clone https://github.com/kikimora12304855/youtube_2_whisper.git

cd youtube-2-whisper

uv tool install .
```

## 🚀 Configuration

On the first run, the script will automatically prompt you to enter the necessary data and create a `.env` configuration file.

You can also manually create a `.env` file in one of the following directories:
1. In the script's current folder.
2. `~/.config/youtube-2-whisper/.env`
3. `~/.youtube-2-whisper/.env`

**`.env` file format:**

```ini
WHISPER_API_URL=http://localhost:8000/v1
WHISPER_API_KEY=sk-12345  # If using a local server, you can enter any string
WHISPER_MODEL_NAME=large-v3
```

## 📖 Usage

Run the tool via the command line.

### Syntax

```bash
youtube-2-whisper URL [START] [END] [OPTIONS]
```

### Arguments

*   `URL`: Video link (required).
*   `START`: Segment start time (optional). Formats: `45` (sec), `1:30` (min:sec), `1:20:05` (h:m:s).
*   `END`: Segment end time (optional).

### Options (Flags)

*   `-l`, `--lang`: Audio language (default: `ru-RU`).
*   `-t`, `--type`: Source type (`youtube`, `podcast`, `audiobook`, `dataset`).
*   `-d`, `--description`: Text description of the voice (for TTS datasets).
*   `-o`, `--output-dir`: Folder to save results.

***

### Examples

**1. Download and transcribe the entire video:**
```bash
youtube-2-whisper "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
```

**2. Download a fragment from the 1st to the 3rd minute:**
```bash
youtube-2-whisper "https://www.youtube.com/watch?v=dQw4w9WgXcQ" 1:00 3:00
```

**3. Download a fragment specifying a folder and voice description:**
```bash
youtube-2-whisper "https://youtu.be/example" 10 25 \
  -o ./my_dataset \
  -d "Female voice, calm timbre, audiobook"
```

## 📂 Output Format

The script generates two files for each run:
1.  `filename.flac` — processed audio.
2.  `filename.json` — metadata and text.

**JSON Example:**

```json
{
  "id": "a1b2c3d4...", // SHA256 hash (VideoID + Start + End)
  "lang": "ru-RU",
  "text": {
    "raw": "Привет, мир! Это тестовая запись.",
    "normalized": "привет мир это тестовая запись"
  },
  "source": {
    "type": "youtube",
    "id": "dQw4w9WgXcQ",
    "segment_sec": {
      "start": 60.0,
      "end": 180.0,
      "duration_sec": 120.0
    }
  },
  "speaker": {
    "id": "UCuAXFkgsw1L7xaCfnd5JJOw", // Channel or Author ID
    "voice_description": "Voice: unknown..." // Your description
  }
}
```

## 🛠 Troubleshooting

**Error: `WHISPER_API_URL not specified`**
The script could not find the `.env` file. Run the script, and it will offer to create one, or set the environment variables manually:
```bash
export WHISPER_API_URL='...'
export WHISPER_API_KEY='...'
```
or create `.env` in the `~/.youtube-2-whisper/` directory:
```env
WHISPER_API_URL=http://localhost:8000/v1
WHISPER_API_KEY=sk-12345  # If using a local server, any string works
WHISPER_MODEL_NAME=large-v3
```
## 📝 License

- [GPL-3.0 license](https://github.com/kikimora12304855/youtube_2_whisper#GPL-3.0-1-ov-file)
