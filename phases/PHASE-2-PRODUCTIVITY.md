# Phase 2: Productivity — Gmail, Calendar & Morning Briefing

> **Priority:** 🔴 CRITICAL — Core JARVIS functionality
> **Estimated Time:** 4–5 days
> **Dependencies:** Phase 1 COMPLETE
> **Status:** 🔲 NOT STARTED

---

## Overview

This phase connects JARVIS to your digital life:
1. **Gmail** — Read, categorize, summarize, and reply to emails
2. **Google Calendar** — Check schedule, deadlines, meetings
3. **Morning Briefing** — Automated daily summary via Telegram
4. **Scheduled Routines** — Cron-like background automation

After Phase 2, saying "Jarvis, check my emails" or "prepare my morning
briefing" will actually work.

---

## Prerequisites

- [x] Phase 1 complete (OpenClaw + Ollama + Telegram working)
- [ ] Google account (personal Gmail)
- [ ] Access to Google Cloud Console (free, no CC required)

---

## Step 2.1: Set Up Google Cloud Project

### Create Project

1. Go to https://console.cloud.google.com
2. Click "Select a project" → "New Project"
3. Name: `jarvis-personal-assistant`
4. Organization: No organization
5. Click "Create"

### Enable APIs

In the Google Cloud Console:

```
1. Go to "APIs & Services" → "Library"
2. Search "Gmail API" → Click → Enable
3. Search "Google Calendar API" → Click → Enable
```

### Create OAuth Consent Screen

```
1. Go to "APIs & Services" → "OAuth consent screen"
2. User Type: External → Create
3. App name: "JARVIS Personal Assistant"
4. User support email: your-email@gmail.com
5. Developer contact: your-email@gmail.com
6. Click "Save and Continue"
7. Scopes → Add these:
   - https://www.googleapis.com/auth/gmail.readonly
   - https://www.googleapis.com/auth/gmail.send
   - https://www.googleapis.com/auth/gmail.modify
   - https://www.googleapis.com/auth/calendar.readonly
   - https://www.googleapis.com/auth/calendar.events
8. Save and Continue
9. Test users → Add your own Gmail address
10. Save
```

> **IMPORTANT:** Keep the app in "Testing" mode initially. Later, switch to
> "In Production" to avoid 7-day token expiry (single-user apps don't need
> Google verification).

### Create OAuth Credentials

```
1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: "Desktop app"
4. Name: "JARVIS Desktop"
5. Click "Create"
6. Download the JSON file
7. Save as: d:\Desktop\gaganAI\credentials\client_secret.json
```

Add to `.env`:
```env
GOOGLE_CLIENT_SECRET_PATH=./credentials/client_secret.json
GOOGLE_TOKEN_PATH=./credentials/gmail_token.json
```

**✅ Checkpoint:** Google Cloud project created, APIs enabled, OAuth credentials downloaded.

---

## Step 2.2: Configure Gmail Integration

### Install Gmail Skill in OpenClaw

Check OpenClaw's documentation for the Gmail/Google integration:

```powershell
cd d:\Desktop\gaganAI\openclaw

# If OpenClaw uses ClawHub skills:
# (Check actual command in OpenClaw docs)
npx openclaw skill install gmail
# OR
npx openclaw skill install google-workspace
```

### First-Time OAuth Authentication

The first time you access Gmail, a browser window will open asking you to
authorize JARVIS. Click through the "unverified app" warnings:

```
1. Browser opens → Select your Gmail account
2. "Google hasn't verified this app" → Click "Advanced"
3. Click "Go to JARVIS Personal Assistant (unsafe)"
4. Grant all requested permissions
5. "JARVIS wants to access your Google Account" → Allow
6. Token saved to credentials/gmail_token.json
```

### Test Gmail Reading

Send a test command via Telegram:

```
Check my unread emails
```

Expected response:
```
You have X unread emails:
• [sender] - [subject] - [preview]
• ...
```

### Build Email Categorization Prompt

Create a custom skill/prompt that categorizes emails:

```
Categorize each email as one of:
- 🎓 College (from .ac.in domains, professors, college administration)
- 💼 Professional (internships, companies, LinkedIn)
- 👤 Personal (friends, family)
- 📧 Newsletter/Promotion (subscriptions, marketing)

For each email, also identify:
- ⏰ Deadlines mentioned
- ❗ Urgency level (high/medium/low)
- 💬 Requires reply? (yes/no)
```

**✅ Checkpoint:** Can read and categorize emails via Telegram.

---

## Step 2.3: Build Email Reply Workflow

### The Approval Flow

```
User: "Reply to Professor Kumar's email"
JARVIS: [Fetches the email thread]
JARVIS: [Generates draft reply]
JARVIS: "Here's my draft reply:

  Dear Professor Kumar,
  Thank you for the feedback on my assignment...
  [draft text]

  📨 Send this reply?
  [✅ Send] [✏️ Edit] [❌ Cancel]"

User: [Clicks ✅ Send]
JARVIS: "✅ Email sent to Prof. Kumar"
```

### Implementation Notes

- Use Telegram inline keyboard buttons for Send/Edit/Cancel
- NEVER auto-send — always require explicit user approval
- For "Edit" — ask user what to change, regenerate, show again
- Store the draft in memory so user can modify it
- Log all sent emails in SQLite for audit trail

