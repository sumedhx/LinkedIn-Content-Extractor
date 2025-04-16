FROM python:3.10-slim

# Install required packages
RUN apt-get update && apt-get install -y \
    wget unzip gnupg curl fonts-liberation libappindicator3-1 \
    libasound2 libnspr4 libnss3 libxss1 libgbm-dev libx11-xcb1 \
    libxcomposite1 libxdamage1 libxi6 libxtst6 xdg-utils \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------
# ✅ Download Chrome for Testing (v114)
# -------------------------------------
RUN wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/114.0.5735.90/linux64/chrome-linux64.zip && \
    unzip chrome-linux64.zip && \
    mv chrome-linux64 /opt/chrome && \
    ln -s /opt/chrome/chrome /usr/bin/chromium && \
    rm chrome-linux64.zip

# -------------------------------------
# ✅ Download ChromeDriver (v114 match)
# -------------------------------------
RUN wget https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/114.0.5735.90/linux64/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip && \
    mv chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm -rf chromedriver-linux64*

# Set environment variables
ENV CHROME_BIN=/usr/bin/chromium
ENV PATH="/usr/bin/chromedriver:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Expose port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
