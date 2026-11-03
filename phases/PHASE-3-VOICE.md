# Phase 3: Voice — "Hey Jarvis" Wake Word + Voice Pipeline

> **Priority:** 🟡 HIGH — The JARVIS experience
> **Estimated Time:** 3–4 days
> **Dependencies:** Phase 1 COMPLETE
> **Status:** 🔲 NOT STARTED

---

## Overview

This phase adds the iconic JARVIS voice interface:
1. **OpenWakeWord** — Always-listening "Hey Jarvis" detector (~50 MB RAM)
2. **whisper.cpp** — Local speech-to-text (~150 MB RAM)
3. **Piper TTS** — Offline text-to-speech (~80 MB RAM)
4. **Edge-TTS** — Online premium voices (zero RAM, needs internet)
5. **Bridge Script** — Glues everything together into a voice loop

After Phase 3, you can say "Hey Jarvis, check my emails" and hear a
spoken response — completely hands-free.

---

## Prerequisites

- [x] Phase 1 complete (OpenClaw running, Telegram working)
- [x] Python 3.11+ installed
- [ ] Working microphone
- [ ] Working speakers or headphones
- [ ] ~1 GB disk space for models

---

## Step 3.1: Set Up Python Virtual Environment

```powershell
cd d:\Desktop\gaganAI

# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\Activate.ps1

# Upgrade pip
pip install --upgrade pip

# Verify
python --version
pip --version
```

> **ALWAYS activate the venv before running voice scripts:**
> `.\venv\Scripts\Activate.ps1`

---

## Step 3.2: Install OpenWakeWord

### Install

```powershell
pip install openwakeword
```

### Download Pre-trained Models

OpenWakeWord comes with default models. For "Hey Jarvis", you have two options:

**Option A: Use built-in "hey_jarvis" model (if available)**

```python
# Test if the default model works:
python -c "
from openwakeword.model import Model
model = Model(wakeword_models=['hey_jarvis_v0.1'])
print('Model loaded successfully!')
"
```

**Option B: Train custom "Hey Jarvis" wake word (recommended)**

1. Go to https://colab.research.google.com
2. Open the OpenWakeWord training notebook:
   `https://github.com/dscripka/openWakeWord/blob/main/notebooks/`
3. Follow the training guide to create a custom "Hey Jarvis" model
4. Download the trained `.onnx` model
5. Save to: `d:\Desktop\gaganAI\voice\wakeword\hey_jarvis.onnx`

### Test Wake Word Detection

Create `d:\Desktop\gaganAI\voice\test_wakeword.py`:

```python
"""Test wake word detection from microphone."""
import pyaudio
import numpy as np
from openwakeword.model import Model

# Load model
model = Model(
    wakeword_models=["hey_jarvis_v0.1"],  # or path to custom model
    inference_framework="onnx"
)

# Audio stream config
CHUNK = 1280  # 80ms at 16kHz
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000

# Start microphone
audio = pyaudio.PyAudio()
stream = audio.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    frames_per_buffer=CHUNK
)

print("🎤 Listening for 'Hey Jarvis'... (Ctrl+C to stop)")

try:
    while True:
        audio_data = stream.read(CHUNK, exception_on_overflow=False)
        audio_array = np.frombuffer(audio_data, dtype=np.int16)

        # Run prediction
        prediction = model.predict(audio_array)

        # Check if wake word detected (threshold: 0.5)
        for model_name, score in prediction.items():
            if score > 0.5:
                print(f"🔔 Wake word detected! (score: {score:.2f})")

except KeyboardInterrupt:
    print("\nStopped.")
    stream.close()
    audio.terminate()
```

```powershell
pip install pyaudio numpy
python voice\test_wakeword.py
```

> **If pyaudio fails to install on Windows:**
> `pip install pipwin && pipwin install pyaudio`
> Or download `.whl` from https://www.lfd.uci.edu/~gohlke/pythonlibs/

**✅ Checkpoint:** Saying "Hey Jarvis" into your mic triggers a detection event.

---

## Step 3.3: Install whisper.cpp (Speech-to-Text)

### Download Pre-built Binary

