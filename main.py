from fastapi import FastAPI, Request
import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT-TOKEN")
print(BOT_TOKEN)

# Initialize FastAPI app
app = FastAPI()

# Telegram API URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

def scrape_linkedin_post(url):
    """Scrape LinkedIn post content using BeautifulSoup."""
    headers = {"User-Agent": "Mozilla/5.0"}  # Prevent getting blocked
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return "Failed to fetch LinkedIn post."

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Try extracting post content (LinkedIn may change structure)
    post_content = soup.find("meta", property="og:description")  # Fetch meta description

    print(post_content)
    return post_content["content"] if post_content else "Could not extract post content."

@app.post("/webhook")
async def receive_update(request: Request):
    data = await request.json()
    message = data.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    # Check if the message contains a valid LinkedIn post link
    if "linkedin.com" in text:
        post_content = scrape_linkedin_post(text)
        response_text = f"🔗 LinkedIn Post Content:\n\n{post_content}"
        print(post_content)
    else:
        response_text = "Please send a valid LinkedIn post link."

    # Send response to Telegram
    requests.post(TELEGRAM_API_URL, json={"chat_id": chat_id, "text": response_text})

    return {"status": "ok"}
