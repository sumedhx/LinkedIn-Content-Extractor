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

# 🔄 LinkedIn Scraper – Execution Flow

## 1. User Interaction
- User sends a message to the **Telegram Bot**
- Message contains a **LinkedIn post URL**

---

## 2. Telegram Webhook
- Telegram forwards the message to the backend
- **FastAPI `/webhook`** endpoint receives the update

---

## 3. URL Validation
- Backend checks if the message contains a valid LinkedIn URL

### Possible Outcomes
- ❌ **Invalid URL**
  - Bot replies: *"Invalid LinkedIn link"*
  - Process ends
- ✅ **Valid URL**
  - URL is extracted and cleaned
  - Flow continues

---

## 4. Authentication Layer
- Backend checks for saved LinkedIn cookies (`cookies.pkl`)

### Authentication Logic
- ✅ **Cookies exist**
  - Reuse existing LinkedIn session
- ❌ **Cookies missing**
  - Open browser
  - Manual LinkedIn login required
  - Save cookies for future use

---

## 5. Scraping Engine
- Launch **Playwright** in headless mode
- Load cookies into browser session
- Open LinkedIn feed
- Navigate to the target LinkedIn post URL
- Wait for post container to load

### Error Handling
- ❌ **Post not loaded**
  - Return error
  - End process
- ✅ **Post loaded**
  - Continue to extraction

---

## 6. Data Extraction
- Scroll page to trigger lazy loading
- Extract full page HTML
- Parse HTML using **BeautifulSoup**

### Extracted Data
- 👤 Author name  
- 📝 Post text content  
- 🖼️ Post images (`feedshare-shrink`)

---

## 7. Data Storage
- Format extracted data for **Notion API**
- Create a new page in Notion database with:
  - Title
  - Content
  - Clean LinkedIn URL
  - Image URLs
  - Timestamp

---

## 8. User Feedback
- Send confirmation message to Telegram
- Include preview of saved content
- Close browser
- Return success response (`OK`)
