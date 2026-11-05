"""
AI-driven Browser Automation via Playwright.
Enables Gagan AI to autonomously navigate websites, extract information,
take screenshots, and summarize web content with local LLM.
100% Dynamic: Zero hardcoded drives, paths, or usernames.
"""
import os
import sys
import re
import time
import urllib.parse
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

SCREENSHOTS_DIR = os.path.join(BASE_DIR, "data", "browser_screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

def browse_url(url: str, headless: bool = True, timeout_sec: int = 25, take_screenshot: bool = False) -> dict:
    """
    Navigate to a website with Playwright, extract clean readable text,
    page title, links, and optional screenshot.
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    result = {
        "url": url,
        "title": "",
        "text": "",
        "links": [],
        "screenshot": None,
        "success": False,
        "error": None
    }

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            page.goto(url, timeout=timeout_sec * 1000, wait_until="domcontentloaded")
            page.wait_for_timeout(1000)

            result["title"] = page.title()

            # Parse content with BeautifulSoup
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Remove noisy elements
            for tag in soup(["script", "style", "nav", "footer", "noscript", "svg"]):
                tag.decompose()

            raw_text = soup.get_text(separator=" ", strip=True)
            # Collapse whitespace
            clean_text = re.sub(r'\s+', ' ', raw_text).strip()
            result["text"] = clean_text[:4000]

            # Extract main links
            links = []
            for a in soup.find_all("a", href=True):
                href = a["href"]
                text = a.get_text(strip=True)
                if text and (href.startswith("http") or href.startswith("/")):
                    full_href = urllib.parse.urljoin(url, href)
                    links.append({"text": text[:60], "url": full_href})
                if len(links) >= 10:
                    break
            result["links"] = links

            # Capture screenshot if requested
            if take_screenshot:
                ts = int(time.time())
                ss_path = os.path.join(SCREENSHOTS_DIR, f"page_{ts}.png")
                page.screenshot(path=ss_path, full_page=False)
                result["screenshot"] = ss_path

            browser.close()
            result["success"] = True

    except Exception as e:
        result["error"] = str(e)

    return result

def search_web_playwright(query: str, max_results: int = 3) -> list:
    """
    Perform a search on DuckDuckGo using Playwright and extract clean search results.
    """
    encoded = urllib.parse.quote_plus(query)
    search_url = f"https://html.duckduckgo.com/html/?q={encoded}"

    results = []
    try:
        data = browse_url(search_url, headless=True)
        if data["success"] and data["text"]:
            soup = BeautifulSoup(data["text"], "html.parser")
            # Fallback text parsing if HTML structure differs
            results.append({"title": f"Search for: {query}", "snippet": data["text"][:600], "url": search_url})
    except Exception as e:
        results.append({"error": str(e)})

    return results

def summarize_web_page(url: str, focus: str = None) -> str:
    """
    Browse a URL and generate a natural 1-2 sentence spoken summary using local LLM.
    """
    page_data = browse_url(url, headless=True)
    if not page_data["success"]:
        return f"Could not access {url}: {page_data['error']}"

    text_snippet = page_data["text"][:1500]
    prompt = (
        f"You are Gagan AI. Summarize the following website content for Gagan in 1 to 2 clear, spoken sentences.\n"
        f"Page Title: {page_data['title']}\n"
        f"Content:\n{text_snippet}\n"
        f"Summary:"
    )

    try:
        import requests
        resp = requests.post("http://127.0.0.1:11434/api/generate", json={
            "model": "phi4-mini:latest",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 70, "num_ctx": 1024}
        }, timeout=20)
        return resp.json().get("response", "").strip() or page_data["title"]
    except Exception:
        return f"Loaded {page_data['title']}: {text_snippet[:200]}..."

if __name__ == "__main__":
    print("Testing Playwright Browser Agent:")
    res = browse_url("https://example.com")
    print("Title:", res["title"])
    print("Text snippet:", res["text"][:100])
    print("Success:", res["success"])

