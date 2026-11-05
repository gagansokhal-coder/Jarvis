"""
GAGAN AI - TACTICAL CYBERPUNK MINI CONSOLE (HACKER GUI)
Features:
- Compact, dangerous hacker aesthetic (Obsidian Black, Neon Matrix Green, Danger Crimson, Cyber Cyan)
- ChatGPT/Gemini-style chat history sidebar (create, view, delete, optimize memory)
- Real-time conversation with local Ollama AI Brain (Phi-4-mini)
- Direct terminal command executor (run PowerShell/shell commands directly inside the console)
- Seamless voice & text synchronization
- IPC Signal listener to pop up instantly when commanded via voice ("Hey Gagan, open text option")
"""

import os
import sys
import time
import datetime
import json
import threading
import subprocess
import requests
import customtkinter as ctk

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from voice.chat_manager import ChatManager
from voice.tts_engine import speak

DATA_DIR = os.path.join(BASE_DIR, "data")
SIGNAL_FILE = os.path.join(DATA_DIR, "gui_trigger.signal")
OLLAMA_API = "http://127.0.0.1:11434/api/generate"

# Cyberpunk Hacker Palette
COLOR_BG_DARK = "#07090e"
COLOR_PANEL = "#0d1117"
COLOR_BORDER = "#1f2937"
COLOR_ACCENT_GREEN = "#00ff66"
COLOR_ACCENT_CYAN = "#00e5ff"
COLOR_ACCENT_RED = "#ff003c"
COLOR_TEXT_MAIN = "#e6edf3"
COLOR_TEXT_MUTED = "#8b949e"
COLOR_CARD_USER = "#131a24"
COLOR_CARD_AI = "#0e1a14"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("green")

