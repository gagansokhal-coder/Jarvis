"""
Launch Cloudflare Tunnel for Gagan AI Web Voice Call and auto-send public HTTPS link to Telegram.
100% Free, zero recurring cost, works anywhere in the world on mobile.
"""
import os
import sys
import re
import time
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))

from scripts.telegram_sender import send_telegram_message

def start_mobile_voice_tunnel():
    print("=" * 60)
    print("   GAGAN AI - MOBILE LIVE VOICE CALL (CLOUDFLARE TUNNEL)")
    print("=" * 60)
    
    # 1. Start Web Voice Server on port 8080 if not already running
    print("🚀 Starting Web Voice Server...")
    server_script = os.path.join(BASE_DIR, 'voice', 'web_voice_call.py')
    python_exe = os.path.join(BASE_DIR, 'venv', 'Scripts', 'python.exe')
    if not os.path.exists(python_exe):
        python_exe = sys.executable

    server_proc = subprocess.Popen([python_exe, server_script])
    time.sleep(2.0)

    # 2. Start Cloudflare Tunnel
    cloudflared_bin = os.path.join(BASE_DIR, 'bin', 'cloudflared.exe')
    if not os.path.exists(cloudflared_bin):
        print("❌ cloudflared.exe not found in bin/")
        return

    print("🌐 Launching Cloudflare Tunnel for secure mobile HTTPS...")
    tunnel_cmd = [cloudflared_bin, "tunnel", "--url", "http://127.0.0.1:8080"]
    tunnel_proc = subprocess.Popen(
        tunnel_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        errors='replace'
    )

    public_url = None
    t0 = time.time()
    while time.time() - t0 < 30:
        line = tunnel_proc.stdout.readline()
        if not line:
            time.sleep(0.2)
            continue
        print(line.strip())
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            public_url = match.group(0)
            break

    if public_url:
        print("\n" + "=" * 60)
        print(f"🎉 MOBILE LIVE VOICE LINK: {public_url}")
        print("=" * 60)
        
        # 3. Auto-send link to Telegram so user gets it on their phone instantly
        telegram_msg = (
            f"🚀 *GAGAN AI MOBILE VOICE CALL IS LIVE!*\n\n"
            f"Talk to Gagan AI from your phone like ChatGPT Voice mode:\n"
            f"🔗 {public_url}\n\n"
            f"• Tap the link in your phone's browser (Safari/Chrome).\n"
            f"• Tap 'START LIVE VOICE CALL'.\n"
            f"• 100% Free, zero tokens, runs directly on your laptop!"
        )
        try:
            send_telegram_message(telegram_msg)
            print("📲 Public HTTPS link automatically delivered to your Telegram!")
        except Exception as e:
            print(f"Telegram notification error: {e}")

        try:
            tunnel_proc.wait()
        except KeyboardInterrupt:
            print("\nShutting down tunnel...")
            tunnel_proc.terminate()
            server_proc.terminate()
    else:
        print("⚠️ Could not capture Cloudflare URL within 30 seconds.")
        tunnel_proc.terminate()
        server_proc.terminate()

if __name__ == '__main__':
    start_mobile_voice_tunnel()
