FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head 2>/dev/null || true && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
