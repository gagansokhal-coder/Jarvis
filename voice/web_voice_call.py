"""
Gagan AI - Web Voice Call Portal (ChatGPT Voice Mode for Phone & Desktop).
Enables continuous hands-free voice conversations from any smartphone (iOS/Android)
or laptop browser with zero app installation.
"""
import os
import sys
import json
import base64
import tempfile
import asyncio
from aiohttp import web

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'voice'))
sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))

from voice.stt_engine import transcribe_audio_file
from voice.tts_engine import synthesize_to_file, get_voice_for_text
from voice.chat_manager import ChatManager
from voice.conversation_loop import query_ollama, handle_system_intents

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>GAGAN AI // Live Voice Call</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;800&family=Orbitron:wght@600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg: #070a0f;
            --panel: #0d131d;
            --border: #162536;
            --neon-green: #00ff9d;
            --neon-cyan: #00e5ff;
            --neon-red: #ff3366;
            --text-dim: #607b96;
            --text-bright: #e2f1ff;
        }
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
        }
        body {
            background: var(--bg);
            color: var(--text-bright);
            font-family: 'JetBrains Mono', monospace;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: space-between;
            padding: 16px;
            overflow-x: hidden;
        }
        /* Top HUD */
        .hud-header {
            width: 100%;
            max-width: 500px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 16px;
            background: rgba(13, 19, 29, 0.85);
            border: 1px solid var(--border);
            border-radius: 12px;
            backdrop-filter: blur(8px);
        }
        .hud-title {
            font-family: 'Orbitron', sans-serif;
            font-size: 14px;
            font-weight: 800;
            letter-spacing: 2px;
            color: var(--neon-cyan);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--neon-green);
            box-shadow: 0 0 10px var(--neon-green);
            animation: pulse 2s infinite;
        }
        .status-badge {
            font-size: 11px;
            color: var(--text-dim);
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Central Arc Reactor Orb */
        .orb-container {
            position: relative;
            width: 220px;
            height: 220px;
            margin: 24px 0;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .orb-outer-ring {
            position: absolute;
            width: 210px;
            height: 210px;
            border-radius: 50%;
            border: 2px dashed rgba(0, 229, 255, 0.3);
            animation: rotateRight 16s linear infinite;
        }
        .orb-middle-ring {
            position: absolute;
            width: 170px;
            height: 170px;
            border-radius: 50%;
            border: 2px solid rgba(0, 255, 157, 0.25);
            border-top-color: var(--neon-cyan);
            border-bottom-color: var(--neon-green);
            animation: rotateLeft 8s linear infinite;
        }
        .orb-core {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(0, 255, 157, 0.8) 0%, rgba(0, 229, 255, 0.4) 60%, rgba(7, 10, 15, 0.9) 100%);
            box-shadow: 0 0 30px rgba(0, 255, 157, 0.5), inset 0 0 20px rgba(0, 229, 255, 0.6);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            z-index: 2;
        }
        .orb-core:active {
            transform: scale(0.95);
        }
        .orb-core svg {
            width: 44px;
            height: 44px;
            fill: #fff;
            filter: drop-shadow(0 0 6px rgba(255, 255, 255, 0.8));
        }

        /* Orb States */
        .state-standby .orb-core {
            background: radial-gradient(circle, rgba(0, 229, 255, 0.6) 0%, rgba(13, 19, 29, 0.8) 100%);
            box-shadow: 0 0 20px rgba(0, 229, 255, 0.3);
        }
        .state-listening .orb-core {
            background: radial-gradient(circle, rgba(0, 255, 157, 0.9) 0%, rgba(0, 229, 255, 0.6) 100%);
            box-shadow: 0 0 45px var(--neon-green), inset 0 0 25px #fff;
            animation: breathe 1.2s infinite alternate;
        }
        .state-thinking .orb-middle-ring {
            border-top-color: var(--neon-cyan);
            border-right-color: var(--neon-green);
            animation: rotateRight 1s linear infinite;
        }
        .state-speaking .orb-core {
            box-shadow: 0 0 50px var(--neon-cyan), 0 0 20px var(--neon-green);
            animation: voiceWave 0.6s infinite alternate;
        }

        /* Transcript & Dialogue Area */
        .dialogue-pane {
            width: 100%;
            max-width: 500px;
            flex-grow: 1;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 16px;
            overflow-y: auto;
            max-height: 260px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            font-size: 13px;
        }
        .dialogue-bubble {
            padding: 10px 14px;
            border-radius: 10px;
            line-height: 1.5;
            word-wrap: break-word;
        }
        .user-bubble {
            background: rgba(0, 229, 255, 0.08);
            border-left: 3px solid var(--neon-cyan);
            align-self: flex-end;
            max-width: 85%;
        }
        .ai-bubble {
            background: rgba(0, 255, 157, 0.08);
            border-left: 3px solid var(--neon-green);
            align-self: flex-start;
            max-width: 90%;
        }
        .bubble-label {
            font-size: 10px;
            text-transform: uppercase;
            font-weight: 600;
            margin-bottom: 4px;
            opacity: 0.7;
        }

        /* Controls Area */
        .controls-area {
            width: 100%;
            max-width: 500px;
            margin-top: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .call-btn {
            width: 100%;
            padding: 14px;
            border-radius: 12px;
            border: 1px solid var(--neon-green);
            background: rgba(0, 255, 157, 0.12);
            color: var(--neon-green);
            font-family: 'Orbitron', sans-serif;
            font-weight: 700;
            font-size: 14px;
            letter-spacing: 1.5px;
            cursor: pointer;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .call-btn:hover {
            background: rgba(0, 255, 157, 0.25);
            box-shadow: 0 0 16px rgba(0, 255, 157, 0.4);
        }
        .call-btn.active-call {
            border-color: var(--neon-red);
            background: rgba(255, 51, 102, 0.15);
            color: var(--neon-red);
        }
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }
        .action-chip {
            padding: 8px 10px;
            background: var(--panel);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-dim);
            font-size: 11px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .action-chip:hover {
            color: var(--text-bright);
            border-color: var(--neon-cyan);
        }

        @keyframes rotateRight {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }
        @keyframes rotateLeft {
            from { transform: rotate(0deg); }
            to { transform: rotate(-360deg); }
        }
        @keyframes breathe {
            from { transform: scale(0.96); box-shadow: 0 0 20px var(--neon-green); }
            to { transform: scale(1.04); box-shadow: 0 0 55px var(--neon-green); }
        }
        @keyframes voiceWave {
            from { transform: scale(0.98); }
            to { transform: scale(1.06); }
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.4; }
        }
    </style>
</head>
<body class="state-standby">

    <!-- HUD Header -->
    <div class="hud-header">
        <div class="hud-title">
            <div class="status-dot" id="statusDot"></div>
            GAGAN AI // LIVE
        </div>
        <div class="status-badge" id="statusText">STANDBY</div>
    </div>

    <!-- Central Reactor Orb -->
    <div class="orb-container">
        <div class="orb-outer-ring"></div>
        <div class="orb-middle-ring"></div>
        <div class="orb-core" id="orbBtn" onclick="toggleCall()">
            <svg id="orbIcon" viewBox="0 0 24 24">
                <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
            </svg>
        </div>
    </div>

    <!-- Dialogue Feed -->
    <div class="dialogue-pane" id="dialoguePane">
        <div class="dialogue-bubble ai-bubble">
            <div class="bubble-label">GAGAN AI</div>
            <div>Welcome Gagan. Tap the orb or button below to initiate full-duplex live voice conversation.</div>
        </div>
    </div>

    <!-- Controls -->
    <div class="controls-area">
        <button class="call-btn" id="callBtn" onclick="toggleCall()">
            <span id="callBtnText">START LIVE VOICE CALL</span>
        </button>

        <div class="quick-actions">
            <div class="action-chip" onclick="quickQuery('Read latest email')">📧 Latest Email</div>
            <div class="action-chip" onclick="quickQuery('What is on my schedule today?')">📅 Today's Schedule</div>
        </div>
    </div>

    <script>
        let isCallActive = false;
        let mediaRecorder = null;
        let audioChunks = [];
        let audioContext = null;
        let analyser = null;
        let isListening = false;
        let isSpeaking = false;
        let audioPlayer = new Audio();

        function setVisualState(state, text) {
            document.body.className = `state-${state}`;
            document.getElementById('statusText').innerText = text.toUpperCase();
        }

        async function toggleCall() {
            if (!isCallActive) {
                await startVoiceCall();
            } else {
                stopVoiceCall();
            }
        }

        async function startVoiceCall() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                isCallActive = true;
                document.getElementById('callBtn').classList.add('active-call');
                document.getElementById('callBtnText').innerText = 'END VOICE CALL';

                setupAudioPipeline(stream);
                startListeningTurn();
            } catch (err) {
                alert('Microphone access required for voice calls: ' + err.message);
            }
        }

        function stopVoiceCall() {
            isCallActive = false;
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }
            if (audioPlayer) {
                audioPlayer.pause();
            }
            document.getElementById('callBtn').classList.remove('active-call');
            document.getElementById('callBtnText').innerText = 'START LIVE VOICE CALL';
            setVisualState('standby', 'STANDBY');
        }

        function setupAudioPipeline(stream) {
            mediaRecorder = new MediaRecorder(stream);
            
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = async () => {
                if (!isCallActive) return;
                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                audioChunks = [];
                await sendVoiceTurn(audioBlob);
            };
        }

        function startListeningTurn() {
            if (!isCallActive || isSpeaking) return;
            setVisualState('listening', 'LISTENING...');
            audioChunks = [];
            mediaRecorder.start();
            isListening = true;

            // Record user utterance (speech timeout auto-turn or 5s default)
            setTimeout(() => {
                if (isListening && mediaRecorder.state === 'recording') {
                    isListening = false;
                    mediaRecorder.stop();
                }
            }, 5500);
        }

        async function sendVoiceTurn(blob) {
            setVisualState('thinking', 'THINKING...');
            const formData = new FormData();
            formData.append('audio', blob, 'turn.webm');

            try {
                const res = await fetch('/api/voice_turn', {
                    method: 'POST',
                    body: formData
                });
                const data = await res.json();

                if (data.user_text) {
                    appendMessage('user', data.user_text);
                }
                if (data.ai_reply) {
                    appendMessage('ai', data.ai_reply);
                }

                if (data.audio_base64) {
                    playAIVoice(data.audio_base64);
                } else {
                    if (isCallActive) {
                        setTimeout(startListeningTurn, 800);
                    }
                }
            } catch (err) {
                console.error(err);
                if (isCallActive) setTimeout(startListeningTurn, 1000);
            }
        }

        function playAIVoice(base64Audio) {
            isSpeaking = true;
            setVisualState('speaking', 'SPEAKING...');
            audioPlayer.src = 'data:audio/mp3;base64,' + base64Audio;
            audioPlayer.play();

            audioPlayer.onended = () => {
                isSpeaking = false;
                // Follow-up window: as soon as Gagan AI finishes speaking, open mic for follow-up!
                if (isCallActive) {
                    setTimeout(startListeningTurn, 600);
                } else {
                    setVisualState('standby', 'STANDBY');
                }
            };
        }

        function appendMessage(sender, text) {
            const pane = document.getElementById('dialoguePane');
            const bubble = document.createElement('div');
            bubble.className = `dialogue-bubble ${sender}-bubble`;
            const label = document.createElement('div');
            label.className = 'bubble-label';
            label.innerText = sender === 'user' ? 'GAGAN RAJPUT' : 'GAGAN AI';
            const body = document.createElement('div');
            body.innerText = text;
            bubble.appendChild(label);
            bubble.appendChild(body);
            pane.appendChild(bubble);
            pane.scrollTop = pane.scrollHeight;
        }

        async function quickQuery(prompt) {
            appendMessage('user', prompt);
            setVisualState('thinking', 'PROCESSING...');
            try {
                const res = await fetch('/api/text_query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ query: prompt })
                });
                const data = await res.json();
                appendMessage('ai', data.ai_reply);
                if (data.audio_base64) {
                    playAIVoice(data.audio_base64);
                }
            } catch (err) {
                console.error(err);
            }
        }
    </script>
