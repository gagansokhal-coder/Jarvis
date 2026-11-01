# Phase 5: Polish — Memory, Cloud Hosting & Hardening

> **Priority:** 🟢 MEDIUM — Makes JARVIS smarter and always-on
> **Estimated Time:** Ongoing
> **Dependencies:** Phases 1–4 COMPLETE
> **Status:** 🔲 NOT STARTED

---

## Overview

This phase transforms JARVIS from a tool into an intelligent companion:
1. **Persistent Memory** — Remembers conversations, preferences, context
2. **RAG Pipeline** — Retrieves relevant past interactions and documents
3. **Oracle Cloud** — 24/7 always-on Telegram bot (even when laptop is off)
4. **Security Hardening** — Audit, encrypt, and lock down everything
5. **Performance Tuning** — Optimize RAM, speed, and responsiveness
6. **Custom Skills** — Build JARVIS-specific automation routines

---

## Step 5.1: Persistent Memory with ChromaDB

### Install ChromaDB

```powershell
cd d:\Desktop\gaganAI
.\venv\Scripts\Activate.ps1
pip install chromadb sentence-transformers
```

### Set Up Vector Database

Create `d:\Desktop\gaganAI\memory\vector_store.py`:

```python
"""
JARVIS persistent vector memory.
Stores and retrieves conversation context using embeddings.
"""
import chromadb
from chromadb.config import Settings
from datetime import datetime

# Initialize persistent ChromaDB
client = chromadb.PersistentClient(
    path="d:/Desktop/gaganAI/memory/chroma_db",
    settings=Settings(anonymized_telemetry=False)
)

# Collections
conversations = client.get_or_create_collection(
    name="conversations",
    metadata={"description": "All JARVIS conversations"}
)

knowledge = client.get_or_create_collection(
    name="knowledge",
    metadata={"description": "Personal knowledge base"}
)

emails = client.get_or_create_collection(
    name="emails",
    metadata={"description": "Important email summaries"}
)


def remember(text: str, metadata: dict = None):
    """Store a piece of information in memory."""
    meta = metadata or {}
    meta["timestamp"] = datetime.now().isoformat()

    conversations.add(
        documents=[text],
        metadatas=[meta],
        ids=[f"conv_{datetime.now().timestamp()}"]
    )


def recall(query: str, n_results: int = 5) -> list:
    """Retrieve relevant memories for a query."""
    results = conversations.query(
        query_texts=[query],
        n_results=n_results
    )
    return results["documents"][0] if results["documents"] else []


def add_knowledge(fact: str, category: str = "general"):
    """Add a fact to the knowledge base."""
    knowledge.add(
        documents=[fact],
        metadatas=[{"category": category, "timestamp": datetime.now().isoformat()}],
        ids=[f"know_{datetime.now().timestamp()}"]
    )


def search_knowledge(query: str, n_results: int = 3) -> list:
    """Search the knowledge base."""
    results = knowledge.query(
        query_texts=[query],
        n_results=n_results
    )
    return results["documents"][0] if results["documents"] else []
```

### Pre-populate Knowledge Base

```python
# Run once to seed JARVIS with personal knowledge:
from memory.vector_store import add_knowledge

# College info
add_knowledge("I am a B.Tech CSE student at NIT Jalandhar", "personal")
add_knowledge("My college portal URL is https://...", "college")
add_knowledge("My HOD is Prof. [Name]", "college")
add_knowledge("Exam schedule is usually in December and May", "college")

# Preferences
add_knowledge("I prefer concise responses", "preferences")
add_knowledge("I use Windows 11", "system")
add_knowledge("My timezone is Asia/Kolkata (IST, UTC+5:30)", "system")

# Contacts
add_knowledge("Prof. Kumar teaches Data Structures, email: kumar@nitj.ac.in", "contacts")
# ... add more as needed
```

> **RAM Note:** ChromaDB with sentence-transformers uses ~500 MB RAM.
> If RAM is tight, use ChromaDB's built-in default embedding function
> instead of sentence-transformers.

**✅ Checkpoint:** Can store and retrieve contextual memories.

---

## Step 5.2: SQLite Conversation History

Create `d:\Desktop\gaganAI\memory\history.py`:

