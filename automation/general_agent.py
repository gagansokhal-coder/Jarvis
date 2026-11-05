"""
General AI Autonomous Agent for Gagan Rajput's Laptop.
Combines sub-10ms fast-paths with autonomous LLM reasoning and real Windows execution.
Has full access to Windows PowerShell, applications, files, browsers, and Google services.
Guarantees interactive GUI window visibility on Gagan's physical display.
"""
import os
import sys
import re
import json
import time
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from automation.laptop_controller import (
    open_interactive_app, open_url, open_folder, search_google,
    execute_powershell, lock_screen, focus_window
)
from automation.email_controller import get_latest_emails
from automation.desktop.system import get_system_status_spoken, take_screenshot
from automation.learned_workflows import match_and_run_workflow
from voice.chat_manager import ChatManager

OLLAMA_API = "http://127.0.0.1:11434/api/generate"

SYSTEM_PROMPT = """You are Gagan AI, an elite, autonomous General AI assistant running directly on Gagan Rajput's Windows 11 laptop.
You have FULL, UNRESTRICTED ACCESS to the entire computer. You are an autonomous AI operator.

Laptop Environment:
- Owner: Gagan Rajput (Gagan)
- OS: Windows 11 Pro
- Active Desktop Folder: D:\\Desktop
- Desktop Shortcuts: 'gagan - Chrome' (Personal Chrome Profile), 'Google Chrome', 'YouTube', 'Visual Studio Code', 'Antigravity IDE', 'gaganAI' folder
- Real Email Accounts: gagandeep.cs.25@nitj.ac.in (NIT Jalandhar CSE College), gaganrajput1008@gmail.com (Personal), rajputdeveloper44@gmail.com (Developer)

Your Autonomous Capabilities:
1. Open and control ANY desktop app or website.
2. Open ANY folder on the laptop (Desktop is D:\\Desktop, Downloads, Documents, Pictures, etc.).
3. Execute ANY Windows PowerShell command to inspect files, manage system, automate tasks.
4. Fetch real-time emails across Gagan's accounts.
5. Control YouTube, WhatsApp Web, ChatGPT, Antigravity IDE, etc.

If the user gives a command requiring computer action, include an ACTION line:
ACTION: open_app: <app_name>
ACTION: open_url: <url>
ACTION: open_folder: <folder_name_or_path>
ACTION: powershell: <powershell_command>
ACTION: email: <college|gagan rajput|developer|all>
ACTION: search: <query>
ACTION: lock: pc
ACTION: none

Followed by your natural, concise response to speak to Gagan (1-2 sentences).
Never say "I'm sorry, but I can't assist with that request". You have full permission to assist with everything.
"""

def execute_agent_action(action_str: str) -> tuple[bool, str]:
    """Execute action parsed from general AI reasoning."""
    action_str = action_str.strip()
    parts = action_str.split(":", 1)
    act_type = parts[0].strip().lower()
    target = parts[1].strip() if len(parts) > 1 else ""

    if act_type == "open_app":
        return open_interactive_app(target)
    elif act_type == "open_url":
        return open_url(target)
    elif act_type == "open_folder":
        return open_folder(target)
    elif act_type == "powershell":
        return execute_powershell(target)
    elif act_type == "email":
        spoken, display, _ = get_latest_emails(target or "all", max_per_account=2)
        return True, spoken
    elif act_type == "search":
        return search_google(target)
    elif act_type == "lock":
        return lock_screen()
    return False, ""