1. Go to https://github.com/ggerganov/whisper.cpp/releases
2. Download the latest Windows release: `whisper-cpp-win-x64.zip`
3. Extract to `d:\Desktop\gaganAI\voice\stt\`

### Download Model

```powershell
cd d:\Desktop\gaganAI\voice\stt

# Download base.en model (~150 MB, best speed/accuracy for English)
curl -L -o ggml-base.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin

# Alternative: tiny.en (~75 MB, faster but less accurate)
# curl -L -o ggml-tiny.en.bin https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.en.bin
```

### Test STT

```powershell
# Record 5 seconds of audio:
# (Use any voice recorder, save as .wav)

# Transcribe:
.\voice\stt\main.exe -m .\voice\stt\ggml-base.en.bin -f test_audio.wav
```

### Python Wrapper (for bridge script)

```python
"""Wrapper for whisper.cpp STT."""
import subprocess
import tempfile
import wave
import numpy as np


def transcribe_audio(audio_data: np.ndarray, sample_rate: int = 16000) -> str:
    """Transcribe audio numpy array using whisper.cpp."""
    # Save to temporary WAV file
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        with wave.open(f.name, "w") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(audio_data.tobytes())
        temp_path = f.name

    # Run whisper.cpp
    result = subprocess.run(
        [
            r"d:\Desktop\gaganAI\voice\stt\main.exe",
            "-m", r"d:\Desktop\gaganAI\voice\stt\ggml-base.en.bin",
            "-f", temp_path,
            "--no-timestamps",
            "-t", "4",  # threads
        ],
        capture_output=True,
        text=True,
    )

    return result.stdout.strip()
```

**✅ Checkpoint:** Can transcribe spoken English to text locally.

---

## Step 3.4: Install Piper TTS (Offline Text-to-Speech)

### Download Piper

1. Go to https://github.com/rhasspy/piper/releases
2. Download `piper_windows_amd64.zip`
3. Extract to `d:\Desktop\gaganAI\voice\tts\piper\`

### Download Voice Model

```powershell
cd d:\Desktop\gaganAI\voice\tts\piper

# Download a high-quality English voice
# (en_US-lessac-medium is a good balance of quality and speed)
curl -L -o en_US-lessac-medium.onnx https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx
curl -L -o en_US-lessac-medium.onnx.json https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

### Test Piper TTS

```powershell
echo "Hello, I am Gagan, your personal assistant" | .\voice\tts\piper\piper.exe --model .\voice\tts\piper\en_US-lessac-medium.onnx --output_file test_speech.wav

# Play the output:
start test_speech.wav
```

**✅ Checkpoint:** Piper generates spoken audio from text, offline.

---

## Step 3.5: Install Edge-TTS (Online Premium Voice)

```powershell
pip install edge-tts
```

### Test Edge-TTS

```powershell
# List available voices:
edge-tts --list-voices | findstr "en-"

# Generate speech (uses Microsoft's neural voices for free):
edge-tts --voice "en-US-GuyNeural" --text "Hello, I am Gagan Rajput" --write-media test_edge.mp3

# Play:
start test_edge.mp3
```

### Recommended Voices

| Voice | Style | Best For |
|---|---|---|
| `en-US-GuyNeural` | Professional male | Default Gagan voice |
| `en-US-ChristopherNeural` | Confident male | Alternative Gagan voice |
| `en-GB-RyanNeural` | British male | If you want a Tony Stark vibe |
| `en-IN-PrabhatNeural` | Indian male | If you prefer Indian accent |

**✅ Checkpoint:** Edge-TTS produces studio-quality speech. Much better than Piper but needs internet.

---

## Step 3.6: Build the Voice Bridge Script

Create `d:\Desktop\gaganAI\voice\bridge.py`:

