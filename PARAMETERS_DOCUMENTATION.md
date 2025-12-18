# 📚 Parameters and Arguments Documentation

This document provides comprehensive information about all parameters, arguments, and configurations available in the youtube-2-whisper project.

## 📋 Table of Contents

1. [Command-Line Arguments](#command-line-arguments)
2. [Configuration Parameters (.env)](#configuration-parameters-env)
3. [Source Types](#source-types)
4. [LLM Normalization Prompts](#llm-normalization-prompts)
5. [Time Format Specifications](#time-format-specifications)
6. [Usage Examples](#usage-examples)
7. [Output Format](#output-format)
8. [Troubleshooting](#troubleshooting)

## 🎯 Command-Line Arguments

### Main Arguments

#### `URL` (required)
- **Description**: Video link from YouTube or other supported platforms (Vimeo, SoundCloud, etc.)
- **Format**: `https://youtube.com/watch?v=VIDEO_ID` or `VIDEO_ID`
- **Example**: `"https://www.youtube.com/watch?v=dQw4w9WgXcQ"` or `dQw4w9WgXcQ`

#### `START` (optional)
- **Description**: Start time of the segment to download
- **Formats**:
  - `45` (seconds)
  - `45.5` (seconds.milliseconds)
  - `1:30` (minutes:seconds)
  - `1:20:05` (hours:minutes:seconds)
  - `1:20:30:500` (hours:minutes:seconds:milliseconds)
- **Example**: `1:30` (start at 1 minute 30 seconds)

#### `END` (optional)
- **Description**: End time of the segment to download
- **Formats**: same as `START`
- **Example**: `5:45` (end at 5 minutes 45 seconds)

### Optional Flags

#### `-l`, `--lang`
- **Description**: Audio language for transcription
- **Type**: string
- **Default**: `ru-RU`
- **Examples**:
  - `-l en-US` (English)
  - `-l de-DE` (German)
  - `-l fr-FR` (French)

#### `-t`, `--type`
- **Description**: Type of audio source
- **Type**: string
- **Possible values**: `youtube`, `podcast`, `audiobook`, `dataset`, `lecture`
- **Default**: `youtube`
- **Examples**:
  - `-t podcast` (podcast)
  - `-t audiobook` (audiobook)
  - `-t lecture` (lecture)

#### `-d`, `--description`
- **Description**: Text description of the speaker's voice
- **Type**: string
- **Usage**: Useful for creating TTS datasets
- **Format**: Free text
- **Example**: `-d "Female voice, calm timbre, audiobook"`

#### `-o`, `--output-dir`
- **Description**: Directory to save results
- **Type**: string
- **Default**: Current directory (`.`)
- **Example**: `-o ./my_dataset`

### LLM Normalization Parameters

#### `--llm-prompt`
- **Description**: Type of prompt for LLM text normalization
- **Type**: string
- **Possible values**: `default`, `podcast`, `audiobook`, `lecture`, `custom`
- **Default**: `None` (not used)
- **Requires**: `LLM_ENABLED=true` in configuration
- **Examples**:
  - `--llm-prompt podcast` (normalization for podcasts)
  - `--llm-prompt audiobook` (normalization for audiobooks)
  - `--llm-prompt custom` (requires `--llm-custom-prompt`)

#### `--llm-custom-prompt`
- **Description**: Custom system prompt for LLM
- **Type**: string
- **Usage**: Used only with `--llm-prompt custom`
- **Example**: `--llm-custom-prompt "Your custom prompt here"`

#### `--disable-llm`
- **Description**: Disable LLM normalization even if enabled in config
- **Type**: flag (no value)
- **Example**: `--disable-llm`

## 🔧 Configuration Parameters (.env)

The configuration file `.env` contains API connection settings and LLM configurations. The file can be located in several places in order of priority:

1. Current directory (`./.env`)
2. `~/.youtube-2-whisper/.env`
3. `~/.config/youtube-2-whisper/.env`

### Main Parameters

#### `WHISPER_API_URL`
- **Description**: URL of the Whisper API server
- **Type**: string
- **Example**: `http://localhost:8000/v1`
- **Required**: Yes

#### `WHISPER_API_KEY`
- **Description**: API key for server access
- **Type**: string
- **Example**: `sk-12345`
- **Required**: Yes
- **Note**: For local server, any string works.

#### `WHISPER_MODEL_NAME`
- **Description**: Name of the Whisper model for transcription
- **Type**: string
- **Default**: `stt`
- **Examples**:
  - `large-v3`
  - `medium`
  - `small`

### LLM Parameters

#### `LLM_ENABLED`
- **Description**: Enable LLM text normalization
- **Type**: boolean
- **Possible values**: `true`, `false`
- **Default**: `false`
- **Example**: `LLM_ENABLED=true`

#### `LLM_MODEL_NAME`
- **Description**: Name of the LLM model for normalization
- **Type**: string
- **Default**: `llm`
- **Example**: `gpt-4`

## 📑 Source Types

The `--type` parameter defines the type of audio source and affects processing and metadata.

### `youtube` (default)
- **Description**: YouTube video
- **Usage**: For regular videos, reviews, tutorials
- **Example**: `-t youtube`

### `podcast`
- **Description**: Podcast
- **Usage**: For audio podcasts with dialogues
- **Features**:
  - Preserves conversational style
  - Removes interjections and pauses (um, uh, like)
  - Breaks into paragraphs by semantic blocks
- **Example**: `-t podcast`

### `audiobook`
- **Description**: Audiobook
- **Usage**: For audio versions of books
- **Features**:
  - Preserves author's style
  - Proper punctuation in dialogues
  - Preserves descriptive elements
- **Example**: `-t audiobook`

### `dataset`
- **Description**: Training dataset
- **Usage**: For creating training datasets
- **Features**:
  - Minimal processing
  - Preserves original structure
- **Example**: `-t dataset`

### `lecture`
- **Description**: Lecture
- **Usage**: For educational videos
- **Features**:
  - Structuring by theses
  - Correcting terms and professional lexicon
  - Removing repetitions
- **Example**: `-t lecture`

## 🤖 LLM Normalization Prompts

LLM normalization transforms text from Whisper into cleaner, more structured form. Several predefined prompts are available:

### `default` (default)
- **Tasks**:
  - Convert numbers to word form
  - Yofication (replacing `e` with `ё` when needed)
  - Stress marks in homographs
  - Preserve original punctuation
- **Example**: `5 кг` → `пять килограммов`

### `podcast`
- **Tasks**:
  - Fix recognition errors
  - Add punctuation
  - Remove interjections (um, uh, like)
  - Preserve conversational style
  - Break into paragraphs

### `audiobook`
- **Tasks**:
  - Fix recognition errors
  - Proper punctuation and quotes in dialogues
  - Preserve author's style
  - Break into paragraphs
  - Preserve descriptive elements

### `lecture`
- **Tasks**:
  - Fix terms and professional lexicon
  - Structure by theses
  - Remove repetitions and speech filler
  - Preserve important examples
  - Add semantic block division

### `custom`
- **Description**: Custom prompt
- **Usage**: Requires `--llm-custom-prompt` to be specified
- **Example**:
  ```bash
  --llm-prompt custom --llm-custom-prompt "Your prompt here"
  ```

## ⏱️ Time Format Specifications

Several formats are supported for specifying start and end times:

### Simple formats
- `45` - 45 seconds
- `45.5` - 45 seconds 500 milliseconds
- `1:30` - 1 minute 30 seconds
- `1:20:05` - 1 hour 20 minutes 5 seconds
- `1:20:30:500` - 1 hour 20 minutes 30 seconds 500 milliseconds

### Usage examples
```bash
# Segment from 1:30 to 5:45
youtube-2-whisper "URL or VIDEO_ID" 1:30 5:45

# Segment from 10 seconds to 25 seconds
youtube-2-whisper "URL or VIDEO_ID" 10 25

# Entire video (no time specified)
youtube-2-whisper "URL or VIDEO_ID"
```

## 💡 Usage Examples

### Basic examples

#### 1. Entire video
```bash
youtube-2-whisper "URL or VIDEO_ID"
```

#### 2. Video segment
```bash
youtube-2-whisper "URL or VIDEO_ID" 1:30 5:45
```

#### 3. With language specification
```bash
youtube-2-whisper "URL or VIDEO_ID" -l en-US
```

### Advanced examples

#### 4. With voice description and source type
```bash
youtube-2-whisper "URL or VIDEO_ID" --type podcast --description "Male voice, low timbre"
```

#### 5. With LLM normalization
```bash
youtube-2-whisper "URL or VIDEO_ID" --llm-prompt podcast
```

#### 6. Save to specific directory
```bash
youtube-2-whisper "URL or VIDEO_ID" -o /path/to/output
```

#### 7. Custom LLM prompt
```bash
youtube-2-whisper "URL or VIDEO_ID" --llm-prompt custom --llm-custom-prompt "Your prompt"
```

#### 8. Full example with all parameters
```bash
youtube-2-whisper "URL or VIDEO_ID" 10 25 \
  -l ru-RU \
  -t podcast \
  -d "Female voice, calm timbre" \
  -o ./my_dataset \
  --llm-prompt podcast
```

## 📊 Output Format

Two files are created for each run:

### 1. `filename.flac`
- **Format**: Mono FLAC, 24kHz
- **Usage**: Ready audio for training models
- **Features**:
  - Normalized loudness (Loudnorm)
  - Mono channel
  - 24kHz sample rate

### 2. `filename.json`
- **Format**: JSON
- **Content**:
  ```json
  {
    "id": "SHA256 hash",
    "lang": "ru-RU",
    "text": {
      "raw": "Original text from Whisper",
      "normalized": "Normalized text"
    },
    "source": {
      "type": "youtube",
      "id": "VIDEO_ID",
      "segment_sec": {
        "start": 60.0,
        "end": 180.0,
        "duration_sec": 120.0
      }
    },
    "speaker": {
      "id": "CHANNEL_ID",
      "voice_description": "Voice description"
    }
  }
  ```

## 🛠️ Troubleshooting

### Common issues

#### Error: `WHISPER_API_URL not specified`
- **Cause**: `.env` file not found or missing required parameters
- **Solution**:
  1. Create `.env` file in current directory
  2. Specify `WHISPER_API_URL` and `WHISPER_API_KEY`
  3. Run script again

#### Error: `FFmpeg not found`
- **Cause**: FFmpeg not installed
- **Solution**: Install FFmpeg using system package manager

---

**Last updated**: 2025-12-17
