import os
import sys

# Ensure UTF-8 output encoding on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import base64
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
import zoneinfo

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from email.mime.text import MIMEText

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCOUNTS_CONFIG_FILE = os.path.join(BASE_DIR, 'config', 'google_accounts.json')
AUDIT_LOG_PATH = os.path.join(BASE_DIR, 'data', 'email_audit_log.json')
IST = zoneinfo.ZoneInfo("Asia/Kolkata")

def load_accounts_config():
    if os.path.exists(ACCOUNTS_CONFIG_FILE):
        try:
            with open(ACCOUNTS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    # Fallback to single legacy token if exists
    legacy = os.path.join(BASE_DIR, 'credentials', 'gmail_token.json')
    if os.path.exists(legacy):
        return {
            "primary_calendar_account": "gagansokhal077@gmail.com",
            "accounts": [{
                "email": "primary@gmail.com",
                "token_file": "credentials/gmail_token.json",
                "enabled": True
            }]
        }
    return {"primary_calendar_account": "gagansokhal077@gmail.com", "accounts": []}

def get_gmail_service_for_token(token_rel_path):
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
            raise RuntimeError(f"Credentials invalid for {token_rel_path}")

    return build('gmail', 'v1', credentials=creds)

def extract_body(payload):
    body_text = ""
    if 'parts' in payload:
        for part in payload['parts']:
            mime_type = part.get('mimeType', '')
            if mime_type == 'text/plain' and 'data' in part.get('body', {}):
                data = part['body']['data']
                try:
                    body_text += base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='replace') + "\n"
                except Exception:
                    pass
            elif 'parts' in part:
                body_text += extract_body(part)
    elif 'body' in payload and 'data' in payload['body']:
        data = payload['body']['data']
        try:
            body_text += base64.urlsafe_b64decode(data.encode('ASCII')).decode('utf-8', errors='replace')
        except Exception:
            pass
    return body_text.strip()

def categorize_email(sender, subject, snippet, body):
    combined_text = f"{sender} {subject} {snippet} {body}".lower()
    sender_lower = sender.lower()

    # Category matching
    category = "👤 Personal"
    college_keywords = ['.ac.in', '.edu', 'college', 'university', 'professor', 'faculty', 'exam', 'assignment', 'syllabus', 'hod', 'dean', 'campus', 'scholarship', 'admit card', 'semester']
    prof_keywords = ['linkedin', 'github', 'internship', 'interview', 'hr', 'recruiter', 'job', 'offer letter', 'hackathon', 'careers', 'hiring', 'work', 'application']
    newsletter_keywords = ['newsletter', 'unsubscribe', 'digest', 'no-reply', 'noreply', 'promotions', 'marketing', 'coupon', 'sale', 'updates@', 'mailer-daemon']

    if any(k in sender_lower or k in combined_text for k in college_keywords):
        category = "🎓 College"
    elif any(k in sender_lower or k in combined_text for k in prof_keywords):
        category = "💼 Professional"
    elif any(k in sender_lower or k in combined_text for k in newsletter_keywords):
        category = "📧 Newsletter/Promo"

    # Urgency detection
    urgency = "LOW"
    high_urgency_keywords = ['urgent', 'immediately', 'immediate', 'asap', 'action required', 'final notice', 'deadline today', 'tomorrow', 'critical', 'warning', 'expires']
    med_urgency_keywords = ['reminder', 'upcoming', 'due date', 'schedule', 'important', 'please review', 'follow up']

    if any(k in combined_text for k in high_urgency_keywords):
        urgency = "HIGH"
    elif any(k in combined_text for k in med_urgency_keywords):
        urgency = "MEDIUM"

    # Deadline extraction
    deadline = None
    deadline_patterns = [
        r'(?:due(?: date)?|deadline|by|before)\s*[:\-]?\s*([A-Za-z]+ \d{1,2}(?:st|nd|rd|th)?(?:, \d{4})?)',
        r'(?:due(?: date)?|deadline|by|before)\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)',
        r'(?:by|due)\s+(tomorrow|today|tonight|this friday|this monday|next week)',
        r'(\d{1,2}:\d{2}\s*(?:am|pm|ist))'
    ]
    for pattern in deadline_patterns:
        match = re.search(pattern, combined_text, re.IGNORECASE)
        if match:
            deadline = match.group(0).strip()
            break

    # Requires reply detection
    requires_reply = False
    reply_signals = ['please reply', 'let me know', 'confirm by', 'rsvp', 'acknowledge', 'waiting for your response', 'send me', 'revert back', 'kindly provide', 'feedback on']
    if any(s in combined_text for s in reply_signals):
        requires_reply = True

    return {
        "category": category,
        "urgency": urgency,
        "deadline": deadline,
        "requires_reply": requires_reply
    }

