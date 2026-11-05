import os
import sys
import time
import json
from datetime import datetime, timedelta
import zoneinfo

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from gmail_manager import (
    load_accounts_config,
    get_gmail_service_for_token,
    extract_body,
    categorize_email,
    mark_messages_as_read
)
from calendar_manager import get_calendar_service
from email_calendar_sync import parse_date_and_time, is_event_already_on_calendar
from telegram_sender import send_telegram_message

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(BASE_DIR, 'data', 'watcher_state.json')
IST = zoneinfo.ZoneInfo("Asia/Kolkata")
POLL_INTERVAL_SECONDS = 60  # Check every 60 seconds

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"accounts": {}}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def process_new_email(msg_data, account_email, cal_service, cal_account):
    """
    Analyzes a newly arrived email:
    1. Detects calendar events & auto-adds to primary calendar
    2. Sends high-priority Telegram alert for College, Career, Urgent, or Calendar events
    """
    subject = msg_data.get('subject', '')
    sender = msg_data.get('sender', '')
    body = msg_data.get('body', '')
    snippet = msg_data.get('snippet', '')
    category = msg_data.get('category', '👤 Personal')
    urgency = msg_data.get('urgency', 'LOW')
    deadline = msg_data.get('deadline')
    requires_reply = msg_data.get('requires_reply', False)

    is_nitj = "nitj" in account_email.lower()
    clean_sender = sender.split('<')[0].strip(' "\'')
    full_content = f"{subject}\n{body}\n{snippet}"

    # 1. Event Detection & Auto-Calendar Sync
    event_triggers = [
        'session', 'interview', 'webinar', 'examination', 'exam of course', 'quiz',
        'compulsory attendance', 'mandatory attendance', 'placement', 'hiring test',
        'online assessment', 'due date', 'submission deadline', 'venue:', 'date:'
    ]
    ignore_keywords = [
        'lost my', 'lost debit', 'lost card', 'lost charger', 'lost watch', 'lost phone',
        'found debit', 'found card', 'found watch', 'found phone', 'found keys', 'lost & found',
        'lost and found', 'blood requirement', 'blood donor'
    ]

    calendar_synced = False
    calendar_details = None

    if any(t in full_content.lower() for t in event_triggers) and not any(ik in full_content.lower() for ik in ignore_keywords):
        start_dt, end_dt, venue = parse_date_and_time(full_content)
        now = datetime.now(IST)
        if start_dt and start_dt >= (now - timedelta(hours=12)):
            clean_sub = subject.replace('Fwd:', '').replace('Reminder |', '').replace('Re:', '').strip()
            tag = "[NITJ]" if is_nitj else ("[Career]" if any(x in full_content.lower() for x in ['interview', 'assessment', 'internship', 'tcs', 'google']) else "[Event]")
            event_title = f"{tag} {clean_sub}"

            if not is_event_already_on_calendar(cal_service, clean_sub, start_dt, end_dt):
                event_body = {
                    'summary': event_title,
                    'description': f"Auto-synced by Gagan AI Watcher\nSource: {account_email}\nFrom: {clean_sender}\n\nSnippet: {snippet}",
                    'location': venue or ("NIT Jalandhar Campus" if is_nitj else ""),
                    'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'Asia/Kolkata'},
                    'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'Asia/Kolkata'},
                    'reminders': {
                        'useDefault': False,
                        'overrides': [{'method': 'popup', 'minutes': 60}, {'method': 'popup', 'minutes': 1440}],
                    },
                }
                try:
                    cal_service.events().insert(calendarId='primary', body=event_body).execute()
                    calendar_synced = True
                    calendar_details = {
                        "title": event_title,
                        "time": start_dt.strftime("%A, %d %b %Y (%I:%M %p IST)"),
                        "venue": venue or "Campus"
                    }
                    print(f"[{datetime.now(IST).strftime('%H:%M:%S')}] 📅 Auto-added event to Calendar: '{event_title}'")
                except Exception as e:
                    print(f"Calendar insert error: {e}", file=sys.stderr)

    # 2. Decide whether to send Instant Telegram Alert
    # Send for: College, Career, High Urgency, Deadlines, Calendar events, or Requires Reply
    should_alert = (
        is_nitj or
        "College" in category or
        "Professional" in category or
        calendar_synced or
        urgency == "HIGH" or
        requires_reply or
        deadline is not None
    )

    if should_alert:
        urg_icon = "🔴" if urgency == "HIGH" else ("🟡" if calendar_synced or requires_reply else "📫")
        lines = [f"{urg_icon} *NEW EMAIL RECEIVED*"]
        lines.append(f"• *Account:* `{account_email}`")
        lines.append(f"• *From:* {clean_sender}")
        lines.append(f"• *Subject:* _{subject}_")
        lines.append(f"• *Category:* {category}")

        if deadline:
            lines.append(f"• *Deadline Mentioned:* ⏰ {deadline}")
        if requires_reply:
            lines.append("• 💬 *Action:* Reply expected")

        if calendar_synced and calendar_details:
            lines.append(f"\n📅 *Auto-Added to Google Calendar (`{cal_account}`):*")
            lines.append(f"   • *Event:* {calendar_details['title']}")
            lines.append(f"   • *Timing:* {calendar_details['time']}")
            lines.append(f"   • *Venue:* {calendar_details['venue']}")

        # Format complete email content
        clean_body = body.strip() if body else snippet.strip()
        if len(clean_body) > 2500:
            preview_body = clean_body[:2500] + "\n\n...[Full email archived in Gagan AI storage]"
        else:
            preview_body = clean_body

        lines.append(f"\n📄 *Complete Message Content:*\n{preview_body}")

        # Save latest email record for instant voice, OpenClaw, and search queries
        latest_record = {
            "account": account_email,
            "sender": clean_sender,
            "subject": subject,
            "category": category,
            "urgency": urgency,
            "deadline": deadline,
            "body": clean_body,
            "received_at": datetime.now(IST).strftime("%Y-%m-%d %I:%M:%S %p IST")
        }
        try:
            data_dir = os.path.join(BASE_DIR, 'data')
            os.makedirs(data_dir, exist_ok=True)
            with open(os.path.join(data_dir, 'latest_email.json'), 'w', encoding='utf-8') as f:
                json.dump(latest_record, f, indent=2, ensure_ascii=False)
            with open(os.path.join(data_dir, 'latest_email.txt'), 'w', encoding='utf-8') as f:
                f.write(f"Account: {account_email}\nFrom: {clean_sender}\nSubject: {subject}\nReceived: {latest_record['received_at']}\nCategory: {category}\n\n{clean_body}")

            # Also mirror to OpenClaw workspace
            ws_dir = os.path.join(data_dir, 'workspace')
            os.makedirs(ws_dir, exist_ok=True)
            with open(os.path.join(ws_dir, 'LATEST_EMAIL.md'), 'w', encoding='utf-8') as f:
                f.write(f"# Latest Received Email\n- **Account:** `{account_email}`\n- **From:** {clean_sender}\n- **Subject:** {subject}\n- **Received:** {latest_record['received_at']}\n- **Category:** {category}\n\n## Content:\n```\n{clean_body}\n```\n")
        except Exception as e:
            print(f"Error saving latest email: {e}", file=sys.stderr)

        try:
            send_telegram_message("\n".join(lines))
            print(f"[{datetime.now(IST).strftime('%H:%M:%S')}] 📲 Telegram alert sent for {account_email}: '{subject[:30]}...'")
        except Exception as e:
            print(f"Telegram alert error: {e}", file=sys.stderr)