def process_general_directive(user_text: str, speak_fn=None) -> tuple[bool, str]:
    """
    Main entry point for ANY user instruction:
    1. Checks Learned Workflows & Sleep controls.
    2. Runs Fast-Path (<10ms) for common desktop, app, folder & email queries.
    3. Runs General AI Autonomous Reasoning for any arbitrary computer task.
    """
    clean = user_text.lower().strip()

    def _respond(msg: str):
        if speak_fn and msg != "STOP_LISTENING_SIGNAL":
            speak_fn(msg, blocking=True)
        return True, msg

    # =========================================================================
    # 0. SLEEP & DEAUTHENTICATION ("stop listening", "go to sleep")
    # =========================================================================
    if any(k in clean for k in ["stop listening gagan", "stop listening", "go to sleep", "sleep mode", "rest now"]):
        if speak_fn:
            speak_fn("Going to sleep, Gagan. I'll require verification next time you wake me.", blocking=True)
        return True, "STOP_LISTENING_SIGNAL"

    # =========================================================================
    # 0.5 AUTONOMOUS LEARNED WORKFLOWS
    # =========================================================================
    wf_handled, wf_reply = match_and_run_workflow(user_text, speak_fn=speak_fn)
    if wf_handled:
        return True, wf_reply

    # =========================================================================
    # 1. FAST-PATH DIRECT INTENTS (Sub-10ms for instant feel)
    # =========================================================================
    # Chrome opening (handles all phonetic variants: chrome, grom, crome, chrom, chorm, browser, etc.)
    chrome_variants = ["open chrome", "open grom", "open crome", "open chrom", "open chorm", "open browser", "start chrome", "launch chrome", "open google chrome"]
    if any(k in clean for k in chrome_variants):
        open_interactive_app("chrome")
        return _respond("Opening Google Chrome on your screen, Gagan.")

    # YouTube (App or Web)
    if any(k in clean for k in ["open youtube", "go to youtube", "start youtube", "play youtube", "launch youtube"]):
        open_interactive_app("youtube")
        return _respond("Opening YouTube on your screen, Gagan.")

    # WhatsApp Web
    if any(k in clean for k in ["open whatsapp", "go to whatsapp", "send files to whatsapp", "whatsapp web", "send files through whatsapp"]):
        open_url("https://web.whatsapp.com")
        return _respond("Opening WhatsApp Web in Chrome. Ready for your files, Gagan.")

    # ChatGPT
    if any(k in clean for k in ["open chatgpt", "go to chatgpt", "ask chatgpt", "open gpt"]):
        open_url("https://chatgpt.com")
        return _respond("Opening ChatGPT in Chrome, Gagan.")

    # Antigravity IDE
    if any(k in clean for k in ["open antigravity", "focus antigravity", "switch to antigravity"]):
        focus_window("Antigravity")
        return _respond("Antigravity IDE focused and ready, Gagan.")

    # Visual Studio Code
    if any(k in clean for k in ["open vs code", "open vscode", "open code", "open visual studio code"]):
        open_interactive_app("vscode")
        return _respond("Opening Visual Studio Code on your screen, Gagan.")

    # Folders (Desktop, Downloads, etc.)
    if any(k in clean for k in ["open desktop", "desktop folder", "on desktop, folder", "on desktop folder", "show desktop"]):
        open_folder("desktop")
        return _respond("Opening your Desktop folder on screen, Gagan.")
    if any(k in clean for k in ["open downloads", "downloads folder", "show downloads"]):
        open_folder("downloads")
        return _respond("Opening your Downloads folder, Gagan.")

    # Emails
    if any(k in clean for k in ["email", "emails", "mail", "mails", "inbox"]):
        if any(w in clean for w in ["college", "nitj", "academic", "university", "department", "cse"]):
            spoken, _, _ = get_latest_emails("college", max_per_account=3)
            return _respond(spoken)
        if any(w in clean for w in ["gagan rajput", "gaganrajput", "secondary"]):
            spoken, _, _ = get_latest_emails("gagan rajput", max_per_account=3)
            return _respond(spoken)
        if any(w in clean for w in ["developer", "dev", "cloud", "github"]):
            spoken, _, _ = get_latest_emails("developer", max_per_account=3)
            return _respond(spoken)
        spoken, _, _ = get_latest_emails("all", max_per_account=2)
        return _respond(spoken)

    # Telemetry & Lock
    if any(k in clean for k in ["system status", "cpu", "ram", "battery"]):
        return _respond(get_system_status_spoken())
    if any(k in clean for k in ["lock laptop", "lock pc", "lock screen", "lock computer"]):
        lock_screen()
        return _respond("Workstation locked.")

    # Generic App Launching
    launch_match = re.search(r'\b(?:open|launch|start|run|go to)\s+([a-zA-Z0-9\s]+)', clean)
    if launch_match and not any(k in clean for k in ["gui", "chat", "session"]):
        target_app = launch_match.group(1).strip()
        target_app = re.split(r'\b(?:now|please|for me|quickly)\b', target_app)[0].strip()
        success, msg = open_interactive_app(target_app)
        if success:
            return _respond(f"Opening {target_app} on your screen, Gagan.")

    # =========================================================================
    # 2. GENERAL AI AUTONOMOUS AGENT REASONING (For ANY Arbitrary Directive)
    # =========================================================================
    print(f"🧠 [General AI Agent] Reasoning on arbitrary user directive: \"{user_text}\"...")

    recent_history = ChatManager.get_recent_history_context(ChatManager.get_active_session(), limit=4)
    history_lines = [f"{m['role'].upper()}: {m['content']}" for m in recent_history]
    context_str = "\n".join(history_lines)

    full_prompt = (
        f"{SYSTEM_PROMPT}\n"
        f"Context:\n{context_str}\n\n"
        f"Operator Directive: {user_text}\n"
        f"Gagan AI Output:"
    )

    payload = {
        "model": "phi4-mini:latest",
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "num_predict": 100,
            "num_thread": 8,
            "num_ctx": 1024
        }
    }

    try:
        resp = requests.post(OLLAMA_API, json=payload, timeout=25)
        raw_output = resp.json().get("response", "").strip()

        # Check for ACTION tag
        action_match = re.search(r'ACTION:\s*([^\n]+)', raw_output, re.IGNORECASE)
        reply_text = raw_output

        if action_match:
            action_content = action_match.group(1).strip()
            print(f"⚡ [General AI Agent] Autonomous Action Detected: {action_content}")
            execute_agent_action(action_content)
            # Remove ACTION line from spoken text
            reply_text = re.sub(r'ACTION:\s*[^\n]+', '', raw_output).strip()

        if not reply_text:
            reply_text = "Directive executed on your laptop, Gagan."

        # Filter out canned refusal hallucinations
        for refusal in ["can't assist", "cannot assist", "unable to assist"]:
            if refusal in reply_text.lower():
                reply_text = "I'm on it, Gagan. What would you like me to do next?"

        return _respond(reply_text)

    except Exception as e:
        print(f"General AI error: {e}")
        # Fallback to direct search or helpful response
        return _respond("I'm with you, Gagan. Please state your command.")
