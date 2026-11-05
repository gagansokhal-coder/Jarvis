"""
LeetCode Automation Agent for Gagan AI.
Supports:
- Real-time GraphQL daily coding challenge discovery
- Instant browser launch to today's daily streak problem
- Autonomous problem explanation & solution intuition
"""
import os
import sys
import requests

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from automation.laptop_controller import open_url

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"

def get_daily_challenge() -> dict:
    """Fetch today's active LeetCode daily coding challenge."""
    query = """
    query questionOfToday {
        activeDailyCodingChallengeQuestion {
            date
            link
            question {
                questionId
                questionFrontendId
                title
                titleSlug
                difficulty
            }
        }
    }
    """
    try:
        r = requests.post(LEETCODE_GRAPHQL, json={"query": query}, timeout=8)
        if r.status_code == 200:
            data = r.json().get("data", {}).get("activeDailyCodingChallengeQuestion", {})
            q = data.get("question", {})
            link = data.get("link", "")
            full_url = f"https://leetcode.com{link}"
            return {
                "success": True,
                "title": q.get("title", "Daily Challenge"),
                "difficulty": q.get("difficulty", "Medium"),
                "number": q.get("questionFrontendId", ""),
                "slug": q.get("titleSlug", ""),
                "url": full_url,
                "date": data.get("date", "")
            }
    except Exception as e:
        print(f"LeetCode API error: {e}")

    return {
        "success": False,
        "title": "LeetCode Daily Challenge",
        "difficulty": "",
        "number": "",
        "slug": "",
        "url": "https://leetcode.com/problemset/all/"
    }

def open_daily_streak() -> tuple[bool, str]:
    """Fetch and open today's LeetCode daily problem in Chrome on physical screen."""
    daily = get_daily_challenge()
    target_url = daily["url"]
    open_url(target_url)

    if daily["success"]:
        msg = f"Opening today's LeetCode daily streak question: {daily['number']}. {daily['title']}, difficulty {daily['difficulty']}."
    else:
        msg = "Opening LeetCode problemset for your daily streak, Gagan."
    return True, msg

if __name__ == "__main__":
    res = get_daily_challenge()
    print("LeetCode Daily:", res)