def get_unread_emails_for_account(acc, max_results=5, query="is:unread"):
    email_acc = acc["email"]
    token_file = acc["token_file"]

    try:
        service = get_gmail_service_for_token(token_file)
        results = service.users().messages().list(userId='me', q=query, maxResults=max_results).execute()
        messages = results.get('messages', [])
    except Exception as e:
        return {"account": email_acc, "error": str(e), "emails": []}

    emails = []
    for msg_meta in messages:
        msg_id = msg_meta['id']
        try:
            msg = service.users().messages().get(userId='me', id=msg_id, format='full').execute()
        except Exception:
            continue

        headers = {h['name'].lower(): h['value'] for h in msg.get('payload', {}).get('headers', [])}
        sender = headers.get('from', 'Unknown Sender')
        subject = headers.get('subject', '(No Subject)')
        date_raw = headers.get('date', '')

        try:
            dt = parsedate_to_datetime(date_raw)
            date_ist = dt.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST")
        except Exception:
            date_ist = date_raw

        snippet = msg.get('snippet', '')
        body = extract_body(msg.get('payload', {}))
        cat_info = categorize_email(sender, subject, snippet, body)

        emails.append({
            "account": email_acc,
            "id": msg_id,
            "threadId": msg.get('threadId', msg_id),
            "sender": sender,
            "subject": subject,
            "date": date_ist,
            "snippet": snippet,
            "body": body[:500] if body else snippet,
            "category": cat_info["category"],
            "urgency": cat_info["urgency"],
            "deadline": cat_info["deadline"],
            "requires_reply": cat_info["requires_reply"]
        })

    return {"account": email_acc, "error": None, "emails": emails}

def get_all_unread_emails(max_per_account=5):
    config = load_accounts_config()
    accounts = [a for a in config.get("accounts", []) if a.get("enabled", True)]
    
    all_results = []
    total_unread = 0

    for acc in accounts:
        res = get_unread_emails_for_account(acc, max_results=max_per_account)
        all_results.append(res)
        total_unread += len(res.get("emails", []))

    return {
        "accounts_count": len(accounts),
        "total_unread": total_unread,
        "results": all_results
    }

def format_telegram_summary(data):
    total = data.get("total_unread", 0)
    acc_count = data.get("accounts_count", 0)

    if total == 0:
        return f"✨ No unread emails across your {acc_count} connected accounts! Inboxes are clean."

    lines = [f"📬 *UNREAD EMAILS REPORT* ({total} unread across {acc_count} accounts)\n"]

    for acc_res in data.get("results", []):
        acc_email = acc_res["account"]
        emails = acc_res.get("emails", [])
        err = acc_res.get("error")

        if err:
            lines.append(f"📧 *{acc_email}*: ⚠️ _Error: {err}_")
            continue

        if not emails:
            continue

        lines.append(f"📧 *{acc_email}* ({len(emails)} unread):")
        for item in emails:
            urgency_icon = "🔴" if item['urgency'] == 'HIGH' else ("🟡" if item['urgency'] == 'MEDIUM' else "⚪")
            reply_badge = " [💬 Reply Needed]" if item['requires_reply'] else ""
            deadline_badge = f" [⏰ {item['deadline']}]" if item['deadline'] else ""
            cat_badge = f"_{item['category']}_"

            sender_clean = item['sender'].split('<')[0].strip(' "\'')
            lines.append(f" {urgency_icon} {cat_badge} *{sender_clean}* — {item['subject']}{reply_badge}{deadline_badge}")
            lines.append(f"    └ Preview: {item['snippet'][:85]}...")
            lines.append(f"    └ ID: `{item['id']}`\n")

    return "\n".join(lines)

