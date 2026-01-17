# LinkedIn-Content-Extractor

[sumedhx](https://github.com/sumedhx) | [vjangale](https://github.com/vjangale) | [TonyMali](https://github.com/TonyMali)

## Tech Used
- LinkedIn
- Telegram Bot
- Beautiful Soup
- FastAPI
- Server(Ngrok, AWS)
- Notion
- selenium

## Work Flow
- User can copy LinkedIn post url and share it to the telegram bot. 
- The Bot will check if is a valid linkedin link or not.
- Backend will extract the content from post using beautiful soup.
- The extracted content will be saved into the Notion database.

## Database Link
- https://www.notion.so/1ca1b6e177c680f8b85fc90d9b1790f1?v=1c9959f97de580f88299000c0c36a662

## Run
- uvicorn main:app --reload



## Stepwise Execution Flow
┌────────────────────────────┐
│ 1. USER INTERACTION        │
└────────────────────────────┘
        │
        ▼
User sends a message to the Telegram Bot
containing a LinkedIn post URL

        │
        ▼
┌────────────────────────────┐
│ 2. TELEGRAM WEBHOOK        │
└────────────────────────────┘
        │
        ▼
FastAPI (/webhook) receives the update

        │
        ▼
┌────────────────────────────┐
│ 3. URL VALIDATION          │
└────────────────────────────┘
        │
        ├── ❌ No LinkedIn URL
        │       → Reply: "Invalid LinkedIn link"
        │       → END
        │
        └── ✅ Valid LinkedIn URL
                │
                ▼
┌────────────────────────────┐
│ 4. AUTHENTICATION LAYER    │
└────────────────────────────┘
        │
        ▼
Check for saved LinkedIn cookies (cookies.pkl)

        │
        ├── ✅ Cookies exist
        │       → Use saved session
        │
        └── ❌ Cookies missing
                → Open browser
                → Manual LinkedIn login
                → Save cookies

        │
        ▼
┌────────────────────────────┐
│ 5. SCRAPING ENGINE         │
└────────────────────────────┘
        │
        ▼
Launch Playwright (headless)

        │
        ▼
Load cookies into browser session

        │
        ▼
Open LinkedIn feed → Navigate to post URL

        │
        ▼
Wait for post container to load

        │
        ├── ❌ Post not loaded
        │       → Return error
        │       → END
        │
        └── ✅ Post loaded
                │
                ▼
┌────────────────────────────┐
│ 6. DATA EXTRACTION         │
└────────────────────────────┘
        │
        ▼
Scroll page to trigger lazy loading

        │
        ▼
Extract page HTML

        │
        ▼
Parse HTML using BeautifulSoup

        │
        ▼
Extract:
• Author name  
• Post text content  
• Post images (feedshare-shrink)

        │
        ▼
┌────────────────────────────┐
│ 7. DATA STORAGE            │
└────────────────────────────┘
        │
        ▼
Format data for Notion API

        │
        ▼
Create new page in Notion Database
with title, content, URL, images, timestamp

        │
        ▼
┌────────────────────────────┐
│ 8. USER FEEDBACK           │
└────────────────────────────┘
        │
        ▼
Send confirmation message to Telegram
with preview of saved content

        │
        ▼
Close browser → Return OK
