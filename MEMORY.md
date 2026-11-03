# 🧠 GAGAN AI (GAGAN RAJPUT) — AGENT MEMORY & HANDOFF FILE

> **READ THIS FIRST.** This file is the single source of truth for any AI agent
> continuing work on this project. It tells you where we stopped, what's done,
> what's next, and how everything fits together.

---

## 🔑 PROJECT IDENTITY

| Field | Value |
|---|---|
| **Assistant Name** | **Gagan** (or **Gagan Rajput**) |
| **Wake Word** | **"Hey Gagan"** |
| **Workspace** | `d:\Desktop\gaganAI` |
| **Owner / Creator** | Gagan Rajput, B.Tech CSE, NIT Jalandhar |
| **OS** | Windows 11 |
| **Hardware** | Intel i7 11th Gen, 16 GB RAM, 512 GB SSD, NO GPU |
| **Budget** | ₹0 recurring/month |
| **Goal** | The most capable personal AI assistant named Gagan with zero cost |

---

## 📌 CURRENT STATUS

| Item | Status |
|---|---|
| **Strategy Document** | ✅ COMPLETE — `JARVIS-AI-Strategy.md` |
| **Phase Plans** | ✅ COMPLETE — `phases/PHASE-*.md` |
| **Environment Keys** | ✅ READY — `.env` file has all API keys |
| **Phase 1: Foundation** | ✅ COMPLETE — Telegram live & verified on Phi-4 Mini |
| **Phase 2: Productivity** | 🔲 NOT STARTED |
| **Phase 3: Voice** | 🔲 NOT STARTED |
| **Phase 4: Automation** | 🔲 NOT STARTED |
| **Phase 5: Polish** | 🔲 NOT STARTED |

> **LAST UPDATED:** 2026-11-02T16:48:00+05:30
> **LAST AGENT ACTION:** Completed Phase 1 Foundation. Configured `ollama/phi4-mini:latest` as primary model for fast daily tasks on CPU, `ollama/qwen2.5:7b` as first fallback, followed by Groq and Gemini cloud APIs. Configured `tools.profile: "messaging"` to prevent tool-prompt bloat and context overflow. Wiped clogged SQLite sessions and verified live Telegram messaging end-to-end: inbound message received from Gagan (`7845751251`) and outbound reply delivered successfully.

---

## 🔐 AVAILABLE CREDENTIALS (in `.env`)

| Key | Provider | Status |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Telegram BotFather | ✅ Ready |
| `GEMINI_API_KEY` | Google AI Studio | ✅ Ready |
| `GROQ_API_KEY` | Groq Cloud | ✅ Ready |
| `CLOUDFLARE_API_TOKEN` | Cloudflare Workers AI | ✅ Ready |
| `CLOUDFLARE_ACCOUNT_ID` | Cloudflare | ✅ Ready |
| `GMAIL_OAUTH` | Google Cloud Console | ✅ 6 Accounts Connected & Active |
| `CALENDAR_OAUTH` | Google Cloud Console | ✅ Connected (`gagansokhal077@gmail.com`) |

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
  ├─ Primary daily chat → Phi-4-mini (3.8B, local Ollama, ~3.7s CPU)
  ├─ Complex reasoning  → Qwen 2.5 7B (local Ollama, ~23s CPU)
  ├─ Heavy cloud task   → Groq API (openai/gpt-oss-120b, cloud speed)
  └─ Cloud fallback     → Gemini Flash API (free)
```

### Voice Pipeline

```
Mic → OpenWakeWord("Hey Gagan") → whisper.cpp(base.en) → OpenClaw → Piper TTS/Edge-TTS → Speaker
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
4. **Do not send passwords, recovery codes, or sensitive personal data to Telegram while Groq is primary** — cloud routing is enabled for responsive replies
5. **Set Ollama `num_ctx: 16384`** — OpenClaw's agent/tool prompt needs more than the previous 4K local context
6. **Use Q4_K_M quantization** — best quality/size ratio for 16 GB RAM
7. **Close Chrome during heavy LLM inference** — frees 2–4 GB RAM
8. **Pin OpenClaw to a stable release** — don't use dev/nightly
9. **All email sending requires user approval** — never auto-send
10. **Update this MEMORY.md** after completing each phase step

---

## 📊 PROGRESS TRACKER

### Phase 1: Foundation
- [x] Install Node.js 20 LTS (v26.13.0)
- [x] Install Docker Desktop
- [x] Install Ollama (v0.40.13)
- [x] Pull Qwen 2.5 7B model
- [x] Pull Phi-4-mini model
- [x] Install & configure OpenClaw (v2026.10.9) in workspace sandbox
- [x] Connect OpenClaw to Ollama (primary: phi4-mini:latest, 1st fallback: qwen2.5:7b)
- [x] Configure Telegram bot channel (open DM policy)
- [x] Run `start_gagan_ai.ps1` in a persistent PowerShell window and verify a Telegram reply from @GaganjiBot
- [x] Configure Groq and Gemini fallbacks (Groq openai/gpt-oss-120b, Gemini gemini-2.5-flash)
- [x] Test tiered model routing
- [x] Create .gitignore & git init

### Phase 2: Productivity
- [x] Create Google Cloud project
- [x] Enable Gmail API & Calendar API
- [x] Set up OAuth 2.0 consent screen (Desktop App credentials)
- [x] Multi-Account OAuth token authentication (All 6 accounts connected with permanent offline refresh tokens)
- [x] Set `gagansokhal077@gmail.com` as ⭐ Primary Calendar
- [x] Connect `gagandeep.cs.25@nitj.ac.in` (College NITJ ID)
- [x] Connect `rajputdeveloper44@gmail.com`, `gaganrajput1008@gmail.com`, `gagancoder22@gmail.com`, `jaibabagi108@gmail.com`
- [x] Build multi-account email reading & categorization (College, Professional, Personal, Newsletters + Urgency & Deadlines)
- [x] Build email reply workflow (drafting & safe sending with audit log)
- [x] Configure Calendar manager (IST Asia/Kolkata timezone)
- [x] Build morning briefing routine (Gmail + Calendar + Action items)
- [x] Set up scheduled Windows Task Scheduler routines (7:00 AM, 9:00 AM, 6:00 PM)
- [x] Test Telegram delivery of live briefings and alerts (Messages #53, #54, #55 verified)

### Phase 3: Voice
- [ ] Install Python 3.11+
- [ ] Install OpenWakeWord
- [ ] Train custom "Hey Gagan" / "Gagan Rajput" wake word
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

