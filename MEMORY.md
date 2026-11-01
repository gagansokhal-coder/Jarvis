# 🧠 JARVIS PROJECT — AGENT MEMORY & HANDOFF FILE

> **READ THIS FIRST.** This file is the single source of truth for any AI agent
> continuing work on this project. It tells you where we stopped, what's done,
> what's next, and how everything fits together.

---

## 🔑 PROJECT IDENTITY

| Field | Value |
|---|---|
| **Project Name** | Personal JARVIS AI Assistant |
| **Workspace** | `d:\Desktop\gaganAI` |
| **Owner** | Gagan Rajput, B.Tech CSE, NIT Jalandhar |
| **OS** | Windows 11 |
| **Hardware** | Intel i7 11th Gen, 16 GB RAM, 512 GB SSD, NO GPU |
| **Budget** | ₹0 recurring/month |
| **Goal** | Most capable personal AI assistant with zero cost |

---

## 📌 CURRENT STATUS

| Item | Status |
|---|---|
| **Strategy Document** | ✅ COMPLETE — `JARVIS-AI-Strategy.md` |
| **Phase Plans** | ✅ COMPLETE — `phases/PHASE-*.md` |
| **Environment Keys** | ✅ READY — `.env` file has all API keys |
| **Phase 1: Foundation** | 🔲 NOT STARTED |
| **Phase 2: Productivity** | 🔲 NOT STARTED |
| **Phase 3: Voice** | 🔲 NOT STARTED |
| **Phase 4: Automation** | 🔲 NOT STARTED |
| **Phase 5: Polish** | 🔲 NOT STARTED |

> **LAST UPDATED:** 2026-11-02T00:33:00+05:30
> **LAST AGENT ACTION:** Created all phase plans and memory file

---

## 🔐 AVAILABLE CREDENTIALS (in `.env`)

| Key | Provider | Status |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram BotFather | ✅ Ready |
| `GEMINI_API_KEY` | Google AI Studio | ✅ Ready |
| `GROQ_API_KEY` | Groq Cloud | ✅ Ready |
| `CLOUDFLARE_API_TOKEN` | Cloudflare Workers AI | ✅ Ready |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare | ✅ Ready |
| `GMAIL_OAUTH` | Google Cloud Console | 🔲 Not yet created |
| `CALENDAR_OAUTH` | Google Cloud Console | 🔲 Not yet created |

### Student Benefits Available

- ✅ GitHub Student Developer Pack (2 years remaining)
- ✅ GitHub Copilot (free)
- ✅ JetBrains IDEs (free)
- ✅ Azure $100 credits (available through pack)
- 🔲 Oracle Cloud Always Free (not yet registered)

---

## 🏗️ ARCHITECTURE DECISION RECORD

### Core Platform: **OpenClaw** (self-hosted)

**Why:** First-class Telegram, Gmail, Calendar, scheduled tasks, remote
control. 400K stars, massive community, MIT license. Dodaios was considered
but lacks native messaging app and email integrations.

### AI Inference: **Tiered Routing**

```
User request → Router
  ├─ Simple/fast tasks → Phi-4-mini (3.8B, local, ~30 tok/s)
  ├─ Complex reasoning → Qwen 2.5 7B (local, ~10 tok/s)
  ├─ Heavy/long tasks  → Groq API (Llama 70B, free, cloud speed)
  └─ Fallback          → Gemini Flash API (free)
```

### Voice Pipeline

```
Mic → OpenWakeWord("Hey Jarvis") → whisper.cpp(base.en) → OpenClaw → Piper TTS/Edge-TTS → Speaker
```

### Key Tech Choices

| Decision | Choice | Reason |
|---|---|---|
| Agent framework | OpenClaw | Best integrations for our use case |
| Local LLM runtime | Ollama | Simplest Windows setup, wraps llama.cpp |
| Primary model | Qwen 2.5 7B Q4_K_M | Best reasoning at 7B, great function calling |
| Fast model | Phi-4-mini 3.8B | 30 tok/s on CPU, good for quick tasks |
| Wake word | OpenWakeWord | Free, Apache 2.0, trainable |
| STT | whisper.cpp (base.en) | Standalone .exe, ~150 MB, high accuracy |
| TTS (offline) | Piper TTS | Fast, lightweight ONNX, MIT |
| TTS (online) | edge-tts | Free Microsoft neural voices, studio quality |
| Browser automation | browser-use + Playwright | AI-driven, Python, works with LLMs |
| Vector memory | ChromaDB | Lightweight, local, Python |
| Database | SQLite | Zero-config, built into Python |
| Telegram library | grammY (via OpenClaw) | Built into OpenClaw's channel system |
| Credential storage | python-keyring | OS-native credential manager |

---

## 📁 PROJECT FILE STRUCTURE (Planned)

```
d:\Desktop\gaganAI\
├── .env                          # API keys (NEVER commit to git)
├── .gitignore                    # Excludes .env, models, etc.
├── MEMORY.md                     # THIS FILE — agent handoff
├── JARVIS-AI-Strategy.md         # Master strategy document
├── phases/                       # Phase implementation guides
│   ├── PHASE-1-FOUNDATION.md
│   ├── PHASE-2-PRODUCTIVITY.md
│   ├── PHASE-3-VOICE.md
│   ├── PHASE-4-AUTOMATION.md
│   └── PHASE-5-POLISH.md
├── openclaw/                     # OpenClaw installation (Phase 1)
│   ├── config/
│   ├── skills/
│   └── data/
├── voice/                        # Voice pipeline scripts (Phase 3)
│   ├── wakeword/
│   ├── stt/
│   ├── tts/
│   └── bridge.py
├── automation/                   # Browser & desktop automation (Phase 4)
│   ├── browser/
│   ├── desktop/
│   └── scripts/
├── memory/                       # Persistent memory (Phase 5)
│   ├── chroma_db/
│   └── sqlite/
├── credentials/                  # OAuth tokens (local only, gitignored)
│   ├── gmail_token.json
│   └── calendar_token.json
└── logs/                         # Runtime logs
```

