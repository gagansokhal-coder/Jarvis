# Phase 1: Foundation — Install Core Infrastructure

> **Priority:** 🔴 CRITICAL — Everything depends on this
> **Estimated Time:** 3–4 days
> **Dependencies:** None
> **Status:** ✅ COMPLETE

---

## Overview

This phase sets up the three pillars:
1. **Ollama** — Local LLM inference (zero cost AI brain)
2. **OpenClaw** — Agent orchestration platform (the JARVIS backbone)
3. **Telegram Bot** — Primary remote control interface

After Phase 1, you will have a working AI assistant you can chat with
via Telegram that runs entirely on your laptop.

---

## Prerequisites Checklist

- [x] Windows 11 machine with 16 GB RAM
- [x] `.env` file with API keys (Telegram, Gemini, Groq, Cloudflare)
- [x] GitHub Student Pack active
- [ ] Stable internet connection for initial downloads (~5 GB total)

---

## Step 1.1: Install System Dependencies

### Install Node.js 20 LTS

```powershell
# Check if already installed
node --version

# If not installed:
winget install OpenJS.NodeJS.LTS
# Close and reopen terminal after install
# Verify:
node --version   # Should show v20.x or v22.x
npm --version
```

### Install Git (if not already)

```powershell
winget install Git.Git
git --version
```

### Install Python 3.11+ (for voice pipeline later, but install now)

```powershell
winget install Python.Python.3.11
# Close and reopen terminal
python --version   # Should show 3.11.x
pip --version
```

### Install Docker Desktop (optional — OpenClaw can run without it)

```powershell
# Only if you want Docker-based deployment:
winget install Docker.DockerDesktop
# Restart PC after install
# Note: Docker uses ~2 GB RAM. Skip if RAM is tight.
```

> **Decision Point:** If RAM is a concern, skip Docker and run OpenClaw
> directly via Node.js. The guide covers both paths.

**✅ Checkpoint:** `node --version`, `python --version`, `git --version` all work.

---

## Step 1.2: Install & Configure Ollama

### Install Ollama

```powershell
winget install Ollama.Ollama
# Ollama starts automatically as a background service
# Verify it's running:
curl http://localhost:11434
# Should return: "Ollama is running"
```

### Pull Models

```powershell
# Primary reasoning model (~4.5 GB download)
ollama pull qwen2.5:7b-instruct-q4_K_M

# Fast model for quick tasks (~2.3 GB download)
ollama pull phi4-mini

# Test that models work:
ollama run phi4-mini "Say hello in exactly 5 words"
# Should respond in ~1-2 seconds

ollama run qwen2.5:7b-instruct-q4_K_M "Explain recursion in 2 sentences"
# Should respond in ~3-5 seconds
```

### Configure Ollama for Performance

Create/edit `%USERPROFILE%\.ollama\config.json`:

```json
{
  "num_ctx": 4096,
  "num_thread": 8
}
```

> **Why `num_ctx: 4096`?** Default is 32K+ which eats ~6 GB RAM for the
> KV cache alone. 4096 tokens is plenty for assistant interactions and
> uses only ~500 MB.

### Verify Ollama API

```powershell
# Test the API endpoint that OpenClaw will use:
curl http://localhost:11434/api/generate -d '{
  "model": "phi4-mini",
  "prompt": "Hello",
  "stream": false
}'
```

**✅ Checkpoint:** Both models respond. Ollama API at localhost:11434 works.

---

## Step 1.3: Install & Configure OpenClaw

### Clone OpenClaw

```powershell
cd d:\Desktop\gaganAI
git clone https://github.com/openclaw/openclaw.git
cd openclaw
```

### Install Dependencies

```powershell
npm install
```

### Configure Environment

Copy your `.env` keys into OpenClaw's config. OpenClaw reads from its own
`.env` file inside its directory:

```powershell
# Copy the parent .env and add OpenClaw-specific settings
copy ..\.env .env
```

Then edit `openclaw/.env` to add these OpenClaw-specific variables:

```env
# --- From parent .env (already there) ---
TELEGRAM_BOT_TOKEN=<your-token>
GEMINI_API_KEY=<your-key>
GROQ_API_KEY=<your-key>
CLOUDFLARE_API_TOKEN=<your-token>
CLOUDFLARE_ACCOUNT_ID=<your-id>

# --- OpenClaw-specific config ---
# Primary model (local Ollama)
DEFAULT_MODEL_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b-instruct-q4_K_M

# Fast model for routing
FAST_MODEL_PROVIDER=ollama
FAST_MODEL=phi4-mini

# Cloud fallbacks
GEMINI_MODEL=gemini-2.0-flash
GROQ_MODEL=llama-3.3-70b-versatile

# Telegram channel
TELEGRAM_ENABLED=true

# Security
ALLOW_SHELL_EXECUTION=true
REQUIRE_APPROVAL_FOR_SEND=true

# Memory
PERSISTENCE_ENABLED=true
DATA_DIR=./data
```

> **IMPORTANT:** Read OpenClaw's actual documentation for the exact env var
> names. The above are representative — the actual config format may differ.
> Run `npm run setup` or check `openclaw/docs/` for the official config guide.

