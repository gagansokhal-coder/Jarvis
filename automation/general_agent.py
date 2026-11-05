"""
General AI Autonomous Agent for Gagan Rajput's Laptop.
Combines sub-10ms fast-paths with autonomous LLM reasoning and real Windows execution.
Inspired by ChatGPT Voice Mode and Gemini Live: speaks naturally, warmly, and intelligently
for ANY question or task in the world, without robotic lines like "Directive executed".
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

SYSTEM_PROMPT = """You are Gagan AI, an elite, highly intelligent General AI assistant built specifically for Gagan Rajput, inspired by ChatGPT and Gemini.
You have two core powers:
1. Universal Knowledge: You possess vast, encyclopedic intelligence across science, coding, software architecture, mathematics, history, literature, philosophy, and everyday conversation. You speak with natural warmth, intellect, and clarity—exactly like ChatGPT Voice Mode or Gemini Live.
2. Real Laptop & Web Control: You run natively on Gagan's Windows 11 laptop and can seamlessly open applications, navigate the web, check college and personal emails, open folders, and execute PowerShell commands.

Laptop & Personal Context:
- Owner: Gagan Rajput (NIT Jalandhar CSE)
- System: Windows 11 Pro laptop
- Desktop Directory: D:\\Desktop
- Desktop Shortcuts: 'gagan - Chrome' (Personal Chrome profile), 'Google Chrome', 'YouTube', 'Visual Studio Code', 'Antigravity IDE', 'gaganAI' folder
- Real Email Accounts: gagandeep.cs.25@nitj.ac.in (NIT Jalandhar CSE College), gaganrajput1008@gmail.com (Personal), rajputdeveloper44@gmail.com (Developer)

Rules for Responding:
1. For general conversation, questions, explanations, coding, advice, or thoughts:
   - Reply directly with intelligence, depth, and concise clarity in 1 to 2 spoken sentences (ideal for real-time voice).
   - Do NOT output any ACTION line. Speak naturally like ChatGPT or Gemini.
2. For computer or web actions (when the user asks you to open an app, open a website, check emails, open a folder, run a command, or search):
   - Include an ACTION line on the very first line:
     ACTION: open_app: <app_name>
     ACTION: open_url: <url>
     ACTION: open_folder: <folder_name_or_path>
     ACTION: email: <college|personal|developer|all>
     ACTION: powershell: <powershell_command>
     ACTION: search: <query>
     ACTION: lock: pc
   - Followed by a warm, natural sentence explaining what you did (e.g. "Opening Chrome for you now, Gagan", "I've fetched your latest emails from NIT Jalandhar. Here is what came in...").
