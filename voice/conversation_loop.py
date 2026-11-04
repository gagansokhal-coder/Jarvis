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
import datetime
import json
import subprocess
import re
import queue
import difflib
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
SILENCE_THRESHOLD = 0.007  # Sensitive RMS energy threshold for normal speech
SILENCE_DURATION_SEC = 2.4 # Generous 2.4s pause tolerance so thinking pauses don't cut off speech
FOLLOWUP_WINDOW_SEC = 8.0  # 8.0 seconds active listening window for follow-up dialogue

# Security Settings
SECURITY_CHALLENGE_ACTIVE = True  # Ask "Who are you?" upon wake-up
AUTHORIZED_IDENTITIES = [
    "bhatti rajput", "code with baba", "follower of bholenath",
    "bhattirajput", "bhatirajput", "bhati rajput", "codewithbaba",
    "follower of bhole nath", "bholenath", "gagan rajput", "gagan"
]

audio_queue = queue.Queue()

def audio_callback(indata, frames, time_info, status):
    if status:
        pass
    audio_queue.put(indata.copy())

def get_today_tasks_context() -> str:
    """Fetch real scheduled events for today from calendar_manager."""
    try:
        script_path = os.path.join(BASE_DIR, 'scripts', 'calendar_manager.py')
        res = subprocess.run(
            ['python', script_path, 'json'],
            capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=8
        )
        if res.returncode == 0 and res.stdout.strip():
            events = json.loads(res.stdout.strip())
            if events:
                lines = [f"• {e.get('start', '')} - {e.get('summary', '')}" for e in events]
                return "Real Events on Gagan's Calendar Today:\n" + "\n".join(lines)
            else:
                return "Real Events: No calendar events or tasks scheduled for today."
    except Exception:
        pass
    return "Calendar status: No pending tasks found."

def build_system_prompt(user_query: str = "") -> str:
    """Build real-time, context-aware prompt with live time and date."""
    now = datetime.datetime.now()
    current_time_str = now.strftime('%I:%M %p') # e.g. 11:30 PM
    current_date_str = now.strftime('%A, %d %B %Y')
    hour = now.hour

    if 5 <= hour < 12:
        period = "Morning"
    elif 12 <= hour < 17:
        period = "Afternoon"
    elif 17 <= hour < 21:
        period = "Evening"
    else:
        period = "Night"

    tasks_info = ""
    query_lower = user_query.lower()
    if any(k in query_lower for k in ["task", "schedule", "today", "calendar", "meeting", "do today", "plan", "event"]):
        tasks_info = f"\n\n{get_today_tasks_context()}"

    prompt = (
        f"You are Gagan AI, the elite personal AI assistant for Gagan Rajput.\n"
        f"• Current Date: {current_date_str}\n"
        f"• Current Time: {current_time_str} ({period})\n"
        f"• CRITICAL RULE: It is currently {period.lower()} ({current_time_str}). NEVER say 'Good morning' or 'Good afternoon' when it is {period.lower()}!\n"
        f"• Personality: Confident, direct, highly intelligent, loyal. Speak naturally in 1 to 2 concise sentences.\n"
        f"• NEVER recite robotic canned lines like 'How may I assist you further today?' or 'Apologies for the oversight'.\n"
        f"• If the user corrects you or hesitates, reply conversationally like a sharp human partner.\n"
        f"• Answer in the same language the user speaks (English, Hindi, Punjabi, etc.)."
        f"{tasks_info}"
    )
    return prompt

def query_ollama(prompt: str, context: list = None) -> tuple[str, list]:
    """Query local Ollama for conversational AI response with real-time awareness."""
    system_prompt = build_system_prompt(prompt)
    
    payload = {
        "model": "phi4-mini:latest",
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.4,
            "num_predict": 100
        }
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
    # Flush any stale audio from earlier TTS or ambient noise
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
        except queue.Empty:
            break

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

