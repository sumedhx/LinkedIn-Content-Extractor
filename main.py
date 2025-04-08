
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

# ========== ENV + FastAPI ==========
load_dotenv()
app = FastAPI()

BOT_TOKEN = os.getenv("BOT_TOKEN")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

COOKIES_FILE = 'cookies.pkl'
LINKEDIN_URL = 'https://www.linkedin.com'

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

def notion_send(title, content, clean_url, image_url):
    published_date = datetime.now().astimezone(timezone.utc).isoformat()
    data = {
        "Title": {
            "title": [{
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

    driver = get_driver(headless=True)
    driver.get(LINKEDIN_URL)

    # Load cookies
    if os.path.exists(COOKIES_FILE):
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
    time.sleep(6)

    # Scroll to trigger loading
    actions = ActionChains(driver)
    for _ in range(3):
        actions.send_keys(Keys.PAGE_DOWN).perform()
        time.sleep(random.uniform(1.5, 2.5))

    # Parse page
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # ==== Title from Author ====
    author_span = soup.find("span", class_="feed-shared-actor__name")
    author_name = author_span.get_text(strip=True) if author_span else "LinkedIn User"
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

    print("🖼️ Post Images:")
    for img in image_urls:
        print("-", img)

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














# Get bot link > extrat content> extract all images of the page(❌)> push to notion

# from fastapi import FastAPI, Request
# import os, pickle, time, random, re, requests
# from bs4 import BeautifulSoup
# from dotenv import load_dotenv
# from datetime import datetime, timezone
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.common.by import By
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.action_chains import ActionChains
# from webdriver_manager.chrome import ChromeDriverManager

# # ========== ENV + FastAPI ==========
# load_dotenv()
# app = FastAPI()

# BOT_TOKEN = os.getenv("BOT_TOKEN")
# NOTION_API_KEY = os.getenv("NOTION_API_KEY")
# NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
# TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# COOKIES_FILE = 'cookies.pkl'
# LINKEDIN_URL = 'https://www.linkedin.com'

# def get_chrome_options(headless=True):
#     options = Options()
#     options.add_argument('--disable-blink-features=AutomationControlled')
#     options.add_experimental_option('excludeSwitches', ['enable-automation'])
#     options.add_experimental_option('useAutomationExtension', False)
#     options.add_argument("--start-maximized")
#     if headless:
#         options.add_argument('--headless=new')
#         options.add_argument("--disable-gpu")
#         options.add_argument("--no-sandbox")
#         options.add_argument("--window-size=1920,1080")
#     return options

# def get_driver(headless=True):
#     return webdriver.Chrome(
#         service=Service(ChromeDriverManager().install()),
#         options=get_chrome_options(headless)
#     )

# def notion_send(title, content, clean_url, image_url):
#     published_date = datetime.now().astimezone(timezone.utc).isoformat()
#     data = {
#         "Title": {
#             "title": [{
#                 "text": {"content": title or "No Title"},
#                 "annotations": {"bold": True}
#             }]
#         },
#         "Content": {
#             "rich_text": [{
#                 "type": "text",
#                 "text": {"content": content or "No Content"},
#                 "annotations": {"color": "green"}
#             }]
#         },
#         "URL": {"url": clean_url},
#         "ImageURL": {"url": image_url if image_url else None},
#         "Published": {"date": {"start": published_date}}
#     }

#     res = requests.post(
#         "https://api.notion.com/v1/pages",
#         headers={
#             "Authorization": f"Bearer {NOTION_API_KEY}",
#             "Content-Type": "application/json",
#             "Notion-Version": "2022-06-28"
#         },
#         json={"parent": {"database_id": NOTION_DATABASE_ID}, "properties": data}
#     )
#     print("✅ Notion response:", res.status_code, res.json())

# @app.post("/webhook")
# async def receive_update(request: Request):
#     data = await request.json()
#     message = data.get("message", {})
#     chat_id = message.get("chat", {}).get("id")
#     text = message.get("text", "")

#     match = re.search(r'(https?://www\.linkedin\.com/[^\s]+)', text)
#     if not match:
#         requests.post(TELEGRAM_API_URL, json={
#             "chat_id": chat_id,
#             "text": "❗ Please send a valid LinkedIn post link."
#         })
#         return {"status": "invalid_url"}

#     linkedin_url = match.group(1)
#     clean_url = linkedin_url.split("?")[0]

#     driver = get_driver(headless=True)
#     driver.get(LINKEDIN_URL)

#     # Load cookies
#     if os.path.exists(COOKIES_FILE):
#         with open(COOKIES_FILE, 'rb') as f:
#             cookies = pickle.load(f)
#             for cookie in cookies:
#                 if 'expiry' in cookie:
#                     del cookie['expiry']
#                 driver.add_cookie(cookie)
#         driver.get("https://www.linkedin.com/feed/")
#         time.sleep(4)

#     # Go to LinkedIn post
#     driver.get(linkedin_url)
#     time.sleep(6)

#     # Scroll to trigger loading
#     actions = ActionChains(driver)
#     for _ in range(3):
#         actions.send_keys(Keys.PAGE_DOWN).perform()
#         time.sleep(random.uniform(1.5, 2.5))

#     # Parse page
#     soup = BeautifulSoup(driver.page_source, 'html.parser')

#     # ==== Title from Author ====
#     author_span = soup.find("span", class_="feed-shared-actor__name")
#     author_name = author_span.get_text(strip=True) if author_span else "LinkedIn User"
#     title = f"Post by {author_name}"
#     print("👤 Author:", author_name)

#     # ==== Content ====
#     content = "No content found."
#     content_div = soup.find("div", class_="attributed-text-segment-list__container")
#     if content_div:
#         content = content_div.get_text(strip=True)
#     else:
#         post_div = soup.find("div", class_="update-components-text")
#         if post_div:
#             content = post_div.get_text(strip=True)

#     print("📝 Content:", content)

#     # ==== Image URLs ====
#     image_urls = []
#     for img in soup.find_all("img"):
#         src = img.get("src")
#         alt = img.get("alt", "").lower()
#         if src and src.startswith("https://") and "profile" not in alt and "emoji" not in src:
#             image_urls.append(src)

#     print("🖼️ Image URLs:")
#     for img in image_urls:
#         print("-", img)

#     # ==== Send to Notion ====
#     notion_send(title, content, clean_url, image_urls[0] if image_urls else None)

#     # ==== Respond to Telegram ====
#     msg = f"✅ *Added to Notion!*\n\n*Title:* {title}\n*URL:* {clean_url}\n\n*Content:* {content[:300]}..."
#     requests.post(TELEGRAM_API_URL, json={
#         "chat_id": chat_id,
#         "text": msg,
#         "parse_mode": "Markdown"
#     })

#     driver.quit()
#     return {"status": "ok"}
