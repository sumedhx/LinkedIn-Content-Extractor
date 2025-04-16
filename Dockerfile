# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy only the necessary files into the container
COPY requirements.txt /app/
COPY .env /app/
COPY app /app/app
COPY cookies.pkl /app/

# Install system dependencies needed for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    libx11-dev \
    libnss3-dev \
    libgdk-pixbuf2.0-0 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libgtk-3-0 \
    libgbm-dev \
    libnotify4 \
    libgconf-2-4 \
    libxss1 \
    fonts-liberation \
    libappindicator3-1 \
    libcurl4 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the FastAPI app port
EXPOSE 8000

# Command to run the FastAPI app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
