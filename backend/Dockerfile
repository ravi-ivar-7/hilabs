FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/

# Create data directory for SQLite
RUN mkdir -p /app/data

EXPOSE 8000

# Create startup script
RUN echo '#!/bin/bash\n\
echo "Waiting for dependencies..."\n\
sleep 5\n\
echo "Creating database tables..."\n\
python -c "from app.core.database import init_db; from app.models import Contract, FileRecord, ContractClause, ProcessingLog; init_db()"\n\
echo "Starting FastAPI server..."\n\
uvicorn app.main:app --host 0.0.0.0 --port 8000' > /app/start.sh && chmod +x /app/start.sh

CMD ["/app/start.sh"]
