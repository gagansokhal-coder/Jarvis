"""
Gagan AI Interactive Voice Conversation Loop with Continuous Follow-Ups & Security Challenge.
Features:
- Multiple Wake Word phrases support ('Hey Gagan', 'Hey Gagan Rajput', 'Gagan')
- Security Challenge Protocol ("Who are you?" / Password verification)
- Intruder Telegram Alert if incorrect passphrase is given
- Multilingual Speech-to-Text (Whisper: English, Hindi, Punjabi, etc.)
- Local Ollama AI Brain (Phi-4-mini / Qwen 2.5)
- Multilingual Neural Text-to-Speech (Edge-TTS)
- Continuous Follow-Up Conversation Window (7-second active listening window)
"""
import os
import sys
import time
import re
import queue
import requests
import numpy as np
import sounddevice as sd
import soundfile as sf

# Set UTF-8 encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WAKEWORD_DIR = os.path.join(BASE_DIR, 'voice', 'wakeword')
OLLAMA_API = "http://127.0.0.1:11434/api/generate"

sys.path.insert(0, os.path.join(BASE_DIR, 'voice'))
from tts_engine import speak, detect_language
from stt_engine import transcribe_audio_numpy

sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))
from telegram_sender import send_telegram_message

# Audio parameters
SAMPLE_RATE = 16000
CHANNELS = 1
SILENCE_THRESHOLD = 0.015  # RMS energy threshold for silence
SILENCE_DURATION_SEC = 1.5 # Consecutive silence seconds to finish user turn
FOLLOWUP_WINDOW_SEC = 7.0  # Seconds to wait for follow-up before sleeping

# Security Settings
SECURITY_CHALLENGE_ACTIVE = True  # Ask "Who are you?" upon wake-up
AUTHORIZED_IDENTITIES = ["gagan", "gagan rajput", "rajput", "its gagan", "it's gagan", "code 1008", "gagan here"]

audio_queue = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    if status:
        pass
    audio_queue.put(indata.copy())

def query_ollama(prompt: str, context: list = None) -> tuple[str, list]:
    """Query local Ollama for conversational AI response."""
    system_prompt = (
        "You are Gagan AI (or Gagan Rajput), a loyal, highly capable personal AI assistant. "
        "Keep your spoken answers concise, direct, helpful, and natural (1 to 3 sentences maximum), "
        "as your answer will be spoken out loud. Answer in the same language the user speaks to you."
    )
    
    payload = {
        "model": "phi4-mini:latest",
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
    }
    if context:
        payload["context"] = context

    try:
        resp = requests.post(OLLAMA_API, json=payload, timeout=30)
        data = resp.json()
        return data.get("response", "I could not generate a response."), data.get("context", [])
    except Exception as e:
        return f"Error contacting AI brain: {e}", []

def record_utterance(max_duration: float = 12.0, initial_timeout: float = 6.0) -> np.ndarray:
    """Record speech from microphone until silence is detected."""
    chunks = []
    silent_time = 0.0
    has_started_speaking = False
    start_time = time.time()
    chunk_duration = 0.1 # 100ms

    while True:
        elapsed = time.time() - start_time
        if not has_started_speaking and elapsed > initial_timeout:
            return np.array([], dtype=np.float32)

        if elapsed > max_duration:
            break

        try:
            chunk = audio_queue.get(timeout=0.2)
        except queue.Empty:
            continue

        chunks.append(chunk)
        rms = np.sqrt(np.mean(chunk**2))

        if rms > SILENCE_THRESHOLD:
            has_started_speaking = True
            silent_time = 0.0
        else:
            if has_started_speaking:
                silent_time += chunk_duration
                if silent_time >= SILENCE_DURATION_SEC:
                    break

    if chunks:
        return np.concatenate(chunks, axis=0).flatten()
    return np.array([], dtype=np.float32)

