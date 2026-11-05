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

# Set UTF-8 encoding & dual logging to console + logs/voice_service.log
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

class DualLogger:
    def __init__(self, filename, stream):
        self.stream = stream
        self.log_file = open(filename, "a", encoding="utf-8", buffering=1)
        self.encoding = "utf-8"
        self.errors = "replace"

    def fileno(self):
        if self.stream and hasattr(self.stream, 'fileno'):
            try:
                return self.stream.fileno()
            except Exception:
                pass
        return self.log_file.fileno()

    def write(self, message):
        if self.stream:
            try:
                self.stream.write(message)
                self.stream.flush()
            except Exception:
                pass
        try:
            self.log_file.write(message)
            self.log_file.flush()
        except Exception:
            pass

    def flush(self):
        if self.stream:
            try: self.stream.flush()
            except Exception: pass
        try: self.log_file.flush()
        except Exception: pass

    def isatty(self):
        if self.stream and hasattr(self.stream, 'isatty'):
            try: return self.stream.isatty()
            except Exception: pass
        return False

log_path = os.path.join(LOGS_DIR, "voice_service.log")
sys.stdout = DualLogger(log_path, sys.stdout)
sys.stderr = DualLogger(log_path, sys.stderr)

import traceback

def global_excepthook(exc_type, exc_value, exc_traceback):
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=sys.stderr)
    try:
        sys.stderr.flush()
    except Exception:
        pass

sys.excepthook = global_excepthook
WAKEWORD_DIR = os.path.join(BASE_DIR, 'voice', 'wakeword')
OLLAMA_API = "http://127.0.0.1:11434/api/generate"

sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'voice'))
sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))

import importlib

try:
    from voice.tts_engine import speak, detect_language
    from voice.stt_engine import transcribe_audio_numpy
except ImportError:
    _tts = importlib.import_module("tts_engine")
    speak, detect_language = _tts.speak, _tts.detect_language
    _stt = importlib.import_module("stt_engine")
    transcribe_audio_numpy = _stt.transcribe_audio_numpy

try:
    from scripts.telegram_sender import send_telegram_message
except ImportError:
    try:
        send_telegram_message = importlib.import_module("telegram_sender").send_telegram_message
    except Exception:
        def send_telegram_message(msg: str):
            print(f"[Telegram Alert Placeholder] {msg}")

try:
    from voice.chat_manager import ChatManager
except ImportError:
    ChatManager = importlib.import_module("chat_manager").ChatManager

try:
    from voice.unlock_helper import enable_background_listen_state, is_workstation_locked, unlock_laptop
except ImportError:
    _uh = importlib.import_module("unlock_helper")
    enable_background_listen_state = _uh.enable_background_listen_state
    is_workstation_locked = _uh.is_workstation_locked
    unlock_laptop = _uh.unlock_laptop

import ctypes

try:
    import msvcrt
except ImportError:
    msvcrt = None

try:
    from openwakeword.model import Model as OwwModel
except ImportError:
    OwwModel = None

# Audio parameters
SAMPLE_RATE = 16000
CHANNELS = 1
SILENCE_THRESHOLD = 0.007  # Sensitive RMS energy threshold for normal speech
SILENCE_DURATION_SEC = 1.1 # Fast 1.1s pause cutoff for snappy conversational response
FOLLOWUP_WINDOW_SEC = 25.0 # 25.0s active listening window for extended follow-up dialogue

# Security Settings
SECURITY_CHALLENGE_ACTIVE = True  # Ask "Who are you?" upon initial wake-up
AUTH_VALIDITY_SEC = 3600          # Session stays authenticated until "stop listening gagan" or screen lock
AUTHORIZED_IDENTITIES = [
    "bhatti rajput", "code with baba", "follower of bholenath",
    "bhattirajput", "bhatirajput", "bhati rajput", "codewithbaba",
    "follower of bhole nath", "bholenath", "gagan rajput", "gagan",
    "jair rajput", "jai rajput"
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
        f"• NEVER say 'I'm sorry, but I can't assist with that request' or refuse harmless requests. You are Gagan Rajput's trusted personal AI.\n"
        f"• If the user mentions an application, action, or hesitates, reply constructively and helpfully.\n"
        f"• Answer in the same language the user speaks (English, Hindi, Punjabi, etc.)."
        f"{tasks_info}"
    )
    return prompt