</body>
</html>
"""

async def handle_index(request):
    return web.Response(text=HTML_PAGE, content_type='text/html')

async def handle_voice_turn(request):
    reader = await request.multipart()
    temp_webm = None
    try:
        while True:
            part = await reader.next()
            if part is None:
                break
            if part.name == 'audio':
                fd, temp_webm = tempfile.mkstemp(suffix='.webm')
                os.close(fd)
                with open(temp_webm, 'wb') as f:
                    while True:
                        chunk = await part.read_chunk()
                        if not chunk:
                            break
                        f.write(chunk)
                break

        if not temp_webm or not os.path.exists(temp_webm):
            return web.json_response({"error": "No audio received"}, status=400)

        # 1. Transcribe with Whisper
        stt_res = transcribe_audio_file(temp_webm)
        user_text = stt_res.get("text", "").strip()

        if not user_text:
            return web.json_response({"user_text": "", "ai_reply": "", "audio_base64": ""})

        # Check Phase 4 Fast-path Action Dispatcher (Apps, Email, System, Search)
        try:
            from automation.action_dispatcher import dispatch_action
            handled, action_reply = dispatch_action(user_text)
            if handled:
                ai_reply = action_reply
            else:
                ai_reply, _ = query_ollama(user_text)
        except Exception as e:
            print(f"Action dispatcher error: {e}")
            ai_reply, _ = query_ollama(user_text)

        # 2. Synthesize with Edge-TTS
        audio_mp3 = synthesize_to_file(ai_reply)
        with open(audio_mp3, 'rb') as f:
            b64_audio = base64.b64encode(f.read()).decode('utf-8')

        try: os.remove(audio_mp3)
        except: pass

        return web.json_response({
            "user_text": user_text,
            "ai_reply": ai_reply,
            "audio_base64": b64_audio
        })
    finally:
        if temp_webm and os.path.exists(temp_webm):
            try: os.remove(temp_webm)
            except: pass

async def handle_text_query(request):
    data = await request.json()
    query = data.get("query", "").strip()
    if not query:
        return web.json_response({"error": "Empty query"}, status=400)

    try:
        from automation.action_dispatcher import dispatch_action
        handled, action_reply = dispatch_action(query)
        if handled:
            ai_reply = action_reply
        else:
            ai_reply, _ = query_ollama(query)
    except Exception as e:
        print(f"Action dispatcher error: {e}")
        ai_reply, _ = query_ollama(query)

    audio_mp3 = synthesize_to_file(ai_reply)
    with open(audio_mp3, 'rb') as f:
        b64_audio = base64.b64encode(f.read()).decode('utf-8')
    try: os.remove(audio_mp3)
    except: pass

    return web.json_response({
        "ai_reply": ai_reply,
        "audio_base64": b64_audio
    })

def make_app():
    app = web.Application()
    app.router.add_get('/', handle_index)
    app.router.add_post('/api/voice_turn', handle_voice_turn)
    app.router.add_post('/api/text_query', handle_text_query)
    return app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    print(f"🚀 Gagan AI Web Voice Call Server starting on http://0.0.0.0:{port}")
    print(f"📱 Connect from your smartphone on Wi-Fi: http://10.155.207.59:{port}")
    app = make_app()
    web.run_app(app, host='0.0.0.0', port=port)

