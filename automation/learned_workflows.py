"""
Autonomous Learned Workflow & Procedure Engine for Gagan AI.
Enables Gagan to learn multi-step workflows taught by the operator,
persist them to disk, and execute them automatically.
Phase 4: Advanced Automation.
"""
import os
import sys
import json
import time
import re
import webbrowser

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
WORKFLOWS_FILE = os.path.join(DATA_DIR, "learned_workflows.json")

# Default core learned recipes taught by Gagan Rajput
DEFAULT_WORKFLOWS = {
    "send files through whatsapp": {
        "description": "Opens Google Chrome to WhatsApp Web and prepares for file sending",
        "aliases": [
            "send files through whatsapp", "send file through whatsapp",
            "send files to whatsapp", "send file to whatsapp", "whatsapp my file",
            "send files on whatsapp", "open whatsapp and send file", "share files on whatsapp"
        ],
        "steps": [
            {"action": "open_url", "target": "https://web.whatsapp.com", "label": "Opening WhatsApp Web in Chrome"},
            {"action": "focus_window", "target": "WhatsApp", "label": "Focusing WhatsApp"},
            {"action": "notify", "message": "WhatsApp Web is open. Ready to select contact and attach your files, Gagan."}
        ]
    },
    "open chatgpt": {
        "description": "Opens ChatGPT in Chrome",
        "aliases": [
            "open chatgpt", "open chat gpt", "start chatgpt", "go to chatgpt",
            "launch chatgpt", "open gpt"
        ],
        "steps": [
            {"action": "open_url", "target": "https://chatgpt.com", "label": "Opening ChatGPT in Chrome"},
            {"action": "focus_window", "target": "ChatGPT", "label": "Focusing ChatGPT"},
            {"action": "notify", "message": "ChatGPT is deployed on your screen, Gagan."}
        ]
    },
    "open antigravity": {
        "description": "Focuses Google Antigravity AI IDE",
        "aliases": [
            "open antigravity", "focus antigravity", "switch to antigravity",
            "show antigravity", "go to antigravity"
        ],
        "steps": [
            {"action": "focus_window", "target": "Antigravity", "label": "Focusing Antigravity IDE"},
            {"action": "notify", "message": "Switched to Antigravity IDE, Gagan."}
        ]
    }
}

def load_workflows() -> dict:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(WORKFLOWS_FILE):
        save_workflows(DEFAULT_WORKFLOWS)
        return DEFAULT_WORKFLOWS
    try:
        with open(WORKFLOWS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure defaults exist
            for k, v in DEFAULT_WORKFLOWS.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception as e:
        print(f"Error loading learned workflows: {e}")
        return DEFAULT_WORKFLOWS

def save_workflows(data: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(WORKFLOWS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving workflows: {e}")

def learn_new_workflow(trigger_phrase: str, steps: list, description: str = "") -> str:
    """Register a new workflow taught by the user."""
    workflows = load_workflows()
    key = trigger_phrase.lower().strip()
    workflows[key] = {
        "description": description or f"Custom workflow for '{trigger_phrase}'",
        "aliases": [key],
        "steps": steps
    }
    save_workflows(workflows)
    return f"Learned new workflow for '{trigger_phrase}' with {len(steps)} steps."

def execute_workflow_step(step: dict) -> tuple[bool, str]:
    """Execute a single atomic step in a workflow."""
    action = step.get("action")
    target = step.get("target", "")

    try:
        if action == "open_url":
            chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            if os.path.exists(chrome_path):
                import subprocess
                subprocess.Popen([chrome_path, "--new-window", target])
            else:
                webbrowser.open(target)
            return True, f"Opened {target}"

        elif action == "launch_app":
            from automation.desktop.launcher import launch_app
            return launch_app(target)

        elif action == "focus_window":
            try:
                import win32com.client
                shell = win32com.client.Dispatch("WScript.Shell")
                shell.AppActivate(target)
                return True, f"Focused {target}"
            except Exception:
                return True, f"Attempted focus on {target}"

        elif action == "type_text":
            import pyautogui
            import pyperclip
            pyperclip.copy(target)
            time.sleep(0.3)
            pyautogui.hotkey('ctrl', 'v')
            return True, f"Typed text"

        elif action == "press_hotkey":
            import pyautogui
            keys = target.split("+")
            pyautogui.hotkey(*keys)
            return True, f"Pressed {target}"

        elif action == "wait":
            duration = float(target) if target else 1.0
            time.sleep(duration)
            return True, f"Waited {duration}s"

        elif action == "notify":
            return True, step.get("message", "Step completed.")

    except Exception as e:
        return False, f"Step execution error ({action}): {e}"

    return False, f"Unknown action: {action}"

def execute_learned_workflow(workflow_key: str, speak_fn=None) -> tuple[bool, str]:
    """Executes all steps in a learned workflow."""
    workflows = load_workflows()
    wf = workflows.get(workflow_key)
    if not wf:
        return False, f"Workflow '{workflow_key}' not found."

    steps = wf.get("steps", [])
    last_spoken = f"Executing workflow: {workflow_key}."

    print(f"⚡ [Workflow Engine] Executing '{workflow_key}' ({len(steps)} steps)...")

    for i, step in enumerate(steps, 1):
        label = step.get("label", f"Step {i}")
        print(f"   ▶ Step {i}: {label}")
        success, msg = execute_workflow_step(step)
        if step.get("action") == "notify":
            last_spoken = step.get("message", msg)

    if speak_fn and last_spoken:
        speak_fn(last_spoken, blocking=True)

    return True, last_spoken

def match_and_run_workflow(user_text: str, speak_fn=None) -> tuple[bool, str]:
    """Check if user_text matches any learned workflow trigger."""
    clean = user_text.lower().strip()
    clean = re.sub(r'[^\w\s]', '', clean)
    workflows = load_workflows()

    # 1. Direct match on key or aliases
    for key, wf in workflows.items():
        if key in clean or clean in key:
            return execute_learned_workflow(key, speak_fn=speak_fn)
        for alias in wf.get("aliases", []):
            alias_clean = re.sub(r'[^\w\s]', '', alias.lower())
            if alias_clean in clean or clean in alias_clean:
                return execute_learned_workflow(key, speak_fn=speak_fn)

    # 2. Teaching intent detection:
    # "learn: when I say X, do Y" or "remember when I say X, do Y"
    teach_match = re.search(r'\b(?:learn|remember)\s+(?:that\s+)?when\s+i\s+say\s+["\']?([^"\',]+)["\']?\s*(?:then|do|,)\s*(.+)', clean)
    if teach_match:
        trigger = teach_match.group(1).strip()
        raw_actions = teach_match.group(2).strip()
        # Parse actions
        steps = []
        if "whatsapp" in raw_actions:
            steps.append({"action": "open_url", "target": "https://web.whatsapp.com", "label": "Open WhatsApp Web"})
            steps.append({"action": "notify", "message": f"Opened WhatsApp for {trigger}"})
        elif "chrome" in raw_actions:
            steps.append({"action": "launch_app", "target": "chrome", "label": "Open Chrome"})
        elif "chatgpt" in raw_actions:
            steps.append({"action": "open_url", "target": "https://chatgpt.com", "label": "Open ChatGPT"})

        if steps:
            learn_new_workflow(trigger, steps, description=raw_actions)
            reply = f"I have learned this workflow, Gagan. Whenever you say '{trigger}', I will execute it."
            if speak_fn:
                speak_fn(reply, blocking=True)
            return True, reply

    return False, ""

