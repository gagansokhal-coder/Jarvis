"""Quick Gagan AI health check — run with venv python."""
import os, sys, time, json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))

results = {}

# 1. Ollama latency
try:
    import requests
    t0 = time.time()
    r = requests.post('http://127.0.0.1:11434/api/generate', json={
        'model': 'phi4-mini:latest',
        'prompt': 'Say hello in one sentence.',
        'system': 'You are Gagan AI. Reply in max 1 sentence.',
        'stream': False,
        'options': {'num_predict': 30, 'num_thread': 8}
    }, timeout=30)
    lat = time.time() - t0
    reply = r.json().get('response', '')[:80]
    results['ollama'] = f"OK {lat:.1f}s | {reply}"
except Exception as e:
    results['ollama'] = f"FAIL: {e}"

# 2. Whisper model
try:
    from voice.stt_engine import get_whisper_model
    t0 = time.time()
    m = get_whisper_model()
    results['whisper'] = f"OK loaded in {time.time()-t0:.1f}s"
except Exception as e:
    results['whisper'] = f"FAIL: {e}"

# 3. TTS
try:
    from voice.tts_engine import synthesize_to_file
    t0 = time.time()
    f = synthesize_to_file("Test.", voice="en-IN-PrabhatNeural")
    results['tts'] = f"OK {time.time()-t0:.1f}s"
    os.remove(f)
except Exception as e:
    results['tts'] = f"FAIL: {e}"

# 4. OpenWakeWord
try:
    from openwakeword.model import Model
    oww = Model(wakeword_models=['voice/wakeword/hey_gagan.onnx'], inference_framework='onnx')
    results['wakeword'] = f"OK keys={list(oww.models.keys())}"
except Exception as e:
    results['wakeword'] = f"FAIL: {e}"

# 5. Telegram sender
try:
    from scripts.telegram_sender import send_telegram_message
    results['telegram_sender'] = "OK imported"
except Exception as e:
    results['telegram_sender'] = f"FAIL: {e}"

# 6. Chat manager
try:
    from voice.chat_manager import ChatManager
    s = ChatManager.get_active_session()
    results['chat_db'] = f"OK session={s[:20]}"
except Exception as e:
    results['chat_db'] = f"FAIL: {e}"

# 7. Gmail
try:
    from scripts.gmail_manager import load_accounts_config
    cfg = load_accounts_config()
    n = len([a for a in cfg.get('accounts', []) if a.get('enabled', True)])
    results['gmail'] = f"OK {n} accounts"
except Exception as e:
    results['gmail'] = f"FAIL: {e}"

# 8. Microphone
try:
    import sounddevice as sd
    devs = sd.query_devices()
    mic_count = sum(1 for d in devs if d.get('max_input_channels', 0) > 0)
    results['mic'] = f"OK {mic_count} input devices"
except Exception as e:
    results['mic'] = f"FAIL: {e}"

# 9. Hacker GUI
try:
    gui_path = os.path.join(BASE_DIR, 'gui', 'hacker_gui.py')
    results['hacker_gui'] = "OK exists" if os.path.exists(gui_path) else "MISSING"
except Exception as e:
    results['hacker_gui'] = f"FAIL: {e}"

# 10. Latest email storage
try:
    ep = os.path.join(BASE_DIR, 'data', 'latest_email.txt')
    if os.path.exists(ep):
        sz = os.path.getsize(ep)
        results['email_storage'] = f"OK {sz} bytes"
    else:
        results['email_storage'] = "EMPTY (no email fetched yet)"
except Exception as e:
    results['email_storage'] = f"FAIL: {e}"

print("=" * 55)
print("  GAGAN AI PHASE 3 HEALTH CHECK")
print("=" * 55)
for k, v in results.items():
    status = "✅" if v.startswith("OK") else "❌"
    print(f"  {status} {k:20s} {v}")
print("=" * 55)

