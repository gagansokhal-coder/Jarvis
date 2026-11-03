import os
import sys

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import json
import re
from datetime import datetime, timedelta
import zoneinfo

from gmail_manager import load_accounts_config, get_gmail_service_for_token, extract_body
from calendar_manager import get_calendar_service
from telegram_sender import send_telegram_message

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNC_LEDGER_FILE = os.path.join(BASE_DIR, 'data', 'synced_calendar_events.json')
IST = zoneinfo.ZoneInfo("Asia/Kolkata")

MONTH_MAP = {
    'jan': 1, 'january': 1,
    'feb': 2, 'february': 2,
    'mar': 3, 'march': 3,
    'apr': 4, 'april': 4,
    'may': 5,
    'jun': 6, 'june': 6,
    'jul': 7, 'july': 7,
    'aug': 8, 'august': 8,
    'sep': 9, 'september': 9,
    'oct': 10, 'october': 10,
    'nov': 11, 'november': 11,
    'dec': 12, 'december': 12
}

def load_sync_ledger():
    if os.path.exists(SYNC_LEDGER_FILE):
        try:
            with open(SYNC_LEDGER_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {"synced_messages": {}, "synced_events": []}

def save_sync_ledger(ledger):
    os.makedirs(os.path.dirname(SYNC_LEDGER_FILE), exist_ok=True)
    with open(SYNC_LEDGER_FILE, 'w', encoding='utf-8') as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)

def parse_time_component(time_str):
    """Parses '02:30 PM' or '2:30pm' into (hour, minute) in 24h format"""
    m = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', time_str, re.IGNORECASE)
    if not m:
        m2 = re.search(r'(\d{1,2})\s*(am|pm)', time_str, re.IGNORECASE)
        if m2:
            h = int(m2.group(1))
            mer = m2.group(2).lower()
            if mer == 'pm' and h != 12:
                h += 12
            elif mer == 'am' and h == 12:
                h = 0
            return h, 0
        return 9, 0

    h = int(m.group(1))
    minute = int(m.group(2))
    mer = m.group(3).lower() if m.group(3) else None

    if mer == 'pm' and h != 12:
        h += 12
    elif mer == 'am' and h == 12:
        h = 0
    return h, minute

def parse_date_and_time(text, email_date_str=None):
    """
    Extracts date, start_time, end_time, and venue from email text.
    Returns (start_dt, end_dt, venue, detection_confidence)
    """
    now = datetime.now(IST)
    curr_year = now.year

    start_dt = None
    end_dt = None
    venue = ""

    # 1. Check for NITJ Structured Format: Date: ... Time: ... Venue: ...
    date_match = re.search(r'(?:Date|Day & Date|Date of event)\s*[:\-]\s*([^\n\r]+)', text, re.IGNORECASE)
    time_match = re.search(r'(?:Time|Timings?|Duration)\s*[:\-]\s*([^\n\r]+)', text, re.IGNORECASE)
    venue_match = re.search(r'(?:Venue|Location|Place|Room)\s*[:\-]\s*([^\n\r]+)', text, re.IGNORECASE)

    if venue_match:
        venue = venue_match.group(1).strip().strip('*_`')

    # If Date line exists
    target_date = None
    if date_match:
        date_line = date_match.group(1).strip()
        # Look for "04 November 2026" or "Nov 4, 2026" or "04/11/2026"
        dm = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', date_line)
        if dm:
            day = int(dm.group(1))
            mon = MONTH_MAP.get(dm.group(2).lower())
            year = int(dm.group(3))
            if mon:
                target_date = (year, mon, day)
        else:
            dm2 = re.search(r'([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s*(\d{4})?', date_line)
            if dm2:
                mon = MONTH_MAP.get(dm2.group(1).lower())
                day = int(dm2.group(2))
                year = int(dm2.group(3)) if dm2.group(3) else curr_year
                if mon:
                    target_date = (year, mon, day)
            else:
                dm3 = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})', date_line)
                if dm3:
                    d, m, y = int(dm3.group(1)), int(dm3.group(2)), int(dm3.group(3))
                    if y < 100: y += 2000
                    target_date = (y, m, d)

    # If no target_date from Date: line, scan whole text for future date patterns
    if not target_date:
        full_dm = re.search(r'(?:tomorrow|on\s+([A-Za-z]+ \d{1,2}(?:st|nd|rd|th)?,?\s*\d{4}?)|(?:held on|scheduled on|date:?)\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4}))', text, re.IGNORECASE)
        if full_dm:
            match_str = full_dm.group(0).lower()
            if 'tomorrow' in match_str:
                tmr = now + timedelta(days=1)
                target_date = (tmr.year, tmr.month, tmr.day)
            elif full_dm.group(1):
                p = full_dm.group(1)
                sub_m = re.search(r'([A-Za-z]+)\s+(\d{1,2})', p)
                if sub_m:
                    mon = MONTH_MAP.get(sub_m.group(1).lower())
                    day = int(sub_m.group(2))
                    if mon:
                        target_date = (curr_year, mon, day)
            elif full_dm.group(2):
                p = full_dm.group(2)
                sub_m2 = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', p)
                if sub_m2:
                    day = int(sub_m2.group(1))
                    mon = MONTH_MAP.get(sub_m2.group(2).lower())
                    year = int(sub_m2.group(3))
                    if mon:
                        target_date = (year, mon, day)

    if not target_date:
        return None, None, venue

    # Parse time
    start_hour, start_min = 9, 0
    end_hour, end_min = 10, 0

    if time_match:
        time_line = time_match.group(1).strip()
        # Look for range: 02:30 PM – 05:00 PM or 2:30 PM to 5:00 PM
        tm_range = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)\s*(?:–|-|to)\s*(\d{1,2}(?::\d{2})?\s*(?:am|pm))', time_line, re.IGNORECASE)
        if tm_range:
            start_hour, start_min = parse_time_component(tm_range.group(1))
            end_hour, end_min = parse_time_component(tm_range.group(2))
        else:
            start_hour, start_min = parse_time_component(time_line)
            end_hour, end_min = (start_hour + 1) % 24, start_min
    else:
        # Check text for standalone time like 'at 2:30 pm' or 'at 11 am'
        standalone_tm = re.search(r'(?:at|by)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))', text, re.IGNORECASE)
        if standalone_tm:
            start_hour, start_min = parse_time_component(standalone_tm.group(1))
            end_hour = (start_hour + 1) % 24

    try:
        y, m, d = target_date
        start_dt = datetime(y, m, d, start_hour, start_min, 0, tzinfo=IST)
        end_dt = datetime(y, m, d, end_hour, end_min, 0, tzinfo=IST)
        if end_dt <= start_dt:
            end_dt = start_dt + timedelta(hours=1)
        return start_dt, end_dt, venue
    except Exception:
        return None, None, venue