def watch_cycle(state, cal_service, cal_account):
    config = load_accounts_config()
    accounts = [a for a in config.get("accounts", []) if a.get("enabled", True)]
    state_accounts = state.setdefault("accounts", {})

    total_new = 0

    for acc in accounts:
        email = acc["email"]
        acc_state = state_accounts.setdefault(email, {"seen_ids": [], "initialized": False})
        seen_ids = set(acc_state.get("seen_ids", []))
        initialized = acc_state.get("initialized", False)

        try:
            service = get_gmail_service_for_token(acc["token_file"])
            # Fetch the latest 10 messages
            res = service.users().messages().list(userId='me', maxResults=10).execute()
            messages = res.get('messages', [])
        except Exception as e:
            continue

        if not messages:
            continue

        current_ids = [m['id'] for m in messages]

        # On very first run, initialize existing IDs so we don't spam 50 historical alerts
        if not initialized:
            acc_state["seen_ids"] = current_ids
            acc_state["initialized"] = True
            continue

        new_ids = [mid for mid in current_ids if mid not in seen_ids]

        if new_ids:
            total_new += len(new_ids)
            for mid in new_ids:
                try:
                    full_msg = service.users().messages().get(userId='me', id=mid, format='full').execute()
                    headers = {h['name'].lower(): h['value'] for h in full_msg.get('payload', {}).get('headers', [])}
                    sender = headers.get('from', 'Unknown Sender')
                    subject = headers.get('subject', '(No Subject)')
                    snippet = full_msg.get('snippet', '')
                    body = extract_body(full_msg.get('payload', {}))

                    cat_info = categorize_email(sender, subject, snippet, body)

                    msg_data = {
                        "id": mid,
                        "sender": sender,
                        "subject": subject,
                        "snippet": snippet,
                        "body": body,
                        "category": cat_info["category"],
                        "urgency": cat_info["urgency"],
                        "deadline": cat_info["deadline"],
                        "requires_reply": cat_info["requires_reply"]
                    }

                    process_new_email(msg_data, email, cal_service, cal_account)

                    # Auto mark read so unread counter stays clean
                    mark_messages_as_read(service, [mid])

                except Exception as e:
                    print(f"Error processing {mid}: {e}", file=sys.stderr)

            # Update seen_ids (keep last 300)
            updated_seen = (list(new_ids) + list(seen_ids))[:300]
            acc_state["seen_ids"] = updated_seen

    save_state(state)
    return total_new

def run_watcher(single_pass=False):
    print("=" * 60)
    print("      GAGAN AI REAL-TIME EMAIL & CALENDAR WATCHER DAEMON")
    print("=" * 60)
    print(f"Poll Interval: {POLL_INTERVAL_SECONDS} seconds")
    print(f"Mode: {'Single Pass (One-off check)' if single_pass else 'Continuous 24/7 Background'}")
    print("Monitoring all 6 Google accounts...")

    state = load_state()
    cal_service, cal_account = get_calendar_service()
    print(f"Syncing events to Primary Calendar: {cal_account}\n")

    if single_pass:
        count = watch_cycle(state, cal_service, cal_account)
        print(f"Single pass finished. New emails processed: {count}")
        return

    print("🟢 Watcher service is LIVE! Listening for inbound emails...\n")
    try:
        while True:
            try:
                watch_cycle(state, cal_service, cal_account)
            except Exception as e:
                print(f"[{datetime.now(IST).strftime('%H:%M:%S')}] Cycle warning: {e}", file=sys.stderr)
            time.sleep(POLL_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nWatcher stopped by user.")

if __name__ == '__main__':
    is_once = "--once" in sys.argv
    run_watcher(single_pass=is_once)

