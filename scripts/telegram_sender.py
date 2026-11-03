import os
import sys
import urllib.request
import urllib.parse
import json

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BASE_DIR, '.env')

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

def send_telegram_message(text, chat_id=None, parse_mode="Markdown"):
    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN")
    target_chat = chat_id or env.get("TELEGRAM_USER_CHAT_ID", "7845751251")

    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN not found in .env")
    if not target_chat:
        raise ValueError("TELEGRAM_USER_CHAT_ID not configured")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            return {"status": "success", "message_id": data.get("result", {}).get("message_id")}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode('utf-8')
        print(f"Telegram API Error ({e.code}): {err_body}", file=sys.stderr)
        # If Markdown failed, retry without parse_mode field entirely
        if "parse" in err_body.lower() or "entity" in err_body.lower() or e.code == 400:
            payload_plain = {
                "chat_id": target_chat,
                "text": text,
                "disable_web_page_preview": True
            }
            req_plain = urllib.request.Request(
                url,
                data=json.dumps(payload_plain).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req_plain, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                return {"status": "success", "message_id": data.get("result", {}).get("message_id"), "plain": True}
        raise RuntimeError(f"Telegram API Error ({e.code}): {err_body}")

if __name__ == '__main__':
    msg = sys.argv[1] if len(sys.argv) > 1 else "🤖 JARVIS Test Message"
    res = send_telegram_message(msg)
    print(f"Message delivered to Telegram! Message ID: {res['message_id']}")