def is_event_already_on_calendar(service, summary, start_dt, end_dt):
    """Checks Google Calendar directly around target window to prevent duplicates."""
    window_start = (start_dt - timedelta(days=1)).isoformat()
    window_end = (end_dt + timedelta(days=1)).isoformat()

    try:
        events = service.events().list(
            calendarId='primary',
            timeMin=window_start,
            timeMax=window_end,
            singleEvents=True
        ).execute().get('items', [])

        clean_sum = summary.lower()
        # Extract core keywords from summary
        keywords = [w for w in re.findall(r'[a-z0-9]+', clean_sum) if len(w) > 3 and w not in ['nitj', 'mandatory', 'session', 'event', 'attendance', 'interview', 'scheduled', 'reminder']]

        for ev in events:
            ev_sum = ev.get('summary', '').lower()
            # If direct substring or matches 2+ keywords
            if summary.lower() in ev_sum or ev_sum in summary.lower():
                return True
            matched_kws = [k for k in keywords if k in ev_sum]
            if len(matched_kws) >= 2:
                return True
    except Exception as e:
        print(f"Calendar check warning: {e}", file=sys.stderr)
    return False

def sync_events_from_emails():
    config = load_accounts_config()
    accounts = [a for a in config.get("accounts", []) if a.get("enabled", True)]
    cal_service, cal_account = get_calendar_service()
    ledger = load_sync_ledger()

    synced_messages = ledger.get("synced_messages", {})
    newly_added = []

    print(f"Scanning emails across {len(accounts)} accounts for auto-calendar events...")
    print(f"Target Primary Calendar: {cal_account}")

    for acc in accounts:
        email_addr = acc["email"]
        is_nitj = "nitj" in email_addr.lower()

        try:
            gmail_service = get_gmail_service_for_token(acc["token_file"])
            # Fetch unread or recent messages
            res = gmail_service.users().messages().list(userId='me', maxResults=15).execute()
            messages = res.get('messages', [])
        except Exception as e:
            print(f"Error checking {email_addr}: {e}", file=sys.stderr)
            continue

        for m_meta in messages:
            msg_id = m_meta['id']
            if msg_id in synced_messages:
                continue

            try:
                full_msg = gmail_service.users().messages().get(userId='me', id=msg_id, format='full').execute()
            except Exception:
                continue

            headers = {h['name'].lower(): h['value'] for h in full_msg.get('payload', {}).get('headers', [])}
            subject = headers.get('subject', '')
            sender = headers.get('from', '')
            date_hdr = headers.get('date', '')
            body = extract_body(full_msg.get('payload', {}))
            snippet = full_msg.get('snippet', '')

            full_content = f"{subject}\n{body}\n{snippet}"

            # Event detection keywords
            event_triggers = [
                'session', 'interview', 'webinar', 'examination', 'exam of course', 'quiz',
                'compulsory attendance', 'mandatory attendance', 'placement', 'hiring test',
                'online assessment', 'due date', 'submission deadline', 'venue:', 'date:'
            ]

            # Exclusion filters for non-calendar notices
            ignore_keywords = [
                'lost my', 'lost debit', 'lost card', 'lost charger', 'lost watch', 'lost phone',
                'found debit', 'found card', 'found watch', 'found phone', 'found keys', 'lost & found',
                'lost and found', 'blood requirement', 'blood donor'
            ]
            if any(ik in full_content.lower() for ik in ignore_keywords) or any(ik in subject.lower() for ik in ignore_keywords):
                synced_messages[msg_id] = {"status": "ignored_lost_found_circular"}
                continue

            if not any(t in full_content.lower() for t in event_triggers):
                continue

            # Extract date, time, venue
            start_dt, end_dt, venue = parse_date_and_time(full_content, date_hdr)

            if not start_dt:
                continue

            # Skip past events
            now = datetime.now(IST)
            if start_dt < (now - timedelta(hours=12)):
                synced_messages[msg_id] = {"status": "skipped_past_event", "date": start_dt.isoformat()}
                continue

            # Determine clean title
            clean_sender = sender.split('<')[0].strip(' "\'')
            tag = "[NITJ]" if is_nitj else ("[Career]" if any(x in full_content.lower() for x in ['interview', 'assessment', 'internship', 'tcs', 'google']) else "[Event]")
            
            clean_subject = subject.replace('Fwd:', '').replace('Reminder |', '').replace('Re:', '').strip()
            event_title = f"{tag} {clean_subject}"

            # Deduplication: Check if already on Google Calendar
            if is_event_already_on_calendar(cal_service, clean_subject, start_dt, end_dt):
                synced_messages[msg_id] = {
                    "status": "already_present_on_calendar",
                    "title": event_title,
                    "start": start_dt.isoformat()
                }
                print(f"ℹ️ Already on calendar: '{event_title}' ({start_dt.strftime('%d %b %Y')})")
                continue

            # Create event on Google Calendar
            description = (
                f"Auto-synced by JARVIS AI\n"
                f"Source Account: {email_addr}\n"
                f"Sender: {clean_sender}\n"
                f"Original Subject: {subject}\n\n"
                f"--- Email Snippet ---\n{snippet}"
            )

            event_body = {
                'summary': event_title,
                'description': description,
                'location': venue or ("NIT Jalandhar Campus" if is_nitj else ""),
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'Asia/Kolkata',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': 60},
                        {'method': 'popup', 'minutes': 1440}, # 1 day before
                    ],
                },
            }

            try:
                created = cal_service.events().insert(calendarId='primary', body=event_body).execute()
                event_id = created.get('id')
                html_link = created.get('htmlLink')

                event_record = {
                    "msg_id": msg_id,
                    "calendar_event_id": event_id,
                    "title": event_title,
                    "start": start_dt.strftime("%A, %d %b %Y (%I:%M %p IST)"),
                    "end": end_dt.strftime("%I:%M %p IST"),
                    "venue": venue or "Campus",
                    "source_account": email_addr,
                    "sender": clean_sender,
                    "calendar_account": cal_account,
                    "created_at": datetime.now(IST).isoformat(),
                    "link": html_link
                }

                synced_messages[msg_id] = event_record
                ledger.setdefault("synced_events", []).append(event_record)
                newly_added.append(event_record)

                print(f"✅ AUTO-ADDED TO CALENDAR: '{event_title}' on {event_record['start']}")

            except Exception as e:
                print(f"Error creating calendar event for msg {msg_id}: {e}", file=sys.stderr)

    save_sync_ledger(ledger)

    # Send Telegram notification if new events were added
    if newly_added:
        lines = [f"📅 *JARVIS AUTO-CALENDAR SYNC* ({len(newly_added)} new event{'s' if len(newly_added) > 1 else ''} added)\n"]
        for item in newly_added:
            venue_txt = f" (📍 {item['venue']})" if item['venue'] else ""
            lines.append(f"• *{item['title']}*")
            lines.append(f"  ⏰ {item['start']} – {item['end']}{venue_txt}")
            lines.append(f"  👤 Source: `{item['source_account']}` ({item['sender']})")
            lines.append(f"  📅 Added to: `{item['calendar_account']}`\n")
        
        lines.append("Events automatically synced with 1-hour and 1-day reminders! 🚀")
        try:
            res = send_telegram_message("\n".join(lines))
            print(f"Telegram notification sent! Message ID: {res.get('message_id')}")
        except Exception as e:
            print(f"Failed to send Telegram notification: {e}", file=sys.stderr)

    return newly_added

if __name__ == '__main__':
    added = sync_events_from_emails()
    print(f"\nSync complete. Total new events added: {len(added)}")