```python
"""
Gagan AI Voice Bridge
Connects: Mic → Wake Word → STT → OpenClaw API → TTS → Speaker

This is the main voice pipeline script. Run it at startup for
always-on voice control.
"""
import os
import sys
import time
import json
import wave
import tempfile
import subprocess
import threading
import numpy as np
import pyaudio
import requests
from openwakeword.model import Model

# ============================================================
# CONFIGURATION
# ============================================================

WAKEWORD_MODEL = "hey_gagan.onnx"  # custom trained model (or hey_jarvis_v0.1)
WAKEWORD_THRESHOLD = 0.5
WHISPER_BINARY = r"d:\Desktop\gaganAI\voice\stt\main.exe"
WHISPER_MODEL = r"d:\Desktop\gaganAI\voice\stt\ggml-base.en.bin"
PIPER_BINARY = r"d:\Desktop\gaganAI\voice\tts\piper\piper.exe"
PIPER_MODEL = r"d:\Desktop\gaganAI\voice\tts\piper\en_US-lessac-medium.onnx"
OPENCLAW_API = "http://localhost:3000/api/chat"  # Check actual OpenClaw API
EDGE_TTS_VOICE = "en-US-GuyNeural"

# Audio config
SAMPLE_RATE = 16000
CHUNK_SIZE = 1280  # 80ms at 16kHz
RECORD_SECONDS = 8  # Max recording time after wake word
SILENCE_THRESHOLD = 500  # Amplitude below this = silence
SILENCE_DURATION = 1.5  # Seconds of silence to stop recording

# ============================================================
# FUNCTIONS
# ============================================================

def record_until_silence(stream, max_seconds=RECORD_SECONDS):
    """Record audio until silence is detected or max time reached."""
    print("🎤 Listening...")
    frames = []
    silent_chunks = 0
    chunks_per_second = SAMPLE_RATE // CHUNK_SIZE

    for _ in range(int(max_seconds * chunks_per_second)):
        data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
        frames.append(data)

        audio_array = np.frombuffer(data, dtype=np.int16)
        amplitude = np.abs(audio_array).mean()

        if amplitude < SILENCE_THRESHOLD:
            silent_chunks += 1
        else:
            silent_chunks = 0

        if silent_chunks > int(SILENCE_DURATION * chunks_per_second):
            break

    return b"".join(frames)


def transcribe(audio_bytes):
    """Transcribe audio bytes using whisper.cpp."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        with wave.open(f.name, "w") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(SAMPLE_RATE)
            wav.writeframes(audio_bytes)
        temp_path = f.name

    result = subprocess.run(
        [WHISPER_BINARY, "-m", WHISPER_MODEL, "-f", temp_path,
         "--no-timestamps", "-t", "4"],
        capture_output=True, text=True
    )
    os.unlink(temp_path)
    return result.stdout.strip()


def ask_gagan(text):
    """Send text to OpenClaw and get response."""
    try:
        response = requests.post(OPENCLAW_API, json={
            "message": text,
            "channel": "voice"
        }, timeout=30)
        return response.json().get("reply", "Sorry, I didn't understand.")
    except Exception as e:
        print(f"Error contacting Gagan AI: {e}")
        return "I'm having trouble connecting right now."


def speak(text, use_edge=True):
    """Convert text to speech and play it."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = f.name

    try:
        if use_edge:
            # Try Edge-TTS (better quality, needs internet)
            subprocess.run(
                ["edge-tts", "--voice", EDGE_TTS_VOICE,
                 "--text", text, "--write-media", temp_path],
                capture_output=True, timeout=10
            )
        else:
            raise Exception("Falling back to Piper")
    except Exception:
        # Fallback to Piper (offline)
        process = subprocess.run(
            [PIPER_BINARY, "--model", PIPER_MODEL,
             "--output_file", temp_path],
            input=text, capture_output=True, text=True
        )

    # Play audio
    if os.path.exists(temp_path) and os.path.getsize(temp_path) > 0:
        os.system(f'start /min "" "cmd /c powershell -c (New-Object Media.SoundPlayer \'{temp_path}\').PlaySync()"')
    os.unlink(temp_path)


# ============================================================
# MAIN LOOP
# ============================================================

def main():
    print("=" * 50)
    print("🤖 Gagan AI Voice Assistant")
    print("   Say 'Hey Gagan' to activate")
    print("   Press Ctrl+C to exit")
    print("=" * 50)

    # Load wake word model
    wakeword_model = Model(
        wakeword_models=[WAKEWORD_MODEL],
        inference_framework="onnx"
    )

    # Initialize audio
    audio = pyaudio.PyAudio()
    stream = audio.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=SAMPLE_RATE,
        input=True,
        frames_per_buffer=CHUNK_SIZE
    )

    print("\n🎤 Listening for wake word...")

    try:
        while True:
            # Step 1: Listen for wake word
            data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
            audio_array = np.frombuffer(data, dtype=np.int16)
            prediction = wakeword_model.predict(audio_array)

            for model_name, score in prediction.items():
                if score > WAKEWORD_THRESHOLD:
                    print(f"\n🔔 Wake word detected! (score: {score:.2f})")

                    # Play activation sound (optional)
                    # speak("Yes?", use_edge=False)

                    # Step 2: Record user's command
                    audio_bytes = record_until_silence(stream)

                    # Step 3: Transcribe
                    print("📝 Transcribing...")
                    text = transcribe(audio_bytes)
                    print(f"   You said: '{text}'")

                    if text and len(text.strip()) > 2:
                        # Step 4: Send to Gagan AI
                        print("🧠 Thinking...")
                        response = ask_gagan(text)
                        print(f"   Gagan: {response}")

                        # Step 5: Speak response
                        print("🗣️ Speaking...")
                        speak(response)
                    else:
                        print("   (No speech detected)")

                    print("\n🎤 Listening for wake word...")

    except KeyboardInterrupt:
        print("\n\n👋 Gagan AI signing off. Goodbye!")
        stream.close()
        audio.terminate()


if __name__ == "__main__":
    main()
```

