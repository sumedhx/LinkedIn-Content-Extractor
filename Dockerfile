# Use official Python image
FROM python:3.10-slim

# Install OS dependencies for Chrome + Selenium
RUN apt-get update && apt-get install -y \
    wget unzip gnupg curl fonts-liberation libappindicator3-1 \
    libasound2 libnspr4 libnss3 libxss1 libgbm-dev libx11-xcb1 \
    libxcomposite1 libxdamage1 libxi6 libxtst6 xdg-utils \
    chromium chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Copy files
COPY . /app

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose port
EXPOSE 8000

# Run FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
