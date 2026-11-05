import os
import sys
import json
from datetime import datetime
import zoneinfo

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, 'scripts'))

from scripts.gmail_manager import (
    load_accounts_config,
    get_gmail_service_for_token,
    extract_body,
    categorize_email
)
from scripts.telegram_sender import send_telegram_message

IST = zoneinfo.ZoneInfo("Asia/Kolkata")

def get_latest_across_inboxes():
    config = load_accounts_config()
    accounts = [a for a in config.get("accounts", []) if a.get("enabled", True)]
    
    latest_msg = None
    latest_time = 0
    latest_account = None

    for acc in accounts:
        try:
            service = get_gmail_service_for_token(acc["token_file"])
            res = service.users().messages().list(userId='me', maxResults=3).execute()
            messages = res.get('messages', [])
            for m in messages:
                full = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
                internal_date = int(full.get('internalDate', 0))
                if internal_date > latest_time:
                    latest_time = internal_date
                    latest_msg = full
                    latest_account = acc["email"]
        except Exception as e:
            print(f"Error checking {acc.get('email')}: {e}")

    if not latest_msg:
        print("No emails found.")
        return None

    headers = {h['name'].lower(): h['value'] for h in latest_msg.get('payload', {}).get('headers', [])}
    sender = headers.get('from', 'Unknown')
    subject = headers.get('subject', '(No Subject)')
    snippet = latest_msg.get('snippet', '')
    body = extract_body(latest_msg.get('payload', {}))
    clean_sender = sender.split('<')[0].strip(' "\'')
    clean_body = body.strip() if body else snippet.strip()
    
    received_dt = datetime.fromtimestamp(latest_time / 1000.0, tz=IST)
    received_str = received_dt.strftime("%A, %d %B %Y (%I:%M %p IST)")

    data_dir = os.path.join(BASE_DIR, 'data')
    os.makedirs(data_dir, exist_ok=True)

    record = {
        "account": latest_account,
        "sender": clean_sender,
        "subject": subject,
        "received_at": received_str,
        "body": clean_body
    }

    with open(os.path.join(data_dir, 'latest_email.json'), 'w', encoding='utf-8') as f:
        json.dump(record, f, indent=2, ensure_ascii=False)

    with open(os.path.join(data_dir, 'latest_email.txt'), 'w', encoding='utf-8') as f:
        f.write(f"Account: {latest_account}\nFrom: {clean_sender}\nSubject: {subject}\nDate: {received_str}\n\n{clean_body}")

    ws_dir = os.path.join(data_dir, 'workspace')
    os.makedirs(ws_dir, exist_ok=True)
    with open(os.path.join(ws_dir, 'LATEST_EMAIL.md'), 'w', encoding='utf-8') as f:
        f.write(f"# Latest Email\n- **Account:** `{latest_account}`\n- **From:** {clean_sender}\n- **Subject:** {subject}\n- **Date:** {received_str}\n\n## Content:\n```\n{clean_body}\n```\n")

    return record

def send_complete_mail_to_telegram(record):
    if not record:
        send_telegram_message("📬 No recent emails found in connected Google inboxes.")
        return

    content_preview = record["body"]
    if len(content_preview) > 2800:
        content_preview = content_preview[:2800] + "\n\n...[Full email archived in Gagan AI storage]"

    msg = (
        f"📬 *COMPLETE EMAIL DETAILS*\n\n"
        f"• *Inbox:* `{record['account']}`\n"
        f"• *From:* {record['sender']}\n"
        f"• *Subject:* _{record['subject']}_\n"
        f"• *Date:* {record['received_at']}\n\n"
        f"📄 *Complete Message Content:*\n{content_preview}"
    )
    res = send_telegram_message(msg)
    print("Telegram delivery result:", res)

if __name__ == '__main__':
    rec = get_latest_across_inboxes()
    if rec:
        print(f"Fetched latest: [{rec['account']}] {rec['subject']}")
        send_complete_mail_to_telegram(rec)
