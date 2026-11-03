import os
import sys

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime
import zoneinfo

from morning_briefing import generate_morning_briefing
from gmail_manager import get_all_unread_emails, format_telegram_summary
from telegram_sender import send_telegram_message

IST = zoneinfo.ZoneInfo("Asia/Kolkata")

def run_routine(routine_name):
    now_ist = datetime.now(IST)
    print(f"[{now_ist.isoformat()}] Running routine: {routine_name}...")

    if routine_name == "morning-briefing":
        briefing = generate_morning_briefing()
        res = send_telegram_message(briefing)
        print(f"Morning briefing delivered! Msg ID: {res.get('message_id')}")

    elif routine_name == "email-digest":
        data = get_all_unread_emails(max_per_account=5)
        if data.get("total_unread", 0) > 0:
            msg = f"📬 *EMAIL DIGEST* ({now_ist.strftime('%I:%M %p IST')})\n\n" + format_telegram_summary(data)
            res = send_telegram_message(msg)
            print(f"Email digest delivered! Msg ID: {res.get('message_id')}")
        else:
            print("Inbox zero across all accounts. No digest needed.")

    elif routine_name == "deadline-check":
        data = get_all_unread_emails(max_per_account=5)
        urgent = []
        for acc_res in data.get("results", []):
            for em in acc_res.get("emails", []):
                if em.get("deadline") or em.get("urgency") == "HIGH":
                    urgent.append(em)

        if urgent:
            lines = [f"⏰ *URGENT DEADLINE ALERT* ({len(urgent)} items need attention)\n"]
            for u in urgent[:4]:
                dl = f" [Due: {u['deadline']}]" if u.get('deadline') else ""
                lines.append(f"• 🔴 *{u['sender'].split('<')[0].strip()}* — {u['subject']}{dl}")
                lines.append(f"    └ Account: `{u['account']}`\n")
            lines.append("Please review and take action when possible.")
            res = send_telegram_message("\n".join(lines))
            print(f"Deadline alert sent! Msg ID: {res.get('message_id')}")
        else:
            print("No high-urgency deadlines found.")

    else:
        print(f"Unknown routine: {routine_name}")
        print("Available: morning-briefing, email-digest, deadline-check")

if __name__ == '__main__':
    routine = sys.argv[1] if len(sys.argv) > 1 else "morning-briefing"
    run_routine(routine)
