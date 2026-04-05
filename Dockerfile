# Dockerfile for Vedic Kundali API
FROM python:3.11-slim

# Install system dependencies required by pyswisseph
RUN apt-get update && apt-get install -y \
    libsqlite3-0 \
    libsqlite3-dev \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Copy Swiss Ephemeris data files
COPY *.se1 /app/
COPY kundali/*.se1 /app/kundali/

# Expose port
EXPOSE 8000

# Set environment variables
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Start the application
CMD ["uvicorn", "api_server:app", "--host", "0.0.0.0", "--port", "8000"]