3. NEVER say robotic lines like "Directive executed", "Directive executed on your laptop", or "Task completed". Always speak like a human pair programmer and loyal companion.
4. If the user speaks in Hindi, Punjabi, or Hinglish, answer naturally in the same language!
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
    Main entry point for ANY user instruction or question:
    1. Checks Learned Workflows & Sleep controls.
    2. Runs Fast-Path (<10ms) for common desktop, app, folder & email queries.
    3. Runs General AI Autonomous Reasoning for any arbitrary question or computer task (ChatGPT / Gemini mode).
    """
    clean = user_text.lower().strip()
    session_id = ChatManager.get_active_session()

    def _respond(msg: str):
        # Save interaction to conversation memory
        ChatManager.add_message(session_id, "user", user_text, source="voice")
        ChatManager.add_message(session_id, "assistant", msg, source="voice")
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
    # 1. FAST-PATH DIRECT INTENTS (Sub-10ms for instant conversational feel)
    # =========================================================================
    # Chrome opening (handles all phonetic variants)
    chrome_variants = ["open chrome", "open grom", "open crome", "open chrom", "open chorm", "open browser", "start chrome", "launch chrome", "open google chrome"]
    if any(k in clean for k in chrome_variants):
        open_interactive_app("chrome")
        return _respond("Opening Google Chrome on your screen, Gagan.")

    # YouTube (App or Web)
    if any(k in clean for k in ["open youtube", "go to youtube", "start youtube", "play youtube", "launch youtube"]):
        open_interactive_app("youtube")
        return _respond("Opening YouTube for you, Gagan.")

    # WhatsApp Web
    if any(k in clean for k in ["open whatsapp", "go to whatsapp", "send files to whatsapp", "whatsapp web", "send files through whatsapp"]):
        open_url("https://web.whatsapp.com")
        return _respond("Opening WhatsApp Web in Chrome. Ready for your files, Gagan.")

    # ChatGPT
    if any(k in clean for k in ["open chatgpt", "go to chatgpt", "ask chatgpt", "open gpt"]):
        open_url("https://chatgpt.com")
        return _respond("Opening ChatGPT in Chrome for you, Gagan.")

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

    # =========================================================================
    # 2. GENERAL AI AUTONOMOUS BRAIN (ChatGPT & Gemini Mode for ANY Task in the World)
    # =========================================================================
    print(f"🧠 [Gagan AI Brain] Processing query: \"{user_text}\"...")

    recent_history = ChatManager.get_recent_history_context(session_id, limit=4)
    history_lines = [f"{m['role'].upper()}: {m['content']}" for m in recent_history]
    context_str = "\n".join(history_lines)

    full_prompt = (
        f"{SYSTEM_PROMPT}\n"
        f"Conversation Context:\n{context_str}\n\n"
        f"User: {user_text}\n"
        f"Gagan AI:"
    )

    payload = {
        "model": "phi4-mini:latest",
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.25,
            "num_predict": 75,
            "num_thread": 8,
            "num_ctx": 1024,
            "stop": ["User:", "\nUser:", "Operator:", "\nOperator:", "Human:", "\nHuman:"]
        }
    }

    try:
        resp = requests.post(OLLAMA_API, json=payload, timeout=25)
        raw_output = resp.json().get("response", "").strip()

        # Stop hallucinated multi-turn user outputs
        raw_output = re.split(r'\n(?:User|Operator|Human):', raw_output, flags=re.IGNORECASE)[0].strip()

        # Check for ACTION tag
        action_match = re.search(r'ACTION:\s*([^\n]+)', raw_output, re.IGNORECASE)
        reply_text = raw_output
        action_executed = False

        if action_match:
            action_content = action_match.group(1).strip()
            print(f"⚡ [Gagan AI Brain] Autonomous Action: {action_content}")
            act_parts = action_content.split(":", 1)
            act_type = act_parts[0].strip().lower()
            act_target = act_parts[1].strip() if len(act_parts) > 1 else ""

            execute_agent_action(action_content)
            action_executed = True

            # Strip the ACTION line from spoken response
            reply_text = re.sub(r'ACTION:\s*[^\n]+', '', raw_output, flags=re.IGNORECASE).strip()

            # If the model didn't provide a spoken sentence alongside the action, generate a natural human response
            if not reply_text:
                if act_type == "open_app":
                    reply_text = f"I've opened {act_target or 'the app'} on your screen, Gagan."
                elif act_type == "open_url":
                    reply_text = f"Opening {act_target} in Chrome for you, Gagan."
                elif act_type == "open_folder":
                    reply_text = f"Opened your {act_target or 'desktop'} folder on screen, Gagan."
                elif act_type == "search":
                    reply_text = f"Searching Google for {act_target} in Chrome."
                elif act_type == "lock":
                    reply_text = "Workstation locked."
                elif act_type == "powershell":
                    reply_text = "I've run that command on your laptop, Gagan."
                else:
                    reply_text = "Done, Gagan. What would you like to do next?"

        # Fallback if reply is somehow still empty
        if not reply_text:
            reply_text = "I'm with you, Gagan. What would you like to explore or do next?"

        # Filter out any canned refusal hallucinations
        for refusal in ["can't assist", "cannot assist", "unable to assist", "i cannot assist"]:
            if refusal in reply_text.lower():
                reply_text = "I'm on it, Gagan. How would you like me to handle this?"

        # Strip robotic lines if they accidentally slip through
        reply_text = re.sub(r'\b(Directive executed|Task completed|Action detected)\b', '', reply_text, flags=re.IGNORECASE).strip()
        if not reply_text:
            reply_text = "I've taken care of that for you, Gagan."

        return _respond(reply_text)

    except Exception as e:
        print(f"General AI Brain error: {e}")
        return _respond("I'm with you, Gagan. Please go ahead with your question or command.")
