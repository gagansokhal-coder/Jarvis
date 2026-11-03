import os
import sys

# Ensure UTF-8 output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime
import zoneinfo

from gmail_manager import get_all_unread_emails
from calendar_manager import get_today_events, get_upcoming_events, load_accounts_config
from telegram_sender import send_telegram_message

IST = zoneinfo.ZoneInfo("Asia/Kolkata")

def generate_morning_briefing():
    now_ist = datetime.now(IST)
    date_str = now_ist.strftime("%A, %b %d, %Y")
    time_str = now_ist.strftime("%I:%M %p IST")

    config = load_accounts_config()
    primary_cal = config.get("primary_calendar_account", "gagansokhal077@gmail.com")

    # 1. Fetch Calendar Schedule
    try:
        today_events = get_today_events()
    except Exception as e:
        today_events = []
        print(f"Calendar fetch error: {e}", file=sys.stderr)

    try:
        week_events = get_upcoming_events(days=7)
    except Exception as e:
        week_events = []

    # 2. Fetch Unread Emails across all accounts and mark as read
    try:
        email_data = get_all_unread_emails(max_per_account=10, mark_as_read=True)
    except Exception as e:
        email_data = {"accounts_count": 0, "total_unread": 0, "results": []}
        print(f"Gmail fetch error: {e}", file=sys.stderr)

    # Compile email categories & action items
    college_emails = []
    professional_emails = []
    personal_emails = []
    newsletter_count = 0
    action_items = []

    for acc_res in email_data.get("results", []):
        for em in acc_res.get("emails", []):
            cat = em["category"]
            sender_clean = em["sender"].split('<')[0].strip(' "\'')
            
            item_summary = {
                "account": em["account"],
                "sender": sender_clean,
                "subject": em["subject"],
                "urgency": em["urgency"],
                "deadline": em["deadline"],
                "requires_reply": em["requires_reply"]
            }

            if "College" in cat:
                college_emails.append(item_summary)
            elif "Professional" in cat:
                professional_emails.append(item_summary)
            elif "Personal" in cat:
                personal_emails.append(item_summary)
            else:
                newsletter_count += 1

            # Action item triggers
            if em["requires_reply"]:
                action_items.append(f"Reply to *{sender_clean}* regarding '_{em['subject']}_'")
            if em["deadline"]:
                action_items.append(f"Deadline mentioned by *{sender_clean}*: {em['deadline']} ('_{em['subject']}_')")
            if em["urgency"] == "HIGH":
                action_items.append(f"High urgency notification from *{sender_clean}*: '_{em['subject']}_'")

    # Deduplicate action items
    action_items = list(dict.fromkeys(action_items))

    # Build Briefing Message
    lines = []
    lines.append(f"🌅 *GOOD MORNING, GAGAN!*\n📅 *{date_str}* | ⏰ *{time_str}*\n")

    # Section 1: Today's Schedule
    lines.append(f"📅 *TODAY'S SCHEDULE* (`{primary_cal}`)")
    if today_events:
        for ev in today_events:
            loc = f" 📍 {ev['location']}" if ev['location'] else ""
            lines.append(f" • ⏰ *{ev['start']}* — {ev['summary']}{loc}")
    else:
        lines.append(" • ✨ No meetings or events scheduled today. Clear agenda!")
    lines.append("")

    # Section 2: Important Emails
    total_unread = email_data.get("total_unread", 0)
    acc_count = email_data.get("accounts_count", 0)
    lines.append(f"📬 *INBOX HIGHLIGHTS* ({total_unread} unread across {acc_count} accounts)")

    if college_emails:
        lines.append("\n*🎓 College & Academics (NITJ):*")
        for em in college_emails[:4]:
            urg = "🔴 " if em['urgency'] == 'HIGH' else ""
            lines.append(f" • {urg}*{em['sender']}* — {em['subject']}")

    if professional_emails:
        lines.append("\n*💼 Career & Professional:*")
        for em in professional_emails[:4]:
            urg = "🔴 " if em['urgency'] == 'HIGH' else ""
            lines.append(f" • {urg}*{em['sender']}* — {em['subject']}")

    if personal_emails:
        lines.append("\n*👤 Personal & Direct:*")
        for em in personal_emails[:3]:
            lines.append(f" • *{em['sender']}* — {em['subject']}")

    if newsletter_count > 0:
        lines.append(f"\n_ℹ️ Plus {newsletter_count} promotional/newsletter updates._")

    if total_unread == 0:
        lines.append(" • ✨ All 6 inboxes are at Inbox Zero!")

    lines.append("")

    # Section 3: Upcoming Deadlines & Week Events
    if week_events:
        lines.append("🗓️ *UPCOMING THIS WEEK:*")
        for ev in week_events[:4]:
            lines.append(f" • {ev['start']} — {ev['summary']}")
        lines.append("")

    # Section 4: Action Items
    if action_items:
        lines.append("❗ *ACTION ITEMS FOR TODAY:*")
        for idx, act in enumerate(action_items[:5], 1):
            lines.append(f" {idx}. {act}")
        lines.append("")
    else:
        lines.append("🎯 *FOCUS:* No urgent action items detected. Great day to build and learn!\n")

    lines.append("Have a powerful and productive day! 🚀")
    return "\n".join(lines)

if __name__ == '__main__':
    dry_run = "--dry-run" in sys.argv
    briefing = generate_morning_briefing()

    print("\n" + "=" * 60)
    print("           JARVIS MORNING BRIEFING PREVIEW")
    print("=" * 60)
    print(briefing)
    print("=" * 60 + "\n")

    if not dry_run:
        print("Delivering morning briefing to Telegram...")
        res = send_telegram_message(briefing)
        print(f"✅ Briefing successfully delivered to Telegram! Message ID: {res['message_id']}")
    else:
        print("Dry run complete (not sent to Telegram).")

