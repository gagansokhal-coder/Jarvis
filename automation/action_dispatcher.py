"""
Unified Fast Action Dispatcher for Gagan AI.
Routes user commands in <10ms for instant execution of apps, emails, desktop actions, and search.
Phase 4: Automation
"""
import os
import sys
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'automation'))

from automation.desktop.launcher import launch_app, close_app, search_google, open_url_in_browser, launch_hacker_gui, focus_app
from automation.desktop.system import get_system_status_spoken, take_screenshot, lock_workstation
from automation.email_controller import get_latest_emails
from automation.learned_workflows import match_and_run_workflow
from voice.chat_manager import ChatManager

def dispatch_action(user_text: str, speak_fn=None) -> tuple[bool, str]:
    """
    Evaluates user_text against Phase 4 automation intents.
    Returns: (handled: bool, spoken_response: str)
    """
    clean = user_text.lower().strip()
    clean_nospace = re.sub(r'[^\w\s]', '', clean)

    def _respond(msg: str):
        if speak_fn and msg != "STOP_LISTENING_SIGNAL":
            speak_fn(msg, blocking=True)
        return True, msg

    # =========================================================================
    # 0. SLEEP & DEAUTHENTICATION CONTROL ("stop listening gagan", "go to sleep")
    # =========================================================================
    if any(k in clean for k in ["stop listening gagan", "stop listening", "go to sleep", "sleep mode", "rest now"]):
        print("💤 [Action Dispatcher] Operator requested stop listening / sleep mode.")
        if speak_fn:
            speak_fn("Going to sleep, Gagan. I'll require verification next time you wake me.", blocking=True)
        return True, "STOP_LISTENING_SIGNAL"

    # =========================================================================
    # 0.5 AUTONOMOUS LEARNED WORKFLOWS & USER-TAUGHT PROCEDURES
    # =========================================================================
    wf_handled, wf_reply = match_and_run_workflow(user_text, speak_fn=speak_fn)
    if wf_handled:
        return True, wf_reply

    # =========================================================================
    # 0.7 ADVANCED CHATGPT & WHATSAPP AUTOMATION
    # =========================================================================
    # ChatGPT integration
    chatgpt_match = re.search(r'\b(?:ask chatgpt|tell chatgpt|prompt chatgpt|do some work (?:from|with|on) chatgpt|search on chatgpt)\s*(?:to|about|for)?\s*(.*)', clean)
    if chatgpt_match:
        prompt_query = chatgpt_match.group(1).strip()
        import urllib.parse
        target_url = f"https://chatgpt.com/?q={urllib.parse.quote_plus(prompt_query)}" if prompt_query else "https://chatgpt.com"
        open_url_in_browser(target_url)
        return _respond(f"Deploying ChatGPT for: {prompt_query}" if prompt_query else "Opening ChatGPT in Chrome.")

    # WhatsApp integration
    if any(k in clean for k in ["send files to whatsapp", "send file to whatsapp", "send files through whatsapp", "whatsapp web", "open whatsapp", "share files on whatsapp"]):
        open_url_in_browser("https://web.whatsapp.com")
        focus_app("WhatsApp")
        return _respond("WhatsApp Web opened in Chrome. Ready to attach and send your files, Gagan.")

    # Antigravity IDE integration
    if any(k in clean for k in ["open antigravity", "focus antigravity", "switch to antigravity", "give prompt to antigravity", "antigravity"]):
        focus_app("Antigravity")
        return _respond("Antigravity IDE focused and ready on screen.")

    # =========================================================================
    # 1. APPLICATION LAUNCHING (Chrome, VS Code, Notepad, Terminal, Calc, etc.)
    # =========================================================================
    launch_match = re.search(r'\b(?:open|launch|start|run)\s+([a-zA-Z0-9\s]+)', clean)
    if launch_match and not any(k in clean for k in ["text option", "gui", "console", "email", "mail", "emails", "mails"]):
        app_target = launch_match.group(1).strip()
        # Clean common trailing or filler words
        app_target = re.split(r'\b(?:now|please|for me|quickly|ubt|but|and)\b', app_target)[0].strip()
        for filler in ["the ", "my ", "application ", "app "]:
            if app_target.startswith(filler):
                app_target = app_target[len(filler):].strip()
        
        success, msg = launch_app(app_target)
        if success:
            print(f"⚡ [Action Dispatcher] {msg}")
            return _respond(f"Opening {app_target} now, Gagan.")

    # Application Closing
    close_match = re.search(r'\b(?:close|quit|exit|kill|terminate)\s+([a-zA-Z0-9\s]+)', clean)
    if close_match and not any(k in clean for k in ["chat", "session", "memory"]):
        app_target = close_match.group(1).strip()
        app_target = re.split(r'\b(?:now|please|for me|quickly)\b', app_target)[0].strip()
        for filler in ["the ", "my ", "application ", "app "]:
            if app_target.startswith(filler):
                app_target = app_target[len(filler):].strip()
        success, msg = close_app(app_target)
        print(f"⚡ [Action Dispatcher] {msg}")
        return _respond(f"Closed {app_target}.")

    # =========================================================================
    # 2. EMAIL RETRIEVAL (NITJ College, Gagan Rajput, Primary, All Inboxes)
    # =========================================================================
    email_keywords = [
        "email", "emails", "emial", "emials", "mail", "mails", "mil", "mils",
        "emel", "emels", "emelzi", "emelz", "mel", "mels", "inbox", "inboxes", "gmail"
    ]
    if any(k in clean for k in email_keywords):
        # Account specific email requests
        if any(w in clean for w in ["college", "nitj", "academic", "university", "department", "campus", "cse", "colleg"]):
            print("⚡ [Action Dispatcher] Fetching NITJ College emails...")
            spoken, display, _ = get_latest_emails("college", max_per_account=3)
            print(display)
            return _respond(spoken)

        if any(w in clean for w in ["gagan rajput", "gaganrajput", "secondary", "rajput account"]):
            print("⚡ [Action Dispatcher] Fetching Gagan Rajput account emails...")
            spoken, display, _ = get_latest_emails("gagan rajput", max_per_account=3)
            print(display)
            return _respond(spoken)

        if any(w in clean for w in ["developer", "dev", "cloud", "github"]):
            print("⚡ [Action Dispatcher] Fetching Developer account emails...")
            spoken, display, _ = get_latest_emails("developer", max_per_account=3)
            print(display)
            return _respond(spoken)

        if any(w in clean for w in ["read latest email", "read complete email", "give me complete mail", "read mail", "read the mail"]):
            latest_path = os.path.join(BASE_DIR, 'data', 'latest_email.txt')
            if os.path.exists(latest_path):
                with open(latest_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                lines = content.split("\n\n")
                header = lines[0] if lines else "Latest email found."
                body = lines[1] if len(lines) > 1 else ""
                return _respond(f"{header}. {body[:250]}")
            else:
                spoken, _, _ = get_latest_emails("all", max_per_account=1)
                return _respond(spoken)

        # General / All Inboxes fallback for any email command
        print("⚡ [Action Dispatcher] Fetching all inboxes...")
        spoken, display, _ = get_latest_emails("all", max_per_account=2)
        print(display)
        return _respond(spoken)

    # =========================================================================
    # 3. WEB SEARCH & GOOGLE IN CHROME
    # =========================================================================
    search_match = re.search(r'\b(?:search google for|google|search for|look up)\s+(.+)', clean)
    if search_match:
        query = search_match.group(1).strip()
        search_google(query)
        print(f"⚡ [Action Dispatcher] Searching Google for '{query}'...")
        return _respond(f"Searching Google for {query}.")

    if "open youtube" in clean:
        open_url_in_browser("https://www.youtube.com")
        return _respond("Opening YouTube now, Gagan.")

    # =========================================================================
    # 4. SYSTEM TELEMETRY & DESKTOP CONTROLS
    # =========================================================================
    if any(k in clean for k in ["screenshot", "take screenshot", "capture screen"]):
        print("⚡ [Action Dispatcher] Capturing desktop screenshot...")
        success, msg = take_screenshot(send_telegram=True)
        return _respond("Screenshot captured and sent to your Telegram.")

    if any(k in clean for k in ["system status", "cpu usage", "ram usage", "battery", "system health", "cpu", "ram"]):
        spoken = get_system_status_spoken()
        print(f"⚡ [Action Dispatcher] System telemetry: {spoken}")
        return _respond(spoken)

    if any(k in clean for k in ["lock laptop", "lock screen", "lock computer", "lock pc"]):
        lock_workstation()
        return _respond("Workstation locked.")

    # =========================================================================
    # 5. CYBERPUNK HACKER CONSOLE
    # =========================================================================
    gui_triggers = [
        "open text option", "open text", "open gui", "open chat", "open terminal",
        "show text option", "show gui", "show chat", "open console", "tactical console",
        "hacker screen", "hacker gui", "show console", "text option", "text chat",
        "open text chat", "open the gui", "gui"
    ]
    if any(t in clean for t in gui_triggers):
        launch_hacker_gui()
        return _respond("Tactical console deployed, Gagan.")

    # =========================================================================
    # 6. MEMORY & DATABASE OPTIMIZATION
    # =========================================================================
    if any(t in clean for t in ["delete all chats", "clear all chats", "delete all history", "clear all history", "delete everything"]):
        ChatManager.clear_all_sessions()
        return _respond("All chat logs permanently cleared and database memory freed.")

    if any(t in clean for t in ["optimize memory", "delete chat", "clear chat", "clear memory", "prune memory"]):
        pruned = ChatManager.optimize_memory(keep_recent=5)
        return _respond(f"Memory optimization complete. {pruned} records pruned.")

    return False, ""