def is_identity_match(spoken_text: str, authorized_list: list) -> bool:
    """Intelligent passphrase matching (handles spacing, phonetics, tokens, and fuzzy matching)."""
    spoken_clean = re.sub(r'[^\w\s]', '', spoken_text.lower()).strip()
    spoken_nospace = re.sub(r'\s+', '', spoken_clean)
    if not spoken_nospace:
        return False

    for auth in authorized_list:
        auth_clean = re.sub(r'[^\w\s]', '', auth.lower()).strip()
        auth_nospace = re.sub(r'\s+', '', auth_clean)

        # 1. Exact or substring match (with or without spaces)
        if auth_clean in spoken_clean or spoken_clean in auth_clean:
            return True
        if auth_nospace in spoken_nospace or spoken_nospace in auth_nospace:
            return True

        # 2. Key distinctive tokens (e.g. bhatti, rajput, bholenath, baba)
        auth_tokens = [t for t in auth_clean.split() if len(t) >= 4]
        if auth_tokens and any(token in spoken_clean for token in auth_tokens):
            return True

        # 3. Fuzzy ratio match (tolerates minor STT character differences)
        ratio = difflib.SequenceMatcher(None, spoken_nospace, auth_nospace).ratio()
        if ratio >= 0.70:
            return True

    return False

def verify_identity() -> bool:
    """Security Protocol: Asks 'Who are you?' and checks response with retry tolerance."""
    max_attempts = 2
    for attempt in range(1, max_attempts + 1):
        if attempt == 1:
            print("\n🔒 [Security Challenge] Gagan AI: 'Who are you?'")
            speak("Who are you?", blocking=True)
        else:
            print("\n⚠️ [Security Retry] Passcode not clear. Please speak again:")
            speak("Passcode not clear. Please state your identity again.", blocking=True)

        print("🎤 Listening for identity/passcode...")
        audio = record_utterance(max_duration=6.0, initial_timeout=5.0)
        if len(audio) == 0:
            if attempt < max_attempts:
                continue
            speak("No response received. Security lockout.", blocking=True)
            return False

        stt_res = transcribe_audio_numpy(audio)
        spoken_answer = stt_res.get("text", "").lower().strip()
        print(f"🗣️ Identity response: \"{spoken_answer}\"")

        if is_identity_match(spoken_answer, AUTHORIZED_IDENTITIES):
            print("✅ Identity verified! Access granted.")
            speak("Identity confirmed. Welcome back, Gagan Rajput. What can I do for you?", blocking=True)
            return True
        else:
            print(f"⚠️ Identity attempt {attempt} failed.")

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

                # 4. Continuous Follow-up Loop (8-second window)
                while True:
                    print(f"\n👂 [Follow-up Window: {FOLLOWUP_WINDOW_SEC}s] Listening for follow-up question...")
                    followup_audio = record_utterance(max_duration=14.0, initial_timeout=FOLLOWUP_WINDOW_SEC)

                    if len(followup_audio) == 0:
                        print("⏱️ Follow-up window timed out. Returning to standby.")
                        break

                    stt_followup = transcribe_audio_numpy(followup_audio)
                    followup_text = stt_followup.get("text", "").strip()

                    # If empty noise or false click, do NOT break out of the session! Keep listening!
                    if not followup_text:
                        continue

                    # Hesitation handler: If user said an incomplete hesitation (e.g. "I mean...", "Wait...", "Uh..."), don't interrupt!
                    hesitations = ["i mean", "i mean...", "wait", "um", "uh", "actually", "so", "listen", "no i mean"]
                    clean_check = re.sub(r'[^\w\s]', '', followup_text.lower()).strip()
                    if clean_check in hesitations or (len(clean_check.split()) <= 2 and clean_check in ["i mean", "wait", "actually", "listen", "no"]):
                        print(f"👂 User hesitating ('{followup_text}'). Waiting for complete thought...")
                        more_audio = record_utterance(max_duration=10.0, initial_timeout=5.0)
                        if len(more_audio) > 0:
                            more_stt = transcribe_audio_numpy(more_audio)
                            more_text = more_stt.get("text", "").strip()
                            if more_text:
                                followup_text = f"{followup_text} {more_text}"
                                print(f"🗣️ Complete thought: \"{followup_text}\"")

                    print(f"🗣️ Follow-up: \"{followup_text}\"")

                    # Check for exit words
                    if any(w in followup_text.lower() for w in ["thank you", "thanks", "bye", "goodbye", "stop", "that's all", "alvida", "dhanyavaad", "shut up", "bas"]):
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
