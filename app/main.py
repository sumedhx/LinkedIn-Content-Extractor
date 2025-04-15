from fastapi import FastAPI, Request
import os, pickle, time, random, re, requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from datetime import datetime, timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ========== ENV + FastAPI ==========
load_dotenv()
app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

COOKIES_FILE = 'cookies.pkl'
LINKEDIN_URL = 'https://www.linkedin.com'

# ========== Selenium Setup ==========
def get_chrome_options(headless=True):
    options = Options()
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--start-maximized")
    if headless:
        options.add_argument('--headless=new')
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--window-size=1920,1080")
    return options

def get_driver(headless=True):
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=get_chrome_options(headless)
    )

# ========== Login & Cookie Setup ==========
def ensure_logged_in():
    if os.path.exists(COOKIES_FILE):
        print("✅ Using saved cookies.")
        return

    print("🔓 Cookies not found. Opening browser for manual login...")
    driver = get_driver(headless=False)
    driver.get("https://www.linkedin.com/login")

    # Give the user 60 seconds max to log in manually
    max_wait = 60
    start_time = time.time()
    logged_in = False

    print("⏳ You have 60 seconds to log in manually...")

    while time.time() - start_time < max_wait:
        current_url = driver.current_url
        if "feed" in current_url or "linkedin.com/in/" in current_url:
            logged_in = True
            break
        time.sleep(2)  # check every 2 seconds

    if not logged_in:
        print("❌ Login not detected within time limit. Browser closed.")
        driver.quit()
        raise Exception("Login failed or timed out.")

    # Save cookies after successful login
    with open(COOKIES_FILE, 'wb') as f:
        pickle.dump(driver.get_cookies(), f)
        print("✅ Cookies saved.")

    driver.quit()


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

    driver = get_driver(headless=True)
    driver.get(LINKEDIN_URL)

    # Load cookies
    with open(COOKIES_FILE, 'rb') as f:
        cookies = pickle.load(f)
        for cookie in cookies:
            if 'expiry' in cookie:
                del cookie['expiry']
            driver.add_cookie(cookie)
    driver.get("https://www.linkedin.com/feed/")
    time.sleep(4)

    # Go to LinkedIn post
    driver.get(linkedin_url)

    # Wait for main post container to load
    #Added this because when send a link it sometimes process the old/previous link
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "update-components-actor__title"))
        )
    except:
        print("❌ LinkedIn post not fully loaded. Try again later.")
        driver.quit()
        return {"status": "post_not_loaded"}

    # Scroll to trigger loading
    actions = ActionChains(driver)
    for _ in range(3):
        actions.send_keys(Keys.PAGE_DOWN).perform()
        time.sleep(random.uniform(1.5, 2.5))

    # Parse page
    soup = BeautifulSoup(driver.page_source, 'html.parser')

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

    driver.quit()
    return {"status": "ok"}