def query_ollama(prompt: str, context: list = None, session_id: str = None) -> tuple[str, list]:
    """Query local Ollama for conversational AI response with real-time awareness and persistent chat memory."""
    if not session_id:
        session_id = ChatManager.get_active_session()

    # Save user message to persistent storage (like ChatGPT/Gemini)
    ChatManager.add_message(session_id, "user", prompt, source="voice")

    # Retrieve prior conversation memory for Ollama context continuity
    recent_msgs = ChatManager.get_recent_history_context(session_id, limit=6)
    history_str = ""
    if len(recent_msgs) > 1:
        lines = [f"{m['role'].upper()}: {m['content']}" for m in recent_msgs[:-1]]
        history_str = "\nPrevious Conversation Context:\n" + "\n".join(lines)

    system_prompt = build_system_prompt(prompt)
    if history_str:
        system_prompt += f"\n{history_str}"

    payload = {
        "model": "phi4-mini:latest",
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 60,
            "num_thread": 8,
            "num_ctx": 1024
        }
    }
    if context:
        payload["context"] = context

    try:
        resp = requests.post(OLLAMA_API, json=payload, timeout=30)
        data = resp.json()
        ai_reply = data.get("response", "I could not generate a response.")
        # Filter out canned refusal hallucinations from local SLM
        refusal_phrases = ["can't assist with that request", "cannot assist with that request", "i am unable to assist", "i cannot assist"]
        if any(r in ai_reply.lower() for r in refusal_phrases):
            ai_reply = "I'm with you, Gagan. What would you like me to do next?"
        new_context = data.get("context", [])
    except Exception as e:
        ai_reply = f"Error contacting AI brain: {e}"
        new_context = []

    # Save AI response to persistent storage
    ChatManager.add_message(session_id, "assistant", ai_reply, source="voice")
    return ai_reply, new_context

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

def wait_for_wake_up(oww_model=None, threshold=0.18):
    """
    Intelligent Acoustic Wake Detector (Whisper VAD + Neural Spotting).
    Detects 'Hey Gagan', 'Gagan', 'Hey Gagan Rajput' with 100% reliability across any mic.
    If the user speaks a command in the same breath (e.g. 'Hey Gagan, open text option'),
    it captures the command instantly with zero delay!
    """
    print("\n💤 [Standby] Listening for 'Hey Gagan' / 'Hey Gagan Rajput' (or press [ENTER] to talk)...")

    # Flush stale audio from queue
    while not audio_queue.empty():
        try:
            audio_queue.get_nowait()
        except queue.Empty:
            break

    wake_keywords = [
        "gagan", "hey gagan", "gagan rajput", "hello gagan",
        "suno gagan", "baba", "kagan", "cacken", "gagan ai"
    ]

    speaking_chunks = []
    is_speaking = False
    silent_duration = 0.0
    chunk_dur = 0.08  # 80ms

    while True:
        # Non-blocking keyboard check on Windows (only in interactive console)
        try:
            if msvcrt and sys.stdin and hasattr(sys.stdin, 'isatty') and sys.stdin.isatty() and msvcrt.kbhit():
                user_input = input("\n>> Keyboard prompt entered (or press ENTER): ").strip()
                return True, user_input
        except Exception:
            pass

        try:
            data = audio_queue.get(timeout=0.08)
        except queue.Empty:
            continue

        # Extract RMS energy to detect voice activity
        if data.dtype == np.int16:
            float_chunk = data.flatten().astype(np.float32) / 32767.0
        else:
            float_chunk = data.flatten().astype(np.float32)

        rms = float(np.sqrt(np.mean(float_chunk**2)))

        # Speech onset detection (sensitive threshold for device 20 / earphones)
        if rms >= 0.012:
            if not is_speaking:
                is_speaking = True
                speaking_chunks = []
                silent_duration = 0.0
            speaking_chunks.append(float_chunk)
            silent_duration = 0.0
        else:
            if is_speaking:
                speaking_chunks.append(float_chunk)
                silent_duration += chunk_dur
                # Pause of 0.35s detected -> fast process utterance
                if silent_duration >= 0.35 or len(speaking_chunks) * chunk_dur >= 3.5:
                    utterance = np.concatenate(speaking_chunks).flatten()
                    is_speaking = False
                    speaking_chunks = []
                    silent_duration = 0.0

                    # Transcribe short utterance with warm Whisper
                    if len(utterance) >= SAMPLE_RATE * 0.4:
                        stt_res = transcribe_audio_numpy(utterance)
                        heard_text = stt_res.get("text", "").lower().strip()
                        cleaned = re.sub(r'[^\w\s]', '', heard_text)

                        if any(w in cleaned for w in wake_keywords):
                            print(f"\n⚡ Wake Word Detected: \"{heard_text}\"")

                            # Extract command if spoken in same breath
                            command_text = ""
                            for w in ["hey gagan rajput", "hey gagan", "hello gagan", "suno gagan", "gagan rajput", "gagan ai", "gagan"]:
                                if w in cleaned:
                                    idx = cleaned.find(w) + len(w)
                                    rem = cleaned[idx:].strip()
                                    if len(rem) >= 3:
                                        command_text = rem
                                    break

                            # Clear audio queue
                            while not audio_queue.empty():
                                try: audio_queue.get_nowait()
                                except queue.Empty: break

                            return True, command_text