**✅ Checkpoint:** Can draft and send emails with user approval via Telegram.

---

## Step 2.4: Configure Google Calendar

### Install Calendar Skill

```powershell
# Check OpenClaw docs for exact command:
npx openclaw skill install google-calendar
```

### Test Calendar Reading

```
What's on my schedule today?
Do I have any meetings this week?
When is my next deadline?
```

### Build Calendar Commands

| Command | Action |
|---|---|
| "What's on my schedule today?" | List today's events |
| "Any meetings this week?" | List week's events |
| "When is my next exam?" | Search for exam-related events |
| "Block 2 hours for studying tomorrow" | Create a calendar event |
| "Remind me about assignment at 8 PM" | Create reminder event |

**✅ Checkpoint:** Can read and create calendar events via Telegram.

---

## Step 2.5: Build Morning Briefing Routine

### Create the Briefing Skill

The morning briefing combines Gmail + Calendar + LLM summary:

```
Trigger: Daily at 7:00 AM IST (or user-configured time)
Actions:
  1. Fetch unread emails from last 12 hours
  2. Fetch today's calendar events
  3. Fetch upcoming deadlines (next 7 days)
  4. Send everything to LLM for summarization
  5. Format as a clean briefing
  6. Send to Telegram
```

### Expected Output Format

```
🌅 Good Morning, Gagan! Here's your briefing for Nov 2, 2026:

📧 EMAILS (5 new)
• 🎓 Prof. Kumar — Assignment feedback (needs reply)
• 🎓 NIT Admin — Exam schedule update
• 💼 Google — Interview confirmation for Nov 5
• 👤 Mom — "Come home for Diwali?"
• 📧 GitHub — Weekly digest

📅 TODAY'S SCHEDULE
• 09:00 — Data Structures lecture (Room 203)
• 14:00 — Project meeting with team
• 16:00 — Career counseling session

⏰ UPCOMING DEADLINES
• Nov 3 — OS Assignment submission
• Nov 5 — Google interview (2 days!)
• Nov 8 — ML Project report

❗ ACTION ITEMS
• Reply to Prof. Kumar about assignment
• Prepare for Google interview
• Submit OS assignment by tomorrow

Have a great day! 🚀
```

### Configure Schedule

```powershell
# In OpenClaw config or via Telegram:
/schedule morning-briefing 07:00 daily
/schedule email-digest 09:00,18:00 daily
/schedule deadline-check */2 * * * *   # Every 2 hours
```

**✅ Checkpoint:** Morning briefing arrives on Telegram at 7 AM automatically.

---

## Step 2.6: Set Up Scheduled Tasks

### Available Routines

| Routine | Schedule | Delivery |
|---|---|---|
| Morning Briefing | 7:00 AM daily | Telegram |
| Email Digest | 9:00 AM, 6:00 PM | Telegram |
| Deadline Alerts | Every 2 hours | Telegram (only if deadlines within 48h) |
| Weekly Summary | Sunday 8:00 PM | Telegram |
| Inbox Zero Report | Friday 5:00 PM | Telegram |

### Implementation

Configure via OpenClaw's built-in scheduler:

```javascript
// Example routine config (check OpenClaw docs for actual format):
{
  "routines": [
    {
      "name": "morning-briefing",
      "cron": "0 7 * * *",
      "timezone": "Asia/Kolkata",
      "actions": ["fetch-emails", "fetch-calendar", "summarize", "send-telegram"]
    },
    {
      "name": "email-digest",
      "cron": "0 9,18 * * *",
      "timezone": "Asia/Kolkata",
      "actions": ["fetch-emails", "categorize", "send-telegram"]
    }
  ]
}
```

**✅ Checkpoint:** All scheduled routines are firing on time and delivering to Telegram.

---

## Phase 2 Completion Criteria

- [ ] Google Cloud project created with Gmail + Calendar APIs
- [ ] OAuth authentication working (tokens not expiring)
- [ ] Email reading and categorization working
- [ ] Email reply with approval workflow working
- [ ] Calendar reading working
- [ ] Morning briefing routine delivering at 7 AM
- [ ] Email digest routine working (9 AM, 6 PM)
- [ ] Deadline alert routine working
- [ ] MEMORY.md updated with Phase 2 status = ✅ COMPLETE

---

## Troubleshooting

### OAuth token expires every 7 days
```
1. Go to Google Cloud Console → OAuth consent screen
2. Change Publishing status from "Testing" to "In Production"
3. Since you're the only user, no verification needed
4. Tokens will now persist until manually revoked
```

### "Access blocked: This app's request is invalid"
```
1. Check redirect URI matches in Cloud Console
2. For Desktop apps, use: urn:ietf:wg:oauth:2.0:oob
3. Delete existing token file and re-authenticate
```

### Gmail API quota exceeded
```
- Personal use limits: 250 quota units/second/user
- If hit, implement exponential backoff
- Reduce polling frequency in scheduled tasks
```

### Calendar events showing wrong timezone
```
- Set timezone in OpenClaw config: Asia/Kolkata
- Verify Google Calendar default timezone
- Use IST (UTC+5:30) for all time displays
```

