import os
import sys

# Ensure UTF-8 and unbuffered output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', line_buffering=True)

import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIENT_SECRET_FILE = os.path.join(BASE_DIR, 'credentials', 'client_secret.json')
TOKENS_DIR = os.path.join(BASE_DIR, 'credentials', 'tokens')
ACCOUNTS_CONFIG_FILE = os.path.join(BASE_DIR, 'config', 'google_accounts.json')
DEFAULT_PRIMARY_CALENDAR = "gagansokhal077@gmail.com"

def load_accounts_config():
    if os.path.exists(ACCOUNTS_CONFIG_FILE):
        try:
            with open(ACCOUNTS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "primary_calendar_account": DEFAULT_PRIMARY_CALENDAR,
        "accounts": []
    }

def save_accounts_config(config):
    os.makedirs(os.path.dirname(ACCOUNTS_CONFIG_FILE), exist_ok=True)
    with open(ACCOUNTS_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2)

def get_token_path_for_email(email):
    os.makedirs(TOKENS_DIR, exist_ok=True)
    sanitized = email.strip().lower()
    return os.path.join(TOKENS_DIR, f"token_{sanitized}.json")

def get_credentials_for_email(email):
    token_path = get_token_path_for_email(email)
    if not os.path.exists(token_path):
        return None
    try:
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                with open(token_path, 'w', encoding='utf-8') as f:
                    f.write(creds.to_json())
            else:
                return None
        return creds
    except Exception:
        return None

def add_account():
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"ERROR: Client secret file not found at {CLIENT_SECRET_FILE}")
        sys.exit(1)

    print("\n=======================================================")
    print("  CONNECTING A GOOGLE ACCOUNT TO GAGAN AI")
    print("=======================================================")
    print("A browser window will open.")
    print("👉 Choose the Google account you wish to connect.")
    print("👉 If prompted with 'Unverified app', click Advanced -> Go to Gagan AI (unsafe).")
    print("👉 Grant permissions for Gmail and Google Calendar.")
    print("=======================================================\n")

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
    # prompt='select_account consent' forces Google to show the account picker
    creds = flow.run_local_server(
        port=0,
        prompt='select_account consent',
        access_type='offline',
        authorization_prompt_message="Please visit this URL to authorize Gagan AI:\n{url}\n",
        open_browser=True
    )

    # Detect the email of the authorized account
    gmail_service = build('gmail', 'v1', credentials=creds)
    profile = gmail_service.users().getProfile(userId='me').execute()
    email = profile.get('emailAddress')
    total_messages = profile.get('messagesTotal', 0)

    token_path = get_token_path_for_email(email)
    with open(token_path, 'w', encoding='utf-8') as f:
        f.write(creds.to_json())

    # Also keep the legacy credentials/gmail_token.json updated if this is primary or first
    legacy_token = os.path.join(BASE_DIR, 'credentials', 'gmail_token.json')
    with open(legacy_token, 'w', encoding='utf-8') as f:
        f.write(creds.to_json())

    # Update accounts config
    config = load_accounts_config()
    is_primary = (email.lower() == config.get("primary_calendar_account", "").lower())
    
    # Check if already in list
    existing = [acc for acc in config["accounts"] if acc["email"].lower() == email.lower()]
    if not existing:
        config["accounts"].append({
            "email": email,
            "token_file": os.path.relpath(token_path, BASE_DIR).replace('\\', '/'),
            "is_primary_calendar": is_primary,
            "enabled": True
        })
    save_accounts_config(config)

    print(f"\n🎉 SUCCESS: Connected account: {email}")
    print(f"   Total Messages: {total_messages}")
    if is_primary:
        print(f"   ⭐ Designated as PRIMARY CALENDAR account ({DEFAULT_PRIMARY_CALENDAR})")
    else:
        print(f"   📥 Connected for Gmail inbox monitoring")
    print(f"   Token saved to: {token_path}")
    return email

def list_accounts():
    config = load_accounts_config()
    accounts = config.get("accounts", [])
    primary_cal = config.get("primary_calendar_account", DEFAULT_PRIMARY_CALENDAR)

    print("\n=======================================================")
    print(f"  CONNECTED GOOGLE ACCOUNTS ({len(accounts)} connected)")
    print(f"  Primary Calendar Account: {primary_cal}")
    print("=======================================================")

    if not accounts:
        print("No accounts connected yet.")
        print("Run: python scripts/auth_google.py add")
        return

    for idx, acc in enumerate(accounts, 1):
        email = acc["email"]
        is_cal = (email.lower() == primary_cal.lower())
        cal_tag = " [⭐ PRIMARY CALENDAR]" if is_cal else ""
        creds = get_credentials_for_email(email)
        status = "✅ Active (Token valid)" if creds else "❌ Needs re-auth"
        print(f"{idx}. {email}{cal_tag}")
        print(f"   Status: {status}")
        print(f"   Token:  {acc.get('token_file')}")
    print()

def set_primary_calendar(email):
    config = load_accounts_config()
    config["primary_calendar_account"] = email.strip()
    for acc in config.get("accounts", []):
        acc["is_primary_calendar"] = (acc["email"].lower() == email.strip().lower())
    save_accounts_config(config)
    print(f"✅ Primary calendar account set to: {email.strip()}")

if __name__ == '__main__':
    args = sys.argv[1:]
    cmd = args[0] if args else "list"

    if cmd == "add":
        add_account()
    elif cmd == "list":
        list_accounts()
    elif cmd == "set-calendar":
        if len(args) < 2:
            print("Usage: python auth_google.py set-calendar <email>")
            sys.exit(1)
        set_primary_calendar(args[1])
    else:
        print(f"Unknown command: {cmd}")
        print("Available: add, list, set-calendar <email>")