---

## 📋 PHASE EXECUTION ORDER

| Phase | File | Priority | Depends On | Est. Time |
|---|---|---|---|---|
| **Phase 1** | `phases/PHASE-1-FOUNDATION.md` | 🔴 CRITICAL | Nothing | 3–4 days |
| **Phase 2** | `phases/PHASE-2-PRODUCTIVITY.md` | 🔴 CRITICAL | Phase 1 | 4–5 days |
| **Phase 3** | `phases/PHASE-3-VOICE.md` | 🟡 HIGH | Phase 1 | 3–4 days |
| **Phase 4** | `phases/PHASE-4-AUTOMATION.md` | 🟡 HIGH | Phase 1 | 3–5 days |
| **Phase 5** | `phases/PHASE-5-POLISH.md` | 🟢 MEDIUM | All | Ongoing |

> **RULE:** Complete Phase 1 fully before starting any other phase.
> Phases 2, 3, 4 can be done in parallel after Phase 1.

---

## 🚨 CRITICAL RULES FOR ANY AGENT

1. **NEVER commit `.env` to git** — it contains live API tokens
2. **NEVER expose Ollama on 0.0.0.0** — always localhost:11434
3. **NEVER send private emails through Gemini free tier** — it trains on your data
4. **Use local Ollama for ALL private data** (emails, passwords, personal info)
5. **Set Ollama `num_ctx: 4096`** — saves ~3 GB RAM vs default 32K
6. **Use Q4_K_M quantization** — best quality/size ratio for 16 GB RAM
7. **Close Chrome during heavy LLM inference** — frees 2–4 GB RAM
8. **Pin OpenClaw to a stable release** — don't use dev/nightly
9. **All email sending requires user approval** — never auto-send
10. **Update this MEMORY.md** after completing each phase step

---

## 📊 PROGRESS TRACKER

### Phase 1: Foundation
- [ ] Install Node.js 20 LTS
- [ ] Install Docker Desktop
- [ ] Install Ollama
- [ ] Pull Qwen 2.5 7B model
- [ ] Pull Phi-4-mini model
- [ ] Clone & configure OpenClaw
- [ ] Connect OpenClaw to Ollama
- [ ] Configure Telegram bot channel
- [ ] Test basic chat via Telegram
- [ ] Configure Gemini & Groq fallbacks
- [ ] Test tiered model routing
- [ ] Create .gitignore

### Phase 2: Productivity
- [ ] Create Google Cloud project
- [ ] Enable Gmail API
- [ ] Enable Calendar API
- [ ] Set up OAuth 2.0 consent screen
- [ ] Generate OAuth credentials
- [ ] Configure Gmail skill in OpenClaw
- [ ] Test email reading
- [ ] Build email reply workflow (with approval)
- [ ] Configure Calendar skill
- [ ] Build morning briefing routine
- [ ] Set up scheduled cron tasks
- [ ] Test Telegram delivery of briefings

### Phase 3: Voice
- [ ] Install Python 3.11+
- [ ] Install OpenWakeWord
- [ ] Train custom "Hey Jarvis" wake word
- [ ] Download whisper.cpp Windows binary
- [ ] Download whisper base.en model
- [ ] Install Piper TTS + English voice
- [ ] Install edge-tts
- [ ] Build voice bridge script (bridge.py)
- [ ] Test full voice loop
- [ ] Create Windows startup shortcut

### Phase 4: Automation
- [ ] Install Playwright + Chromium
- [ ] Install browser-use
- [ ] Configure OpenClaw browser skill
- [ ] Build college portal automation
- [ ] Test natural language browser commands
- [ ] Configure shell execution sandbox
- [ ] Build PowerShell automation scripts
- [ ] Set up command whitelist

### Phase 5: Polish
- [ ] Set up ChromaDB for semantic memory
- [ ] Set up SQLite for conversation history
- [ ] Build personal knowledge base
- [ ] Register Oracle Cloud (optional 24/7 hosting)
- [ ] Security audit & hardening
- [ ] Performance tuning
- [ ] Create custom OpenClaw skills
- [ ] Documentation

---

## 🔗 QUICK REFERENCES

| Resource | URL |
|---|---|
| OpenClaw GitHub | https://github.com/openclaw/openclaw |
| OpenClaw Docs | https://openclaw.ai |
| Ollama | https://ollama.com |
| Qwen 2.5 Models | https://huggingface.co/Qwen |
| whisper.cpp Releases | https://github.com/ggerganov/whisper.cpp/releases |
| Piper TTS Releases | https://github.com/rhasspy/piper/releases |
| OpenWakeWord | https://github.com/dscripka/openWakeWord |
| browser-use | https://github.com/browser-use/browser-use |
| edge-tts | https://github.com/rany2/edge-tts |
| ChromaDB | https://github.com/chroma-core/chroma |
| Google Cloud Console | https://console.cloud.google.com |
| Gemini AI Studio | https://aistudio.google.com |
| Groq Console | https://console.groq.com |
| Telegram BotFather | https://t.me/BotFather |