def create_draft_reply(account_email, message_id, reply_text):
    config = load_accounts_config()
    target_acc = next((a for a in config.get("accounts", []) if a["email"].lower() == account_email.lower()), None)
    if not target_acc:
        raise ValueError(f"Account {account_email} not found in connected accounts.")

    service = get_gmail_service_for_token(target_acc["token_file"])
    original = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    headers = {h['name'].lower(): h['value'] for h in original.get('payload', {}).get('headers', [])}

    subject = headers.get('subject', '')
    if not subject.lower().startswith('re:'):
        subject = f"Re: {subject}"

    reply_to = headers.get('reply-to', headers.get('from', ''))
    thread_id = original.get('threadId', message_id)
    msg_id_header = headers.get('message-id', '')

    mime_msg = MIMEText(reply_text)
    mime_msg['to'] = reply_to
    mime_msg['subject'] = subject
    if msg_id_header:
        mime_msg['In-Reply-To'] = msg_id_header
        mime_msg['References'] = msg_id_header

    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode('ASCII')
    draft_body = {
        'message': {
            'threadId': thread_id,
            'raw': raw
        }
    }

    draft = service.users().drafts().create(userId='me', body=draft_body).execute()
    return {
        "status": "success",
        "account": account_email,
        "draftId": draft.get('id'),
        "threadId": thread_id,
        "to": reply_to,
        "subject": subject
    }

def send_email_reply(account_email, message_id, reply_text):
    config = load_accounts_config()
    target_acc = next((a for a in config.get("accounts", []) if a["email"].lower() == account_email.lower()), None)
    if not target_acc:
        raise ValueError(f"Account {account_email} not found in connected accounts.")

    service = get_gmail_service_for_token(target_acc["token_file"])
    original = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    headers = {h['name'].lower(): h['value'] for h in original.get('payload', {}).get('headers', [])}

    subject = headers.get('subject', '')
    if not subject.lower().startswith('re:'):
        subject = f"Re: {subject}"

    reply_to = headers.get('reply-to', headers.get('from', ''))
    thread_id = original.get('threadId', message_id)
    msg_id_header = headers.get('message-id', '')

    mime_msg = MIMEText(reply_text)
    mime_msg['to'] = reply_to
    mime_msg['subject'] = subject
    if msg_id_header:
        mime_msg['In-Reply-To'] = msg_id_header
        mime_msg['References'] = msg_id_header

    raw = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode('ASCII')
    sent = service.users().messages().send(userId='me', body={'threadId': thread_id, 'raw': raw}).execute()

    # Log to audit trail
    os.makedirs(os.path.dirname(os.path.abspath(AUDIT_LOG_PATH)), exist_ok=True)
    records = []
    if os.path.exists(AUDIT_LOG_PATH):
        try:
            with open(AUDIT_LOG_PATH, 'r', encoding='utf-8') as f:
                records = json.load(f)
        except Exception:
            records = []
    records.append({
        "action": "SEND_EMAIL",
        "account": account_email,
        "messageId": sent.get('id'),
        "threadId": thread_id,
        "to": reply_to,
        "subject": subject,
        "timestamp": datetime.now(IST).isoformat(),
        "text": reply_text
    })
    with open(AUDIT_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(records, f, indent=2)

    return {
        "status": "sent",
        "account": account_email,
        "messageId": sent.get('id'),
        "to": reply_to,
        "subject": subject
    }

if __name__ == '__main__':
    args = sys.argv[1:]
    command = args[0] if args else "list"

    if command == "list":
        limit = int(args[1]) if len(args) > 1 else 5
        data = get_all_unread_emails(max_per_account=limit)
        print(format_telegram_summary(data))

    elif command == "json":
        limit = int(args[1]) if len(args) > 1 else 5
        data = get_all_unread_emails(max_per_account=limit)
        print(json.dumps(data, indent=2, ensure_ascii=False))

    elif command == "draft":
        if len(args) < 4:
            print("Usage: python gmail_manager.py draft <account_email> <message_id> <reply_text>")
            sys.exit(1)
        res = create_draft_reply(args[1], args[2], args[3])
        print(f"Draft created on {res['account']}: {res['draftId']}")

    elif command == "send":
        if len(args) < 4:
            print("Usage: python gmail_manager.py send <account_email> <message_id> <reply_text>")
            sys.exit(1)
        res = send_email_reply(args[1], args[2], args[3])
        print(f"Email sent from {res['account']}: {res['messageId']} to {res['to']}")

    else:
        print(f"Unknown command: {command}")
        print("Available: list, json, draft, send")
