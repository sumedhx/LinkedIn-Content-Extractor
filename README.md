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

## Run
- uvicorn main:app --reload

