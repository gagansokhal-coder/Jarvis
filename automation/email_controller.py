"""
Account-Specific Email Controller for Gagan AI.
Supports all 6 Google accounts (NITJ College, Main, Developer, Coder, Personal, Gagan Rajput).
Phase 2 & Phase 4 Integration.
"""
import os
import sys
import json
from datetime import datetime

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

ACCOUNT_ALIASES = {
    "gagandeep.cs.25@nitj.ac.in": [
        "nitj", "college", "academic", "university", "department", "campus",
        "student", "nit jalandhar", "cse", "classes"
    ],
    "gaganrajput1008@gmail.com": [
        "gagan rajput", "gaganrajput", "secondary", "gaganrajput1008"
    ],
    "gagansokhal077@gmail.com": [
        "main", "primary", "sokhal", "calendar", "default", "gagansokhal"
    ],
    "rajputdeveloper44@gmail.com": [
        "developer", "dev", "cloud", "github", "rajputdeveloper"
    ],
    "gagancoder22@gmail.com": [
        "coder", "coding", "learning", "gagancoder"
    ],
    "jaibabagi108@gmail.com": [
        "personal", "baba", "jaibabagi", "jaibabagi108"
    ]
}

def resolve_account_by_query(query: str) -> list[str]:
    """Resolve user query string to one or more matched email addresses."""
    q = query.lower().strip()
    
    if any(k in q for k in ["all", "every", "all accounts", "all emails", "all inboxes", "inboxes"]):
        return list(ACCOUNT_ALIASES.keys())

    matched = []
    for email, aliases in ACCOUNT_ALIASES.items():
        if email in q:
            return [email]
        if any(alias in q for alias in aliases):
            matched.append(email)

    return matched if matched else ["gagansokhal077@gmail.com"]

def get_latest_emails(account_query: str = "all", max_per_account: int = 3, send_telegram: bool = False) -> tuple[str, str, list]:
    """
    Fetch latest emails for the specified account(s).
    Returns: (spoken_summary, display_text, raw_list)
    """
    config = load_accounts_config()
    all_accs = {a["email"]: a for a in config.get("accounts", []) if a.get("enabled", True)}
    
    target_emails = resolve_account_by_query(account_query)
    results = []

    for email_addr in target_emails:
        acc_info = all_accs.get(email_addr)
        if not acc_info:
            continue
        try:
            service = get_gmail_service_for_token(acc_info["token_file"])
            res = service.users().messages().list(userId='me', maxResults=max_per_account).execute()
            messages = res.get('messages', [])
            
            for m in messages:
                full = service.users().messages().get(userId='me', id=m['id'], format='full').execute()
                headers = {h['name'].lower(): h['value'] for h in full.get('payload', {}).get('headers', [])}
                sender = headers.get('from', 'Unknown')
                subject = headers.get('subject', '(No Subject)')
                snippet = full.get('snippet', '')
                date_str = headers.get('date', '')
                clean_sender = sender.split('<')[0].strip(' "\'')
                body = extract_body(full.get('payload', {}))
                
                results.append({
                    "account": email_addr,
                    "sender": clean_sender,
                    "subject": subject,
                    "date": date_str,
                    "snippet": snippet,
                    "body": body.strip() if body else snippet
                })
        except Exception as e:
            print(f"Error fetching from {email_addr}: {e}", file=sys.stderr)

    if not results:
        msg = f"No recent emails found for {account_query}."
        return msg, msg, []

    # Save the absolute latest email to data/latest_email.txt & workspace
    top_email = results[0]
    data_dir = os.path.join(BASE_DIR, 'data')
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, 'latest_email.txt'), 'w', encoding='utf-8') as f:
        f.write(f"Account: {top_email['account']}\nFrom: {top_email['sender']}\nSubject: {top_email['subject']}\nDate: {top_email['date']}\n\n{top_email['body']}")
    
    ws_dir = os.path.join(data_dir, 'workspace')
    os.makedirs(ws_dir, exist_ok=True)
    with open(os.path.join(ws_dir, 'LATEST_EMAIL.md'), 'w', encoding='utf-8') as f:
        f.write(f"# Latest Email ({top_email['account']})\n- **From:** {top_email['sender']}\n- **Subject:** {top_email['subject']}\n\n```\n{top_email['body'][:2000]}\n```\n")

    # Build spoken summary
    spoken_parts = []
    if len(target_emails) == 1:
        spoken_parts.append(f"Here are the latest emails from your {target_emails[0].split('@')[0]} account:")
    else:
        spoken_parts.append(f"Here are your latest emails across inboxes:")

    for i, e in enumerate(results[:3]):
        spoken_parts.append(f"Number {i+1}, from {e['sender']}, subject: {e['subject']}.")

    spoken_summary = " ".join(spoken_parts)

    # Build display text
    display_lines = [f"📬 **EMAIL REPORT ({len(results)} found)**\n"]
    for i, e in enumerate(results):
        display_lines.append(f"**{i+1}. [{e['account']}]**")
        display_lines.append(f"• **From:** {e['sender']}")
        display_lines.append(f"• **Subject:** _{e['subject']}_")
        display_lines.append(f"• **Snippet:** {e['snippet'][:120]}...\n")

    display_text = "\n".join(display_lines)

    # Optional Telegram dispatch
    if send_telegram:
        try:
            send_telegram_message(display_text)
        except Exception as e:
            print(f"Telegram dispatch error: {e}", file=sys.stderr)

    return spoken_summary, display_text, results

if __name__ == '__main__':
    query = sys.argv[1] if len(sys.argv) > 1 else "college"
    print(f"Fetching emails for query: '{query}'...")
    spoken, display, _ = get_latest_emails(query, max_per_account=2)
    print("\n[SPOKEN]:", spoken)
    print("\n[DISPLAY]:\n", display)