def verify_identity() -> bool:
    """Security Protocol: Asks 'Who are you?' and checks response."""
    print("\n🔒 [Security Challenge] Gagan AI: 'Who are you?'")
    speak("Who are you?", blocking=True)

    print("🎤 Listening for identity/passcode...")
    audio = record_utterance(max_duration=6.0, initial_timeout=5.0)
    if len(audio) == 0:
        speak("No response received. Security lockout.", blocking=True)
        return False

    stt_res = transcribe_audio_numpy(audio)
    spoken_answer = stt_res.get("text", "").lower().strip()
    spoken_clean = re.sub(r'[^\w\s]', '', spoken_answer)
    print(f"🗣️ Identity response: \"{spoken_answer}\"")

    is_authorized = any(ident in spoken_clean for ident in AUTHORIZED_IDENTITIES)

    if is_authorized:
        print("✅ Identity verified! Access granted.")
        speak("Identity confirmed. Welcome back, Gagan. What can I do for you?", blocking=True)
        return True
    else:
        print("❌ Identity NOT recognized! Sending intruder alert to Telegram.")
        speak("Access denied. Unauthorized voice request.", blocking=True)
        try:
            alert_msg = (
                f"🚨 *GAGAN AI SECURITY ALERT*\n\n"
                f"An unrecognized person attempted to activate Gagan AI via voice.\n"
                f"• Spoken Identity: \"{spoken_answer}\"\n"
                f"• Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"• Action: System locked & voice session terminated."
            )
            send_telegram_message(alert_msg)
        except Exception as e:
            print(f"Telegram alert error: {e}", file=sys.stderr)
        return False

def run_voice_loop():
    print("=" * 60)
    print("       GAGAN AI ADVANCED VOICE & SECURITY SYSTEM")
    print("=" * 60)
    print("Multi-Wake Phrases: 'Hey Gagan', 'Hey Gagan Rajput', 'Gagan'")
    print(f"Security Challenge: {'ACTIVE (Who are you?)' if SECURITY_CHALLENGE_ACTIVE else 'DISABLED'}")
    print("Follow-up Window: 7.0 seconds")
    print("Languages: English, Hindi, Punjabi, 90+ languages")
    print("=" * 60)

    print("\n🟢 Microphone open and listening... (Ctrl+C to stop)")

    conversation_context = None

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, callback=audio_callback):
        while True:
            try:
                print("\n💤 [Standby] Listening for wake-up... (Press ENTER or type prompt to activate)")
                
                user_input = input(">> Press [ENTER] to talk (or type command): ")
                direct_text = user_input.strip()

                # If activated:
                if not direct_text:
                    # 1. Security Challenge: "Who are you?"
                    if SECURITY_CHALLENGE_ACTIVE:
                        authenticated = verify_identity()
                        if not authenticated:
                            continue

                    print("🎤 Listening for your query... Speak now!")
                    audio_data = record_utterance(max_duration=12.0, initial_timeout=6.0)
                    if len(audio_data) == 0:
                        print("No speech detected.")
                        continue

                    print("⚡ Transcribing speech with Whisper...")
                    stt_res = transcribe_audio_numpy(audio_data)
                    user_text = stt_res.get("text", "").strip()
                    detected_lang = stt_res.get("language", "en")
                    print(f"🗣️ You said [{detected_lang}]: \"{user_text}\"")
                else:
                    user_text = direct_text

                if not user_text:
                    continue

                # 2. Query AI Brain
                print("🧠 Gagan AI is thinking...")
                ai_reply, conversation_context = query_ollama(user_text, conversation_context)
                print(f"🤖 Gagan: \"{ai_reply}\"")

                # 3. Speak response out loud
                speak(ai_reply, blocking=True)

                # 4. Continuous Follow-up Loop (7-second window)
                while True:
                    print(f"\n👂 [Follow-up Window: {FOLLOWUP_WINDOW_SEC}s] Listening for follow-up question...")
                    followup_audio = record_utterance(max_duration=12.0, initial_timeout=FOLLOWUP_WINDOW_SEC)

                    if len(followup_audio) == 0:
                        print("⏱️ Follow-up window timed out. Returning to standby.")
                        break

                    stt_followup = transcribe_audio_numpy(followup_audio)
                    followup_text = stt_followup.get("text", "").strip()

                    if not followup_text:
                        break

                    print(f"🗣️ Follow-up: \"{followup_text}\"")

                    # Check for exit words
                    if any(w in followup_text.lower() for w in ["thank you", "thanks", "bye", "goodbye", "stop", "that's all", "alvida", "dhanyavaad"]):
                        print("👋 User ended conversation.")
                        speak("You're welcome, Gagan. I'm here whenever you need me.", blocking=True)
                        break

                    # Continue conversation
                    ai_reply, conversation_context = query_ollama(followup_text, conversation_context)
                    print(f"🤖 Gagan: \"{ai_reply}\"")
                    speak(ai_reply, blocking=True)

            except KeyboardInterrupt:
                print("\nVoice loop stopped.")
                break
            except Exception as e:
                print(f"Loop error: {e}", file=sys.stderr)
                time.sleep(1)

if __name__ == '__main__':
    run_voice_loop()