```python
"""
SQLite-based conversation history for JARVIS.
Stores full conversation logs, email records, and audit trails.
"""
import sqlite3
from datetime import datetime

DB_PATH = "d:/Desktop/gaganAI/memory/jarvis.db"


def init_db():
    """Create tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            channel TEXT NOT NULL,  -- 'telegram', 'voice', 'api'
            role TEXT NOT NULL,     -- 'user', 'assistant'
            message TEXT NOT NULL,
            model_used TEXT,
            tokens_used INTEGER
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS emails_sent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            to_address TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            approved_by TEXT NOT NULL  -- 'telegram', 'voice'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS commands_executed (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            command TEXT NOT NULL,
            approved BOOLEAN NOT NULL,
            result TEXT,
            exit_code INTEGER
        )
    """)

    conn.commit()
    conn.close()


def log_conversation(channel: str, role: str, message: str,
                     model: str = None, tokens: int = None):
    """Log a conversation turn."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO conversations (timestamp, channel, role, message, model_used, tokens_used) VALUES (?, ?, ?, ?, ?, ?)",
        (datetime.now().isoformat(), channel, role, message, model, tokens)
    )
    conn.commit()
    conn.close()


def get_recent_conversations(limit: int = 20) -> list:
    """Get recent conversation history."""
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT timestamp, channel, role, message FROM conversations ORDER BY id DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return rows


# Initialize on import
init_db()
```

**✅ Checkpoint:** All conversations and actions logged to SQLite.

---

## Step 5.3: Oracle Cloud Always-On Hosting (Optional)

> This step is OPTIONAL. It lets JARVIS respond on Telegram even when
> your laptop is off, using Oracle Cloud's free ARM VM.

### Register for Oracle Cloud

1. Go to https://cloud.oracle.com/
2. Sign up with your NIT email
3. Choose region: `ap-mumbai-1` (India)
4. You'll need an international-enabled debit/credit card for verification
5. Select "Always Free" tier

### Create ARM Instance

```
Shape: VM.Standard.A1.Flex
OCPUs: 2
RAM: 12 GB
OS: Ubuntu 22.04 (Canonical)
Boot Volume: 50 GB
```

> **"Out of host capacity" error:** Very common in Mumbai region. Try:
> - Different fault domains (FD-1, FD-2, FD-3)
> - Off-peak hours (2–5 AM IST)
> - Retry script running every 5 minutes
> - Temporarily upgrade to Pay-As-You-Go (still free within limits)

### Set Up the VM

```bash
# SSH into the instance
ssh -i your-key.pem ubuntu@<public-ip>

# Update system
sudo apt update && sudo apt upgrade -y

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a small model (12 GB RAM available)
ollama pull phi4-mini
# OR for better quality:
ollama pull qwen2.5:7b-instruct-q4_K_M

# Create swap file (important!)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Clone OpenClaw (lightweight Telegram-only config)
git clone https://github.com/openclaw/openclaw.git
cd openclaw
npm install

# Copy your .env (with Telegram token, Groq key, etc.)
nano .env  # Paste your credentials

# Start with pm2 for auto-restart
sudo npm install -g pm2
pm2 start npm --name jarvis -- start
pm2 save
pm2 startup
```

### Configure Dual-Mode Operation

```
When laptop is ON:
  → Local Ollama (fast, private, full features)
  → Oracle VM in standby mode

When laptop is OFF:
  → Oracle VM handles Telegram bot
  → Uses Groq API for inference (free, fast)
  → Limited features (no browser/desktop automation)
```

**✅ Checkpoint:** Telegram bot works 24/7, even when laptop is off.

---

## Step 5.4: Security Audit

### Checklist

- [ ] `.env` is in `.gitignore`
- [ ] No API keys in any committed files
- [ ] Ollama only on localhost:11434 (not 0.0.0.0)
- [ ] College portal password in OS credential manager (not .env)
- [ ] Gmail OAuth tokens in `credentials/` (gitignored)
- [ ] Shell command sandbox active with whitelist
- [ ] Email sending requires Telegram approval
- [ ] No sensitive data sent to Gemini free tier
- [ ] Oracle Cloud VCN blocks all inbound except SSH
- [ ] Telegram bot token is not shared publicly

### Encrypt Sensitive Config

```powershell
# Use Windows EFS to encrypt the credentials folder:
cipher /e d:\Desktop\gaganAI\credentials
cipher /e d:\Desktop\gaganAI\.env
```

### Rate Limit Protection

Add rate limiting to prevent abuse if someone discovers your Telegram bot:

```python
# In your Telegram handler:
from collections import defaultdict
import time

rate_limits = defaultdict(list)

def check_rate_limit(user_id: int, max_requests: int = 30, window: int = 60):
    """Allow max_requests per window seconds per user."""
    now = time.time()
    rate_limits[user_id] = [t for t in rate_limits[user_id] if now - t < window]
    if len(rate_limits[user_id]) >= max_requests:
        return False
    rate_limits[user_id].append(now)
    return True
```

