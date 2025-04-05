from fastapi import FastAPI, Request
import requests
from bs4 import BeautifulSoup
import os
import re
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# Initialize FastAPI app
app = FastAPI()

# Telegram API URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# Notion API Headers
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# LinkedIn scraper
def scrape_linkedin_post(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return "Failed to fetch LinkedIn post.", "No content", url

    soup = BeautifulSoup(response.text, "html.parser")

    title = soup.title.text if soup.title else "No Title Found"
    content_div = soup.find("div", class_="attributed-text-segment-list__container")
    content = content_div.get_text(strip=True) if content_div else "No content found."

    clean_url = url.split("?")[0]

    return title, content, clean_url

# Send to Notion
def create_page(data: dict):
    create_url = "https://api.notion.com/v1/pages"

    payload = {"parent": {"database_id": NOTION_DATABASE_ID}, "properties": data}

    res = requests.post(create_url, headers=HEADERS, json=payload)
    
    print("Status Code:", res.status_code)
    print("Response:", res.json())  # Print the full response from Notion
    
    return res

# Webhook handler
@app.post("/webhook")
async def receive_update(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    # Extract LinkedIn URL from the text
    match = re.search(r'(https?://www\.linkedin\.com/[^\s]+)', text)
    if match:
        linkedin_url = match.group(1)
        title, content, clean_url = scrape_linkedin_post(linkedin_url)
        published_date = datetime.now().astimezone(timezone.utc).isoformat()

        # Build data for Notion
        print("Title - ",title)
        print("Content - ",content)
        print(clean_url)
        notion_data = {
            "Title": {
                "title": [
                    {
                        "text": {
                            "content": title,
                        },
                        "annotations": {
                        "bold": True
                }
                    }
                ]
            },
            "Content": {
        "rich_text": [
            {
                "type": "text",
                "text": {
                    "content": content
                },
                "annotations": {
                    "color": "green"
                }
            }
        ]
    },
            "URL": {
                "url": clean_url
            },
            "Published": {"date": {"start": published_date}} 
        }

        create_page(notion_data)

        response_text = f"✅ *Added to Notion!*\n\n*Title:* {title}\n*URL:* {clean_url}\n\n*Content:* {content}"
    else:
        response_text = "❗ Please send a valid LinkedIn post link."

    # Send back to Telegram
    requests.post(TELEGRAM_API_URL, json={
        "chat_id": chat_id,
        "text": response_text,
        "parse_mode": "Markdown"
    })

    return {"status": "ok"}
