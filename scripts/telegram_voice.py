"""
Telegram Voice Note Delivery Engine for Gagan AI.
Converts text into high-quality neural speech and sends it directly
to your phone as a Telegram Voice Note.
"""
import os
import sys
import tempfile
import requests

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, '.env')

sys.path.insert(0, os.path.join(BASE_DIR, 'voice'))
from tts_engine import synthesize_to_file

def load_env():
    env = {}
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip().strip('"').strip("'")
    return env

def send_telegram_voice(text: str, caption: str = None, chat_id: str = None) -> dict:
    """Synthesize text and send as a native Telegram Voice Note."""
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN")
    target_chat = chat_id or env.get("TELEGRAM_USER_CHAT_ID", "7845751251")

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in .env")
    if not target_chat:
        raise ValueError("TELEGRAM_USER_CHAT_ID not configured")

    # 1. Synthesize audio
    fd, audio_path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)

    try:
        synthesize_to_file(text, output_path=audio_path)

        # 2. Upload as voice note via Telegram API
        url = f"https://api.telegram.org/bot{token}/sendVoice"
        with open(audio_path, 'rb') as audio_file:
            files = {'voice': ('voice.mp3', audio_file, 'audio/mpeg')}
            data = {'chat_id': target_chat}
            if caption:
                data['caption'] = caption

            resp = requests.post(url, data=data, files=files, timeout=30)
            data_resp = resp.json()

            if not data_resp.get("ok"):
                raise RuntimeError(f"Telegram API Error: {data_resp.get('description')}")

            msg_id = data_resp.get("result", {}).get("message_id")
            return {"status": "success", "message_id": msg_id}

    finally:
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass

if __name__ == '__main__':
    msg = sys.argv[1] if len(sys.argv) > 1 else "Namaste Gagan! Gagan AI voice message system is now live on your phone."
    print(f"Sending voice note to Telegram: '{msg}'...")
    res = send_telegram_voice(msg, caption="🎙️ Gagan AI Voice Note")
    print(f"✅ Voice note delivered successfully! Message ID: {res['message_id']}")