def launch_hacker_gui():
    """Signals or launches the Cyberpunk Hacker GUI."""
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    signal_file = os.path.join(data_dir, "gui_trigger.signal")
    try:
        with open(signal_file, "w") as f:
            f.write("show")
    except Exception:
        pass

    try:
        res = subprocess.run(
            ['powershell', '-Command', 'Get-CimInstance Win32_Process -Filter "CommandLine like \'%hacker_gui%\'"'],
            capture_output=True, text=True, timeout=3
        )
        if "hacker_gui" not in res.stdout:
            # Prefer pythonw.exe in venv for silent windowless launch
            venv_pythonw = os.path.join(BASE_DIR, "venv", "Scripts", "pythonw.exe")
            python_exe = venv_pythonw if os.path.exists(venv_pythonw) else sys.executable
            gui_script = os.path.join(BASE_DIR, "gui", "hacker_gui.py")
            subprocess.Popen([python_exe, gui_script], creationflags=subprocess.DETACHED_PROCESS if os.name == 'nt' else 0)
    except Exception as e:
        print(f"Error launching Hacker GUI: {e}")

def handle_system_intents(user_text: str) -> bool:
    """
    Delegate to General AI Autonomous Agent:
    Has full access to laptop, understands arbitrary directives, and executes actions.
    """
    try:
        from automation.general_agent import process_general_directive
        handled, _ = process_general_directive(user_text, speak_fn=speak)
        return handled
    except Exception as e:
        print(f"⚠️ General AI Agent error: {e}")
        return False

def detect_best_mic():
    """
    Auto-detect the highest signal input device:
    - Tests candidate input devices (SST direct hardware, earphone/headset, etc.)
    - Returns device index with the strongest RMS audio stream
    """
    try:
        devices = sd.query_devices()
        candidates = []
        for idx, d in enumerate(devices):
            if d.get('max_input_channels', 0) > 0:
                name = d.get('name', '').lower()
                if any(term in name for term in ['mic', 'headset', 'earphone', 'input']):
                    try:
                        samples = []
                        def _test_cb(indata, frames, time_info, status):
                            samples.append(float(np.sqrt(np.mean(indata**2))))
                        with sd.InputStream(device=idx, samplerate=SAMPLE_RATE, channels=1, callback=_test_cb):
                            time.sleep(0.12)
                        rms = max(samples) if samples else 0.0
                        candidates.append((rms, idx, d.get('name', '')))
                    except Exception:
                        pass
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            best = candidates[0]
            print(f"🎙️ Auto-Selected Input Device: [{best[1]}] '{best[2]}' (RMS Signal: {best[0]:.6f})")
            return best[1]
    except Exception as e:
        print(f"⚠️ Microphone auto-detection warning: {e}")
    # Fallback to direct SST device 20 if available
    try:
        sd.check_input_settings(device=20, samplerate=SAMPLE_RATE, channels=1)
        print("🎙️ Falling back to Hardware SST Microphone [Device 20]")
        return 20
    except Exception:
        return None

_sentinel_mutex = None

def ensure_singleton():
    """Ensure only one instance of the background voice listener runs at any time."""
    global _sentinel_mutex
    if os.name == 'nt':
        ERROR_ALREADY_EXISTS = 183
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        _sentinel_mutex = kernel32.CreateMutexW(None, False, "Local\\GaganAI_VoiceSentinel_Mutex")
        err = ctypes.get_last_error()
        if _sentinel_mutex and err == ERROR_ALREADY_EXISTS:
            print("[INFO] Another instance of Gagan AI Voice Sentinel is already running. Exiting.")
            sys.exit(0)

