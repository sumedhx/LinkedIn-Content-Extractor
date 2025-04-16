from fastapi import FastAPI, Request
import os, pickle, time, random, re, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright

# ========== ENV + FastAPI ==========
load_dotenv()
app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

COOKIES_FILE = 'cookies.pkl'
LINKEDIN_URL = 'https://www.linkedin.com'

# ========== Playwright Setup ==========
def get_playwright_browser(headless=True):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        return browser

# ========== Login & Cookie Setup ==========
def ensure_logged_in():
    if os.path.exists(COOKIES_FILE):
        print("✅ Using saved cookies.")
        return

    print("🔓 Cookies not found. Opening browser for manual login...")
    browser = get_playwright_browser(headless=False)
    page = browser.new_page()

    page.goto("https://www.linkedin.com/login")

    # Give the user 60 seconds max to log in manually
    max_wait = 60
    start_time = time.time()
    logged_in = False

    print("⏳ You have 60 seconds to log in manually...")

    while time.time() - start_time < max_wait:
        if page.url != "https://www.linkedin.com/login":
            logged_in = True
            break
        time.sleep(2)  # check every 2 seconds

    if not logged_in:
        print("❌ Login not detected within time limit. Browser closed.")
        browser.close()
        raise Exception("Login failed or timed out.")

    # Save cookies after successful login
    cookies = page.context.cookies()
    with open(COOKIES_FILE, 'wb') as f:
        pickle.dump(cookies, f)
        print("✅ Cookies saved.")

    browser.close()

# ========== Notion ==========
def notion_send(title, content, clean_url, image_url):
    published_date = datetime.now().astimezone(timezone.utc).isoformat()
    data = {
        "Title": {
            "title": [{
                "type": "text",
                "text": {"content": title or "No Title"},
                "annotations": {"bold": True}
            }]
        },
        "Content": {
            "rich_text": [{
                "type": "text",
                "text": {"content": content or "No Content"},
                "annotations": {"color": "green"}
            }]
        },
        "URL": {"url": clean_url},
        "ImageURL": {
            "rich_text": [{
                "type": "text",
                "text": {
                    "content": "\n".join(image_url) if image_url else "No images"
                }
            }]
        },
        "PostImages": {
            "files": [
                {
                    "type": "external",
                    "name": f"image_{i+1}",
                    "external": {"url": url}
                }
                for i, url in enumerate(image_url)
            ]
        },
        "Published": {"date": {"start": published_date}}
    }

    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers={
            "Authorization": f"Bearer {NOTION_API_KEY}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        },
        json={"parent": {"database_id": NOTION_DATABASE_ID}, "properties": data}
    )
    print("✅ Notion response:", res.status_code, res.json())

# ========== FastAPI Webhook ==========
@app.post("/webhook")
async def receive_update(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    match = re.search(r'(https?://www\.linkedin\.com/[^\s]+)', text)
    if not match:
        requests.post(TELEGRAM_API_URL, json={
            "chat_id": chat_id,
            "text": "❗ Please send a valid LinkedIn post link."
        })
        return {"status": "invalid_url"}

    linkedin_url = match.group(1)
    clean_url = linkedin_url.split("?")[0]

    # Ensure we're logged in (save cookies if needed)
    ensure_logged_in()

    browser = get_playwright_browser(headless=True)
    page = browser.new_page()

    # Load cookies
    with open(COOKIES_FILE, 'rb') as f:
        cookies = pickle.load(f)
        for cookie in cookies:
            page.context.add_cookies([cookie])
    
    page.goto("https://www.linkedin.com/feed/")
    time.sleep(4)

    # Go to LinkedIn post
    page.goto(linkedin_url)

    # Wait for main post container to load
    try:
        page.wait_for_selector(".update-components-actor__title", timeout=15000)
    except:
        print("❌ LinkedIn post not fully loaded. Try again later.")
        browser.close()
        return {"status": "post_not_loaded"}

    # Scroll to trigger loading
    for _ in range(3):
        page.keyboard.press("PageDown")
        time.sleep(random.uniform(1.5, 2.5))

    # Parse page
    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')

    # ==== Title from Author ====
    author_block = soup.find("span", class_="update-components-actor__title")
    author_name = "LinkedIn User"
    if author_block:
        inner_name_span = author_block.find("span", attrs={"aria-hidden": "true"})
        if inner_name_span:
            author_name = inner_name_span.get_text(strip=True)
    title = f"Post by {author_name}"
    print("👤 Author:", author_name)

    # ==== Content ====
    content = "No content found."
    content_div = soup.find("div", class_="attributed-text-segment-list__container")
    if content_div:
        content = content_div.get_text(strip=True)
    else:
        post_div = soup.find("div", class_="update-components-text")
        if post_div:
            content = post_div.get_text(strip=True)
    print("📝 Content:", content)

    # ==== Post Images Only (feedshare-shrink) ====
    image_urls = []
    seen = set()
    for img in soup.find_all("img"):
        src = img.get("src")
        if src and "feedshare-shrink" in src and src not in seen:
            seen.add(src)
            image_urls.append(src)
    print("🖼️ Post Images:", image_urls)

    # ==== Send to Notion ====
    notion_send(title, content, clean_url, image_urls)

    # ==== Respond to Telegram ====
    msg = f"✅ *Added to Notion!*\n\n*Title:* {title}\n*URL:* {clean_url}\n\n*Content:* {content[:300]}..."
    requests.post(TELEGRAM_API_URL, json={
        "chat_id": chat_id,
        "text": msg,
        "parse_mode": "Markdown"
    })

    browser.close()
    return {"status": "ok"}
