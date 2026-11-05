"""
GitHub Navigation & Repository Controller for Gagan AI.
Owner Profile: gagansokhal-coder
"""
import os
import sys
import re

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from automation.laptop_controller import open_url

GITHUB_USERNAME = "gagansokhal-coder"

def open_github_profile(username: str = GITHUB_USERNAME) -> tuple[bool, str]:
    """Open GitHub user profile in Chrome."""
    url = f"https://github.com/{username}"
    open_url(url)
    return True, f"Opening GitHub profile for {username} in Chrome, Gagan."

def open_github_repo(repo_name: str, username: str = GITHUB_USERNAME) -> tuple[bool, str]:
    """Open specific repository under Gagan's account."""
    clean_repo = repo_name.strip().replace(" ", "-")
    url = f"https://github.com/{username}/{clean_repo}"
    open_url(url)
    return True, f"Opening repository {clean_repo} on GitHub for you, Gagan."

def handle_github_request(user_text: str) -> tuple[bool, str]:
    """Process natural language GitHub instructions."""
    clean = user_text.lower().strip()

    # Match specific repo request (e.g. "go to my repo Jarvis", "open repo gaganAI")
    repo_match = re.search(r'\b(?:repo|repository)\s+([a-zA-Z0-9_\-]+)', clean)
    if repo_match:
        target_repo = repo_match.group(1).strip()
        return open_github_repo(target_repo)

    # Match profile / account request
    if any(k in clean for k in ["my account", "gagansokhal-coder", "my github", "profile", "account"]):
        return open_github_profile()

    # General GitHub
    open_url("https://github.com")
    return True, "Opening GitHub in Chrome for you, Gagan."

if __name__ == "__main__":
    print(handle_github_request("go to my account gagansokhal-coder"))
