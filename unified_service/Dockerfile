FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code from all services
COPY ../market_data_service/app /app/market_data
COPY ../decision_engine/app /app/decision_engine
COPY ../trading_service/app /app/trading_service
COPY app /app/app

# Expose port
EXPOSE 8080

# Run the unified service
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