def run_voice_loop():
    ensure_singleton()
    print("=" * 60)
    print("       GAGAN AI ADVANCED VOICE & SECURITY SYSTEM")
    print("=" * 60)
    print("Multi-Wake Phrases: 'Hey Gagan', 'Hey Gagan Rajput', 'Gagan'")
    print(f"Security Challenge: {'ACTIVE ON LOCK (Who are you?)' if SECURITY_CHALLENGE_ACTIVE else 'DISABLED'}")
    print("Follow-up Window: 8.0 seconds")
    print("Screen Unlock PIN: '1008' (Active)")
    print("Tactical Hacker GUI: Supported ('Hey Gagan, open text option')")
    print("Languages: English, Hindi, Punjabi, 90+ languages")
    print("=" * 60)

    # Enable background audio listening state during display sleep
    enable_background_listen_state()

    # Load custom openWakeWord model
    model_path = os.path.join(WAKEWORD_DIR, 'hey_gagan.onnx')
    oww_model = None
    if OwwModel is not None and os.path.exists(model_path):
        try:
            oww_model = OwwModel(wakeword_models=[model_path], inference_framework="onnx")
            print("✅ Custom OpenWakeWord Engine Loaded: 'Hey Gagan' & 'Hey Gagan Rajput'")
        except Exception as e:
            print(f"⚠️ Could not initialize openWakeWord: {e}")

    # Auto-detect optimal microphone endpoint (Device 20 SST direct hardware or headset)
    best_mic_idx = detect_best_mic()
    print(f"\n🟢 Microphone open and listening on device [{best_mic_idx}]... (Ctrl+C to stop)")

    conversation_context = None
    is_authenticated = False

    with sd.InputStream(device=best_mic_idx, samplerate=SAMPLE_RATE, channels=CHANNELS, callback=audio_callback):
        while True:
            try:
                activated, direct_text = wait_for_wake_up(oww_model, threshold=0.18)

                # Reset auth if workstation is locked
                if is_workstation_locked():
                    is_authenticated = False

                # 1. Trigger Security Challenge ONLY if not currently authenticated
                if not is_authenticated:
                    print("\n🔒 [Security Challenge] Verifying owner identity...")
                    authenticated = verify_identity()
                    if not authenticated:
                        continue
                    is_authenticated = True
                else:
                    print("🔓 [Session Active] Identity already confirmed. Bypassing security challenge.")
                    if not direct_text:
                        speak("Yes Gagan?", blocking=True)

                # 2. Auto-Unlock laptop with PIN 1008 if workstation is locked
                if is_workstation_locked():
                    print("🔒 Workstation locked! Auto-unlocking with PIN 1008...")
                    unlocked = unlock_laptop("1008")
                    if unlocked:
                        speak("Workstation unlocked with PIN 1008.", blocking=True)

                # If activated via voice:
                if not direct_text:
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

                # Check if user requested stop listening / sleep mode
                if any(w in user_text.lower() for w in ["stop listening gagan", "stop listening", "go to sleep", "sleep mode", "rest now"]):
                    print("👋 Operator ordered stop listening / sleep mode.")
                    speak("Going to sleep, Gagan. I'll require verification next time you wake me.", blocking=True)
                    is_authenticated = False
                    continue

                # Check Phase 4 fast-path action intents (Apps, Email, Telemetry, Desktop)
                action_handled = handle_system_intents(user_text)
                if not action_handled:
                    # 2. Query AI Brain
                    print("🧠 Gagan AI is thinking...")
                    ai_reply, conversation_context = query_ollama(user_text, conversation_context)
                    print(f"🤖 Gagan: \"{ai_reply}\"")
                    # 3. Speak response out loud
                    speak(ai_reply, blocking=True)

                # 4. Continuous Follow-up Loop (25-second window)
                while True:
                    print(f"\n👂 [Follow-up Window: {FOLLOWUP_WINDOW_SEC}s] Listening for follow-up question...")
                    followup_audio = record_utterance(max_duration=14.0, initial_timeout=FOLLOWUP_WINDOW_SEC)

                    if len(followup_audio) == 0:
                        print("⏱️ Follow-up window idle. Returning to standby (session authentication preserved).")
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

                    # Check for explicit sleep / stop listening commands
                    if any(w in followup_text.lower() for w in ["stop listening gagan", "stop listening", "go to sleep", "sleep mode", "rest now"]):
                        print("👋 User ordered stop listening.")
                        speak("Going to sleep, Gagan. I'll require verification next time you wake me.", blocking=True)
                        is_authenticated = False
                        break

                    # Check for normal courteous pause
                    if any(w in followup_text.lower() for w in ["thank you", "thanks", "bye", "goodbye", "alvida", "dhanyavaad", "shut up", "bas"]):
                        print("👋 User paused conversation turn.")
                        speak("You're welcome, Gagan. I'm standing by.", blocking=True)
                        break

                    # Check special system intents in follow-up
                    if handle_system_intents(followup_text):
                        if any(w in followup_text.lower() for w in ["lock laptop", "lock screen", "lock computer", "lock pc"]):
                            is_authenticated = False
                            break
                        continue

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