### Install Bridge Dependencies

```powershell
pip install pyaudio numpy requests openwakeword edge-tts
```

### Test the Full Voice Loop

```powershell
cd d:\Desktop\gaganAI
.\venv\Scripts\Activate.ps1
python voice\bridge.py
```

Expected flow:
1. Script starts → "Listening for wake word..."
2. You say "Hey Gagan" → "Wake word detected!"
3. You say "What time is it?" → "Transcribing..."
4. OpenClaw processes → "Gagan: It's 10:30 AM"
5. Speaker plays the response
6. Returns to listening

**✅ Checkpoint:** Full voice loop works end-to-end.

---

## Step 3.7: Create Windows Startup Shortcut

### Create a Batch File

Create `d:\Desktop\gaganAI\start_gagan_voice.bat`:

```batch
@echo off
title Gagan Voice Assistant
cd /d d:\Desktop\gaganAI
call venv\Scripts\activate.bat
python voice\bridge.py
pause
```

### Add to Startup (optional)

```powershell
# Create shortcut in Startup folder:
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut("$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Gagan Voice.lnk")
$shortcut.TargetPath = "d:\Desktop\gaganAI\start_gagan_voice.bat"
$shortcut.WorkingDirectory = "d:\Desktop\gaganAI"
$shortcut.WindowStyle = 7  # Minimized
$shortcut.Save()
```

**✅ Checkpoint:** Gagan voice starts automatically on Windows boot.

---

## Phase 3 Completion Criteria

- [ ] Python venv created and working
- [ ] OpenWakeWord installed and detecting "Hey Gagan" / "Gagan Rajput"
- [ ] whisper.cpp downloaded, base.en model working
- [ ] Piper TTS generating speech offline
- [ ] edge-tts generating premium speech online
- [ ] bridge.py running full voice loop
- [ ] Voice commands reaching OpenClaw and getting responses
- [ ] Startup batch file created
- [ ] MEMORY.md updated with Phase 3 status = ✅ COMPLETE

---

## Troubleshooting

### Microphone not detected
```powershell
# List audio devices:
python -c "import pyaudio; p=pyaudio.PyAudio(); [print(p.get_device_info_by_index(i)['name']) for i in range(p.get_device_count())]"
# Set the correct device index in the bridge script
```

### Wake word triggers too often (false positives)
```
- Increase WAKEWORD_THRESHOLD from 0.5 to 0.7 or 0.8
- Train a custom model with more negative examples
```

### Wake word never triggers
```
- Decrease WAKEWORD_THRESHOLD to 0.3
- Ensure microphone gain is adequate
- Try speaking closer to the microphone
- Check if the correct model is loaded
```

### whisper.cpp is slow
```
- Use tiny.en model instead of base.en (~2x faster)
- Reduce thread count if CPU is overheating
- Ensure Ollama isn't running a model simultaneously (RAM contention)
```

### Edge-TTS fails (no internet)
```
- The bridge script automatically falls back to Piper TTS
- No action needed — graceful degradation is built in
```

