FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
 
COPY worker/requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Download spaCy model and pre-cache sentence transformers model
RUN python -m spacy download en_core_web_sm

# Pre-download sentence-transformers model to avoid runtime downloads
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

COPY worker/ .

# Copy backend app code for database models and core modules
COPY backend/app ./app

RUN mkdir -p /app/data /app/upload

ENV PYTHONPATH=/app

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Waiting for Redis..."\n\
sleep 10\n\
echo "Starting Celery worker..."\n\
celery -A celery_app worker --loglevel=info --concurrency=2 -Q contract_preprocessing,contract_classification' > /app/start_worker.sh && chmod +x /app/start_worker.sh

CMD ["/app/start_worker.sh"]