### Start OpenClaw

```powershell
# First-time setup (may create databases, download dependencies):
npm run setup

# Start the server:
npm start
# OR for development mode with auto-reload:
npm run dev
```

**✅ Checkpoint:** OpenClaw starts without errors. Check logs for "Connected to Ollama" and "Telegram bot started".

---

## Step 1.4: Configure Telegram Bot

### Verify Bot Token

Your Telegram bot token is already in `.env`. Verify the bot exists:

1. Open Telegram on your phone
2. Search for your bot by its username
3. Send `/start`
4. You should get a response from OpenClaw

### Test Basic Interactions

Send these messages to your Telegram bot:

```
Hello, who are you?
What time is it?
Tell me a joke
Summarize this: [paste any paragraph]
```

### Configure Bot Commands (via BotFather)

Open @BotFather in Telegram and set commands for your bot:

```
/setcommands
```

Then paste:
```
briefing - Get your morning briefing
emails - Check your emails
schedule - View today's schedule
status - System status
help - List available commands
```

**✅ Checkpoint:** You can chat with JARVIS via Telegram and get intelligent responses powered by your local Qwen 2.5 7B model.

---

## Step 1.5: Configure Cloud Model Fallbacks

### Test Gemini Integration

```powershell
# Quick test of your Gemini API key:
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=$env:GEMINI_API_KEY" `
  -H "Content-Type: application/json" `
  -d '{"contents":[{"parts":[{"text":"Hello"}]}]}'
```

### Test Groq Integration

```powershell
# Quick test of your Groq API key:
curl https://api.groq.com/openai/v1/chat/completions `
  -H "Authorization: Bearer $env:GROQ_API_KEY" `
  -H "Content-Type: application/json" `
  -d '{"model":"llama-3.3-70b-versatile","messages":[{"role":"user","content":"Hello"}]}'
```

### Configure Model Routing in OpenClaw

The routing logic should follow this priority:

```
1. LOCAL (Ollama Phi-4-mini)    → Fast, simple tasks, classification
2. LOCAL (Ollama Qwen 2.5 7B)  → Complex reasoning, function calling
3. CLOUD (Groq Llama 70B)      → When local is too slow or quality needed
4. CLOUD (Gemini Flash)         → Final fallback, long context tasks
```

> **Privacy Rule:** Configure routing so that messages containing email
> content, passwords, or personal data NEVER go to Gemini (it trains on
> free-tier data). Local Ollama or Groq (doesn't train) only.

**✅ Checkpoint:** All four model endpoints respond. Routing is configured.

---

## Step 1.6: Create .gitignore

```powershell
cd d:\Desktop\gaganAI
```

Create `.gitignore`:

```gitignore
# Secrets
.env
*.env
credentials/
*_token.json
*_secret.json

# Models (too large for git)
models/
*.gguf
*.bin

# Runtime
node_modules/
__pycache__/
*.pyc
logs/
data/
chroma_db/
*.db

# OS
Thumbs.db
Desktop.ini
.DS_Store

# IDE
.vscode/
.idea/
*.swp
```

### Initialize Git Repo

```powershell
cd d:\Desktop\gaganAI
git init
git add .gitignore MEMORY.md JARVIS-AI-Strategy.md phases/
git commit -m "Initial project setup: strategy, memory, and phase plans"
```

**✅ Checkpoint:** Git repo initialized. Secrets excluded.

---

## Phase 1 Completion Criteria

All of these must be true before moving to Phase 2:

- [x] Node.js 20+ installed and working (v26.13.0)
- [x] Python 3.11+ installed and working (3.12.7)
- [x] Ollama installed, running at localhost:11434 (v0.40.13)
- [x] Qwen 2.5 7B and Phi-4-mini models pulled and tested
- [x] OpenClaw installed globally (v2026.10.9) and configured for workspace sandbox
- [x] Telegram bot responds to messages (Gateway live & connected: @GaganjiBot)
- [x] Gemini API key verified working (gemini-2.5-flash)
- [x] Groq API key verified working (llama-3.3-70b-versatile)
- [x] .gitignore created, git repo initialized
- [x] MEMORY.md updated with Phase 1 status = ✅ COMPLETE

---

## Troubleshooting

### Ollama won't start
```powershell
# Check if port 11434 is already in use:
netstat -ano | findstr 11434
# Kill conflicting process if needed:
taskkill /PID <pid> /F
# Restart Ollama:
ollama serve
```

### Out of memory when loading Qwen 7B
```powershell
# Close Chrome and other heavy apps first
# If still OOM, use smaller model:
ollama pull qwen2.5:3b-instruct-q4_K_M
# Update OLLAMA_MODEL in .env accordingly
```

### OpenClaw npm install fails
```powershell
# Clear npm cache:
npm cache clean --force
# Try with legacy peer deps:
npm install --legacy-peer-deps
```

### Telegram bot not responding
1. Check bot token is correct in `.env`
2. Check OpenClaw logs for Telegram errors
3. Verify bot isn't blocked or deleted in BotFather
4. Check internet connection