class HackerConsole(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GAGAN // TACTICAL CYBER_CORE v3.0")
        self.geometry("920x620")
        self.minsize(780, 500)
        self.configure(fg_color=COLOR_BG_DARK)

        self.active_session_id = ChatManager.get_active_session()
        self.conversation_context = None

        self._build_ui()
        self._load_sessions_list()
        self._load_active_messages()

        # Hide on close button instead of destroying, so it reopens instantly on voice command
        self.protocol("WM_DELETE_WINDOW", self.withdraw)

        # Start background signal listener to show window on voice command
        self._start_ipc_listener()

    def _build_ui(self):
        # Top Tactical Header
        self.header_frame = ctk.CTkFrame(self, height=48, fg_color=COLOR_PANEL, corner_radius=0, border_width=1, border_color=COLOR_BORDER)
        self.header_frame.pack(fill="x", side="top")

        self.lbl_status = ctk.CTkLabel(
            self.header_frame,
            text=" ● SYSTEM ONLINE // PHI-4 CORE // 24/7 SENTINEL",
            font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
            text_color=COLOR_ACCENT_GREEN
        )
        self.lbl_status.pack(side="left", padx=16, pady=8)

        self.btn_optimize = ctk.CTkButton(
            self.header_frame,
            text="⚡ OPTIMIZE MEMORY",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            fg_color="#1a2332",
            hover_color="#223044",
            text_color=COLOR_ACCENT_CYAN,
            border_width=1,
            border_color=COLOR_ACCENT_CYAN,
            width=130,
            height=28,
            command=self.optimize_memory
        )
        self.btn_optimize.pack(side="right", padx=8, pady=8)

        self.btn_new_chat = ctk.CTkButton(
            self.header_frame,
            text="＋ NEW THREAD",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            fg_color="#12281e",
            hover_color="#1b3d2e",
            text_color=COLOR_ACCENT_GREEN,
            border_width=1,
            border_color=COLOR_ACCENT_GREEN,
            width=110,
            height=28,
            command=self.new_session
        )
        self.btn_new_chat.pack(side="right", padx=8, pady=8)

        # Main Container
        self.main_container = ctk.CTkFrame(self, fg_color=COLOR_BG_DARK, corner_radius=0)
        self.main_container.pack(fill="both", expand=True)

        # Left Sidebar (Chat History Sessions)
        self.sidebar_frame = ctk.CTkFrame(self.main_container, width=220, fg_color=COLOR_PANEL, corner_radius=0, border_width=1, border_color=COLOR_BORDER)
        self.sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)

        self.lbl_sidebar_title = ctk.CTkLabel(
            self.sidebar_frame,
            text="[ ARCHIVED LOGS ]",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=COLOR_TEXT_MUTED
        )
        self.lbl_sidebar_title.pack(fill="x", padx=12, pady=(12, 6))

        self.sidebar_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color="transparent")
        self.sidebar_scroll.pack(fill="both", expand=True, padx=4, pady=4)

        self.btn_delete_curr = ctk.CTkButton(
            self.sidebar_frame,
            text="🗑️ DELETE THIS CHAT",
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#2a1215",
            hover_color="#45181d",
            text_color=COLOR_ACCENT_RED,
            border_width=1,
            border_color=COLOR_ACCENT_RED,
            height=28,
            command=self.delete_current_session
        )
        self.btn_delete_curr.pack(fill="x", padx=8, pady=8)

        # Right Area: Chat History & Command Bar
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color=COLOR_BG_DARK, corner_radius=0)
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Chat Feed
        self.chat_scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color=COLOR_BG_DARK)
        self.chat_scroll.pack(fill="both", expand=True, padx=12, pady=10)

        # Bottom Command Bar
        self.input_frame = ctk.CTkFrame(self.content_frame, height=54, fg_color=COLOR_PANEL, border_width=1, border_color=COLOR_BORDER)
        self.input_frame.pack(fill="x", side="bottom", padx=12, pady=(0, 12))

        self.lbl_prompt_symbol = ctk.CTkLabel(
            self.input_frame,
            text="root@gagan-ai:~#",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color=COLOR_ACCENT_GREEN
        )
        self.lbl_prompt_symbol.pack(side="left", padx=(12, 6), pady=8)

        self.entry_input = ctk.CTkEntry(
            self.input_frame,
            placeholder_text="Enter tactical query, or '/cmd <powershell command>'...",
            font=ctk.CTkFont(family="Consolas", size=13),
            fg_color="#090d14",
            border_color="#21262d",
            text_color="#00ff66",
            height=36
        )
        self.entry_input.pack(side="left", fill="x", expand=True, padx=6, pady=8)
        self.entry_input.bind("<Return>", lambda e: self.send_input())

        self.btn_send = ctk.CTkButton(
            self.input_frame,
            text="TRANSMIT",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color="#00ff66",
            text_color="#000000",
            hover_color="#00cc55",
            width=90,
            height=36,
            command=self.send_input
        )
        self.btn_send.pack(side="right", padx=10, pady=8)

    def _load_sessions_list(self):
        """Render session buttons in the sidebar."""
        for widget in self.sidebar_scroll.winfo_children():
            widget.destroy()

        sessions = ChatManager.get_sessions()
        for s in sessions:
            sid = s["id"]
            title = s["title"]
            count = s["message_count"]
            time_short = s["updated_at"][5:16]

            is_active = (sid == self.active_session_id)
            btn_bg = "#1f2937" if is_active else "transparent"
            border_col = COLOR_ACCENT_GREEN if is_active else "#21262d"

            btn = ctk.CTkButton(
                self.sidebar_scroll,
                text=f"{title}\n[{count} msgs | {time_short}]",
                font=ctk.CTkFont(family="Consolas", size=11),
                anchor="w",
                fg_color=btn_bg,
                hover_color="#1b2330",
                text_color=COLOR_TEXT_MAIN if is_active else COLOR_TEXT_MUTED,
                border_width=1,
                border_color=border_col,
                height=42,
                command=lambda s_id=sid: self.switch_session(s_id)
            )
            btn.pack(fill="x", pady=3, padx=2)

    def _load_active_messages(self):
        """Render all messages of active session into scrollable area."""
        for widget in self.chat_scroll.winfo_children():
            widget.destroy()

        messages = ChatManager.get_messages(self.active_session_id)
        if not messages:
            # Welcoming tactical banner
            welcome_lbl = ctk.CTkLabel(
                self.chat_scroll,
                text="[ GAGAN AI TACTICAL MAINFRAME READY ]\nSpeak via microphone or type your directives below.\nTo execute shell commands, prefix with /cmd (e.g. /cmd ipconfig)",
                font=ctk.CTkFont(family="Consolas", size=12),
                text_color=COLOR_TEXT_MUTED,
                justify="center"
            )
            welcome_lbl.pack(pady=40)
            return

        for m in messages:
            self._render_message_bubble(m["role"], m["content"], m["source"], m["timestamp"])

        self._scroll_to_bottom()

    def _render_message_bubble(self, role: str, content: str, source: str = "text", timestamp: str = ""):
        is_user = (role == "user")
        header_text = f"▶ OPERATOR // GAGAN [{source.upper()}] - {timestamp[11:16]}" if is_user else f"⚡ GAGAN AI // CORE [{source.upper()}] - {timestamp[11:16]}"
        hdr_color = COLOR_ACCENT_CYAN if is_user else COLOR_ACCENT_GREEN
        bg_card = COLOR_CARD_USER if is_user else COLOR_CARD_AI
        border_col = "#1d2b3a" if is_user else "#122a1e"

        bubble_frame = ctk.CTkFrame(self.chat_scroll, fg_color=bg_card, border_width=1, border_color=border_col, corner_radius=6)
        bubble_frame.pack(fill="x", pady=6, padx=4)

        hdr_lbl = ctk.CTkLabel(
            bubble_frame,
            text=header_text,
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=hdr_color,
            anchor="w"
        )
        hdr_lbl.pack(fill="x", padx=10, pady=(6, 2))

        msg_lbl = ctk.CTkLabel(
            bubble_frame,
            text=content,
            font=ctk.CTkFont(family="Consolas", size=13),
            text_color=COLOR_TEXT_MAIN,
            justify="left",
            anchor="w",
            wraplength=640
        )
        msg_lbl.pack(fill="x", padx=10, pady=(0, 8))

    def _scroll_to_bottom(self):
        self.chat_scroll._parent_canvas.yview_moveto(1.0)

    def switch_session(self, session_id: str):
        self.active_session_id = session_id
        self._load_sessions_list()
        self._load_active_messages()

    def new_session(self):
        self.active_session_id = ChatManager.create_session()
        self._load_sessions_list()
        self._load_active_messages()
        self.entry_input.focus()

    def delete_current_session(self):
        ChatManager.delete_session(self.active_session_id)
        self.active_session_id = ChatManager.get_active_session()
        self._load_sessions_list()
        self._load_active_messages()

    def optimize_memory(self):
        pruned = ChatManager.optimize_memory(self.active_session_id, keep_recent=10)
        self.lbl_status.configure(text=f" ● MEMORY OPTIMIZED // Pruned {pruned} stale records", text_color=COLOR_ACCENT_CYAN)
        self._load_active_messages()
        self.after(3000, lambda: self.lbl_status.configure(text=" ● SYSTEM ONLINE // PHI-4 CORE // 24/7 SENTINEL", text_color=COLOR_ACCENT_GREEN))

    def send_input(self):
        raw_text = self.entry_input.get().strip()
        if not raw_text:
            return

        self.entry_input.delete(0, "end")
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Log User Message
        ChatManager.add_message(self.active_session_id, "user", raw_text, source="gui")
        self._render_message_bubble("user", raw_text, "gui", now_str)
        self._scroll_to_bottom()
        self._load_sessions_list()

        # 2. Check for Slash Command Shortcuts
        cmd_lower = raw_text.lower().strip()
        if cmd_lower in ["/lock", "/lockpc", "/lockscreen"]:
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
            return
        if cmd_lower in ["/new", "/newchat"]:
            self.new_session()
            return
        if cmd_lower in ["/optimize", "/opt"]:
            self.optimize_memory()
            return
        if cmd_lower in ["/delete", "/del"]:
            self.delete_current_session()
            return
        if cmd_lower in ["/exit", "/quit"]:
            self.destroy()
            return
        if cmd_lower in ["/clear", "/cls"]:
            for widget in self.chat_scroll.winfo_children():
                widget.destroy()
            return

        # 3. Check for Direct System Shell Commands
        common_cmds = ["ipconfig", "systeminfo", "dir", "whoami", "calc", "notepad", "tasklist", "netstat", "hostname"]
        if raw_text.startswith("/cmd ") or any(raw_text.startswith(c) for c in common_cmds):
            cmd = raw_text[5:].strip() if raw_text.startswith("/cmd ") else raw_text
            self._execute_terminal_command(cmd)
            return

        # 3.5 General AI Autonomous Agent (Full laptop access & actions)
        try:
            from automation.general_agent import process_general_directive
            handled, action_reply = process_general_directive(raw_text)
            if handled:
                ChatManager.add_message(self.active_session_id, "assistant", action_reply, source="ai")
                self._render_message_bubble("assistant", action_reply, "ai", now_str)
                self._scroll_to_bottom()
                self.lbl_status.configure(text=" ● GENERAL AI ONLINE // LAPTOP AGENT READY", text_color=COLOR_ACCENT_GREEN)
                return
        except Exception as e:
            print(f"General AI error: {e}")

        # 4. Query Ollama AI Brain in background thread so UI doesn't freeze
        threading.Thread(target=self._process_ai_query, args=(raw_text,), daemon=True).start()

    def _execute_terminal_command(self, cmd: str):
        def _run():
            try:
                res = subprocess.run(
                    ["powershell.exe", "-Command", cmd],
                    capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15
                )
                output = res.stdout if res.stdout else res.stderr
                if not output.strip():
                    output = f"Command '{cmd}' executed successfully (no stdout)."
            except Exception as e:
                output = f"Execution error: {e}"

            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ChatManager.add_message(self.active_session_id, "assistant", output, source="cmd")
            self.after(0, lambda: self._render_message_bubble("assistant", output, "cmd", now_str))
            self.after(0, self._scroll_to_bottom)

        threading.Thread(target=_run, daemon=True).start()

    def _process_ai_query(self, user_text: str):
        self.lbl_status.configure(text=" ● PROCESSING DIRECTIVE // CONTACTING PHI-4...", text_color=COLOR_ACCENT_CYAN)

        context_msgs = ChatManager.get_recent_history_context(self.active_session_id, limit=6)
        formatted_history = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in context_msgs[:-1]])

        sys_prompt = (
            "You are Gagan AI, an advanced, elite, personal AI assistant for Gagan Rajput. "
            "Tone: sharp, intelligent, highly respectful, tactical, and capable. "
            "Never call yourself JARVIS. Your name is Gagan AI."
        )

        full_prompt = f"{formatted_history}\nUSER: {user_text}\nGAGAN AI:" if formatted_history else user_text

        payload = {
            "model": "phi4-mini:latest",
            "prompt": full_prompt,
            "system": sys_prompt,
            "stream": False,
            "options": {"temperature": 0.4, "num_predict": 120}
        }

        try:
            resp = requests.post(OLLAMA_API, json=payload, timeout=30)
            data = resp.json()
            ai_reply = data.get("response", "Could not generate reply.")
        except Exception as e:
            ai_reply = f"Error communicating with AI Core: {e}"

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ChatManager.add_message(self.active_session_id, "assistant", ai_reply, source="gui")

        self.after(0, lambda: self._render_message_bubble("assistant", ai_reply, "gui", now_str))
        self.after(0, self._scroll_to_bottom)
        self.after(0, lambda: self.lbl_status.configure(text=" ● SYSTEM ONLINE // PHI-4 CORE // 24/7 SENTINEL", text_color=COLOR_ACCENT_GREEN))

    def _start_ipc_listener(self):
        """Polls for GUI trigger signals written by voice loop or daemon."""
        def _check():
            if os.path.exists(SIGNAL_FILE):
                try:
                    with open(SIGNAL_FILE, "r") as f:
                        sig = f.read().strip()
                    os.remove(SIGNAL_FILE)
                    if sig == "show":
                        self.deiconify()
                        self.lift()
                        self.focus_force()
                        self.entry_input.focus()
                        self._load_active_messages()
                except Exception:
                    pass
            self.after(500, _check)

        self.after(500, _check)

def show_gui():
    """Trigger the GUI to appear or launch."""
    with open(SIGNAL_FILE, "w") as f:
        f.write("show")

if __name__ == "__main__":
    app = HackerConsole()
    app.mainloop()
