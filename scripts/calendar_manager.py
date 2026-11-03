import os
import sys

# Ensure UTF-8 output encoding on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from datetime import datetime, timedelta
import zoneinfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNTS_CONFIG_FILE = os.path.join(BASE_DIR, 'config', 'google_accounts.json')
IST = zoneinfo.ZoneInfo("Asia/Kolkata")

def load_accounts_config():
    if os.path.exists(ACCOUNTS_CONFIG_FILE):
        try:
            with open(ACCOUNTS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"primary_calendar_account": "gagansokhal077@gmail.com", "accounts": []}

def get_calendar_service():
    config = load_accounts_config()
    primary_email = config.get("primary_calendar_account", "gagansokhal077@gmail.com").lower()
    accounts = config.get("accounts", [])

    target_acc = next((a for a in accounts if a.get("email", "").lower() == primary_email), None)

    # If primary email not yet connected, fall back to first connected account with a notice
    token_rel_path = None
    active_email = primary_email

    if target_acc:
        token_rel_path = target_acc.get("token_file")
        active_email = target_acc.get("email")
    elif accounts:
        token_rel_path = accounts[0].get("token_file")
        active_email = accounts[0].get("email")
        print(f"⚠️ Note: Primary calendar '{primary_email}' not connected yet. Using fallback '{active_email}'.", file=sys.stderr)
    else:
        raise FileNotFoundError(f"No Google account connected for Calendar. Connect {primary_email} via 'python scripts/auth_google.py add'.")

    token_file = os.path.join(BASE_DIR, token_rel_path)
    if not os.path.exists(token_file):
        raise FileNotFoundError(f"OAuth token not found at {token_file}")

    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_file, 'w', encoding='utf-8') as f:
                f.write(creds.to_json())
        else:
            raise RuntimeError(f"Credentials invalid for {active_email}. Please re-authenticate.")

    return build('calendar', 'v3', credentials=creds), active_email

def parse_event_time(event_time_dict):
    """Returns (formatted_str, datetime_obj or None)"""
    if 'dateTime' in event_time_dict:
        dt = datetime.fromisoformat(event_time_dict['dateTime'].replace('Z', '+00:00'))
        dt_ist = dt.astimezone(IST)
        return dt_ist.strftime("%I:%M %p"), dt_ist
    elif 'date' in event_time_dict:
        return f"All Day ({event_time_dict['date']})", None
    return "Unknown time", None

def get_today_events():
    now_ist = datetime.now(IST)
    start_of_day = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now_ist.replace(hour=23, minute=59, second=59, microsecond=999999)

    return get_events_range(start_of_day, end_of_day)

def get_upcoming_events(days=7):
    now_ist = datetime.now(IST)
    end_of_period = now_ist + timedelta(days=days)
    return get_events_range(now_ist, end_of_period)

def get_events_range(start_dt, end_dt):
    service, active_email = get_calendar_service()
    time_min = start_dt.isoformat()
    time_max = end_dt.isoformat()

    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    items = events_result.get('items', [])
    parsed_events = []

    for item in items:
        start_str, start_dt_obj = parse_event_time(item.get('start', {}))
        end_str, end_dt_obj = parse_event_time(item.get('end', {}))

        parsed_events.append({
            "id": item.get('id'),
            "account": active_email,
            "summary": item.get('summary', '(No Title)'),
            "description": item.get('description', ''),
            "location": item.get('location', ''),
            "start": start_str,
            "end": end_str,
            "htmlLink": item.get('htmlLink', '')
        })

    return parsed_events

def create_calendar_event(summary, start_time_str, duration_minutes=60, description="", location=""):
    service, active_email = get_calendar_service()
    now_ist = datetime.now(IST)

    cleaned = start_time_str.strip().lower()
    if cleaned.startswith('today'):
        time_part = cleaned.replace('today', '').strip()
        h, m = map(int, time_part.split(':'))
        start_dt = now_ist.replace(hour=h, minute=m, second=0, microsecond=0)
    elif cleaned.startswith('tomorrow'):
        time_part = cleaned.replace('tomorrow', '').strip()
        h, m = map(int, time_part.split(':'))
        start_dt = (now_ist + timedelta(days=1)).replace(hour=h, minute=m, second=0, microsecond=0)
    else:
        try:
            naive_dt = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
            start_dt = naive_dt.replace(tzinfo=IST)
        except Exception:
            start_dt = datetime.fromisoformat(start_time_str)
            if start_dt.tzinfo is None:
                start_dt = start_dt.replace(tzinfo=IST)

    end_dt = start_dt + timedelta(minutes=duration_minutes)

    event_body = {
        'summary': summary,
        'description': description,
        'location': location,
        'start': {
            'dateTime': start_dt.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': end_dt.isoformat(),
            'timeZone': 'Asia/Kolkata',
        },
    }

    created_event = service.events().insert(calendarId='primary', body=event_body).execute()
    return {
        "status": "created",
        "account": active_email,
        "id": created_event.get('id'),
        "summary": summary,
        "start": start_dt.strftime("%d %b %Y, %I:%M %p IST"),
        "end": end_dt.strftime("%d %b %Y, %I:%M %p IST"),
        "link": created_event.get('htmlLink')
    }

def format_telegram_calendar(events, title="📅 TODAY'S SCHEDULE"):
    config = load_accounts_config()
    primary_email = config.get("primary_calendar_account", "gagansokhal077@gmail.com")

    if not events:
        return f"{title} ({primary_email})\n• ✨ No events scheduled. You have a clear agenda!"

    lines = [f"*{title}* (`{primary_email}`) — {len(events)} event{'s' if len(events) > 1 else ''}\n"]
    for ev in events:
        loc = f" 📍 {ev['location']}" if ev['location'] else ""
        desc = f"\n    └ {ev['description'][:60]}..." if ev['description'] else ""
        lines.append(f"• ⏰ *{ev['start']}* — {ev['summary']}{loc}{desc}")

    return "\n".join(lines)

if __name__ == '__main__':
    args = sys.argv[1:]
    command = args[0] if args else "today"

    if command == "today":
        events = get_today_events()
        print(format_telegram_calendar(events, "📅 TODAY'S SCHEDULE (IST)"))

    elif command == "week":
        events = get_upcoming_events(days=7)
        print(format_telegram_calendar(events, "🗓️ UPCOMING 7 DAYS SCHEDULE (IST)"))

    elif command == "json":
        events = get_today_events()
        print(json.dumps(events, indent=2, ensure_ascii=False))

    elif command == "add":
        if len(args) < 3:
            print("Usage: python calendar_manager.py add <summary> <start_time> [duration_mins] [description]")
            print("Examples: python calendar_manager.py add 'OS Exam Prep' 'today 18:00' 120")
            sys.exit(1)
        summary = args[1]
        start_time = args[2]
        duration = int(args[3]) if len(args) > 3 else 60
        desc = args[4] if len(args) > 4 else ""
        res = create_calendar_event(summary, start_time, duration, desc)
        print(f"Event created in {res['account']}: '{res['summary']}' from {res['start']} to {res['end']}")

    else:
        print(f"Unknown command: {command}")
        print("Available: today, week, json, add")