**✅ Checkpoint:** Security audit passed. All items checked.

---

## Step 5.5: Performance Tuning

### RAM Budget (16 GB Total)

| Component | RAM Usage | Running When |
|---|---|---|
| Windows 11 | ~3.5 GB | Always |
| Ollama (Phi-4-mini loaded) | ~3 GB | Always |
| OpenClaw (Node.js) | ~300 MB | Always |
| OpenWakeWord | ~50 MB | Voice active |
| whisper.cpp | ~150 MB | During transcription |
| Piper/Edge-TTS | ~80 MB | During speech |
| ChromaDB | ~200 MB | When queried |
| Playwright (browser task) | ~500 MB | During browser tasks |
| **Total (idle)** | **~7 GB** | |
| **Total (active)** | **~8–10 GB** | |
| **Headroom** | **6–8 GB** | For Chrome, apps |

### Optimization Tips

1. **Keep Phi-4-mini as default** (not Qwen 7B) — saves 2.5 GB RAM
2. **Load Qwen 7B only on demand** — Ollama unloads after 5 min idle
3. **Set `OLLAMA_KEEP_ALIVE=5m`** in environment
4. **Close browser after automation tasks** — don't leave Playwright running
5. **Use edge-tts over Piper** when online — zero local RAM
6. **Limit ChromaDB collection sizes** — prune old conversations monthly

### Speed Optimization

```env
# Add to .env for faster Ollama performance:
OLLAMA_NUM_PARALLEL=1        # Single request (saves RAM)
OLLAMA_MAX_LOADED_MODELS=1   # Only one model at a time
OLLAMA_KEEP_ALIVE=5m         # Unload after 5 minutes idle
```

**✅ Checkpoint:** System runs smoothly with 6+ GB headroom.

---

## Step 5.6: Custom Skills & Refinement

### Ideas for Custom Skills

| Skill | Description |
|---|---|
| **Homework Helper** | Parse assignment PDFs, summarize requirements, set deadlines |
| **Code Review** | Review your code, suggest improvements, find bugs |
| **Study Timer** | Pomodoro technique with Telegram notifications |
| **Expense Tracker** | Log expenses via Telegram, generate monthly reports |
| **News Digest** | Fetch and summarize tech news daily |
| **Interview Prep** | Quiz you on DSA, system design topics |
| **Git Status** | Daily summary of your GitHub activity |
| **Weather** | Morning weather included in briefing |

### Building a Custom Skill Template

```python
"""
Template for a custom JARVIS skill.
Save in: d:\Desktop\gaganAI\automation\skills\your_skill.py
"""

SKILL_NAME = "your-skill-name"
SKILL_DESCRIPTION = "What this skill does"
SKILL_TRIGGERS = ["keyword1", "keyword2"]  # Natural language triggers


async def execute(params: dict) -> str:
    """
    Main skill logic.
    Args: params dict with user's request details
    Returns: string response to send back to user
    """
    # Your logic here
    result = "Skill result"
    return result


# Register with OpenClaw (check docs for actual registration method)
```

**✅ Checkpoint:** At least 3 custom skills created and working.

---

## Phase 5 Completion Criteria

- [ ] ChromaDB vector memory working
- [ ] SQLite conversation history logging
- [ ] Knowledge base pre-populated
- [ ] Oracle Cloud VM set up (optional)
- [ ] 24/7 Telegram fallback working (optional)
- [ ] Security audit complete
- [ ] Performance optimized (under 10 GB RAM idle)
- [ ] At least 3 custom skills built
- [ ] MEMORY.md updated with Phase 5 status = ✅ COMPLETE

---

## 🎉 PROJECT COMPLETE

When all 5 phases are done, you'll have:

- ✅ A personal AI assistant that responds to "Hey Jarvis"
- ✅ Email management with smart categorization and reply drafting
- ✅ Automated morning briefings delivered to Telegram
- ✅ Calendar management and deadline tracking
- ✅ Browser automation for college portal and web tasks
- ✅ Desktop control (launch apps, system status, screenshots)
- ✅ Remote control via Telegram from anywhere
- ✅ Persistent memory that learns your preferences
- ✅ Scheduled routines running automatically
- ✅ All running at ₹0/month cost

**Congratulations, you've built JARVIS! 🚀**

