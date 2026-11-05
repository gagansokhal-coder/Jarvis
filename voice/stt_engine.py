"""
Multilingual Speech-to-Text (STT) Engine for Gagan AI.
Powered by faster-whisper (CTranslate2).
Supports 99+ languages with automatic language detection and translation capabilities.
"""
import os
import sys
import tempfile
import numpy as np
import soundfile as sf

# Patch PyAV if av.open doesn't accept or issues with metadata_errors in newer versions
try:
    import av
    _orig_av_open = av.open
    def _patched_av_open(*args, metadata_errors=None, **kwargs):
        return _orig_av_open(*args, **kwargs)
    av.open = _patched_av_open
except Exception:
    pass

from faster_whisper import WhisperModel

DEFAULT_INITIAL_PROMPT = (
    "Gagan Rajput, Bhatti Rajput, Code with Baba, follower of Bholenath. "
    "LeetCode, daily streak, problem, solution, submit, GitHub, repo, gagansokhal-coder, "
    "GUI, text option, text chat option, text window, unlock laptop, lock laptop, password, PIN, "
    "Microsoft Edge, Google Chrome, YouTube, VS Code, Visual Studio Code, NIT Jalandhar, NITJ. "
    "Hinglish, Hindi, English, Punjabi conversation."
)

PHONETIC_CORRECTIONS = [
    (r'\b(litcode|lit code|leet code|leadcode|lead code)\b', 'leetcode'),
    (r'\b(jiway|ji way|g ui|gee you eye|gui text|text option|text chat option|text window)\b', 'open gui'),
    (r'\b(gagan sokhal coder|gagansokhal coder|gagan coder)\b', 'gagansokhal-coder'),
    (r'\b(dialy streak|daily streak)\b', 'daily streak'),
    (r'\b(alotp|labtop|loptop)\b', 'laptop'),
    (r'\b(chorm|grom|crome|chrom)\b', 'chrome'),
    (r'\b(micorosft edge|micro soft edge|close the edge|close edge|close microsoft edge)\b', 'close microsoft edge'),
]

def clean_phonetic_transcription(text: str) -> str:
    """Normalize common Whisper misheard terms, accents, and typos."""
    if not text:
        return ""
    import re
    cleaned = text
    for pattern, replacement in PHONETIC_CORRECTIONS:
        cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
    return cleaned

_MODEL_INSTANCE = None

def get_whisper_model(model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is None:
        # Load high-speed base model with lightweight int8 quantization for instant CPU response
        try:
            _MODEL_INSTANCE = WhisperModel(model_size, device=device, compute_type=compute_type)
        except Exception:
            _MODEL_INSTANCE = WhisperModel("base", device=device, compute_type=compute_type)
    return _MODEL_INSTANCE

def transcribe_audio_file(audio_path: str, language: str = None, initial_prompt: str = None) -> dict:
    """
    Transcribe audio file.
    If language is None, Whisper automatically detects the spoken language.
    """
    model = get_whisper_model()
    prompt = initial_prompt or DEFAULT_INITIAL_PROMPT
    segments, info = model.transcribe(
        audio_path,
        beam_size=2,
        condition_on_previous_text=False,
        language=language,
        initial_prompt=prompt,
        vad_filter=True, # Filters out background silence
        vad_parameters=dict(min_silence_duration_ms=200, threshold=0.35)
    )

    raw_text = " ".join([segment.text for segment in segments]).strip()
    full_text = clean_phonetic_transcription(raw_text)

    return {
        "text": full_text,
        "language": info.language,
        "language_probability": round(info.language_probability, 2),
        "duration": round(info.duration, 2)
    }

def transcribe_audio_numpy(audio_array: np.ndarray, sample_rate: int = 16000, language: str = None) -> dict:
    """Transcribe an in-memory numpy float32 audio buffer with high-gain volume boost normalization."""
    if len(audio_array) == 0:
        return {"text": "", "language": "en", "language_probability": 0.0, "duration": 0.0}

    # Volume normalization to boost quiet laptop microphones and faint speech
    max_val = np.max(np.abs(audio_array))
    if max_val > 0.002:
        audio_array = audio_array * (0.95 / max_val)

    fd, temp_wav = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        sf.write(temp_wav, audio_array, sample_rate)
        result = transcribe_audio_file(temp_wav, language=language)
        return result
    finally:
        if os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except:
                pass

if __name__ == '__main__':
    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(f"Transcribing '{path}'...")
        res = transcribe_audio_file(path)
        print(f"Language: {res['language']} (Prob: {res['language_probability']})")
        print(f"Transcription: {res['text']}")
    else:
        print("Whisper STT Engine ready. Pass a .wav/.mp3 file to transcribe.")

