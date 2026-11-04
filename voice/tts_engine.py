"""
Multilingual Text-to-Speech (TTS) Engine for Gagan AI.
Supports English (India/US), Hindi, Punjabi, and 100+ global languages using Edge Neural TTS.
Plays directly via sounddevice without external popups.
"""
import asyncio
import os
import re
import sys
import tempfile
import edge_tts
import sounddevice as sd
import soundfile as sf

# Preferred Neural Voices
VOICE_MAP = {
    "en-IN": "en-IN-PrabhatNeural",      # Indian English (Male, natural)
    "en-US": "en-US-GuyNeural",           # US English (Male)
    "hi": "hi-IN-MadhurNeural",           # Hindi (Male)
    "pa": "pa-IN-OjasNeural",             # Punjabi (Male) / pa-IN-GurpreetNeural
    "es": "es-ES-AlvaroNeural",           # Spanish
    "fr": "fr-FR-HenriNeural",            # French
    "de": "de-DE-ConradNeural",           # German
    "default": "en-IN-PrabhatNeural"
}

def detect_language(text: str) -> str:
    """Detect language of text using Unicode blocks and character patterns."""
    devanagari_count = len(re.findall(r'[\u0900-\u097F]', text))
    gurmukhi_count = len(re.findall(r'[\u0A00-\u0A7F]', text))

    if devanagari_count > 3:
        return "hi"
    if gurmukhi_count > 3:
        return "pa"

    # Default to English
    return "en-IN"

def get_voice_for_text(text: str) -> str:
    lang = detect_language(text)
    return VOICE_MAP.get(lang, VOICE_MAP["default"])

async def _synthesize_async(text: str, output_path: str, voice: str = None) -> str:
    if not voice:
        voice = get_voice_for_text(text)
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)
    return output_path

def synthesize_to_file(text: str, output_path: str = None, voice: str = None) -> str:
    """Synthesize text to audio file (.mp3 or .ogg)."""
    if not output_path:
        fd, output_path = tempfile.mkstemp(suffix=".mp3")
        os.close(fd)
    
    asyncio.run(_synthesize_async(text, output_path, voice))
    return output_path

def speak(text: str, blocking: bool = True, voice: str = None):
    """Synthesize and play audio through default speakers/headphones."""
    if not text or not text.strip():
        return
    
    # Clean markdown formatting from text for cleaner speech
    clean_text = re.sub(r'[*_#`~>\[\]\(\)]', ' ', text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    try:
        temp_audio = synthesize_to_file(clean_text, voice=voice)
        data, fs = sf.read(temp_audio)
        sd.play(data, fs)
        if blocking:
            sd.wait()
        try:
            os.remove(temp_audio)
        except:
            pass
    except Exception as e:
        print(f"TTS Error: {e}", file=sys.stderr)

if __name__ == '__main__':
    test_phrase = sys.argv[1] if len(sys.argv) > 1 else "Hello Gagan! Your multilingual voice system is active and ready."
    print(f"Speaking: '{test_phrase}'")
    speak(test_phrase)
    print("Done!")
