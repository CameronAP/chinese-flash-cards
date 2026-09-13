# Chinese Flashcard Generator

An app that speeds up and partially automates flashcard creation for learning Chinese. Input Chinese-to-English translations via CSV or directly into a table, then generate pinyin automatically (or provide your own). Integrates with Anki via AnkiConnect, letting you push cards straight into the decks of your choice.

## Features

- Import Chinese-to-English translations via CSV
- Enter and edit phrases directly in a table
- Generate pinyin automatically
- Two flashcard formats:
  - English to Characters
  - Characters to Pinyin
- Generate audio for each phrase
- Sync directly to Anki via AnkiConnect, with a choice of two target decks

## Prerequisites

- Python installed
- [Anki](https://apps.ankiweb.net/) installed and running
- The [AnkiConnect](https://ankiweb.net/shared/info/2055492159) add-on installed in Anki
> **Note:** This app has only been tested on Windows. Since AnkiConnect requires the app and Anki to be running on the same machine, cross-platform behavior (macOS/Linux) is untested and not guaranteed.

## Setup

1. **Clone the repository**
```bash
   git clone <repo-url>
   cd <your-repo-folder>
```

2. **Create a virtual environment**
```bash
   python3 -m venv venv
```

3. **Activate the virtual environment**

- Windows:
```bash
     venv\Scripts\activate
```

4. **Install dependencies**
```bash
   pip install -e .
```
## Usage

### 1. Choose an audio generation provider

This app supports two audio generation backends: **texttovoice.online** and **ElevenLabs**. Choose whichever suits your needs and complete the corresponding setup below. All relevant links and variables are located in `src/service/audio.py`.

#### texttovoice.online

- Create an account at [texttovoice.online](https://www.texttovoice.online/) and retrieve your **User ID**.
- Set this value in `audio.py`:

```python
  USER_ID = "<User_ID>"
```

#### ElevenLabs

- Follow the instructions at the [ElevenLabs API key page](https://elevenlabs.io/app/developers/api-key) to generate an **API key**.
- Follow the instructions at the [ElevenLabs Voice Lab](https://elevenlabs.io/app/voice-lab) to obtain a **Voice ID**.
- Set these values in `audio.py`:

```python
  ELL_VOICE_ID = "<VOICE_ID>"
  ELL_API_KEY = "<API_KEY>"
```

### 2. Run the program

Once setup is complete, run the app with:

```bash
./start.bat

or 

python src/main.py
```

Once the app is running, use the dropdown at the top of the window to select your TTS provider (**texttovoice.online** or **ElevenLabs**).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.