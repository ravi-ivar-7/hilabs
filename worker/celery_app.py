#!/usr/bin/env python3
"""
Shared Celery app configuration for contract processing
"""
import sys
import os
from pathlib import Path
from celery import Celery

# Set up paths for Docker container or local development
if os.path.exists('/app'):
    sys.path.insert(0, "/app")
    if 'DATABASE_URL' not in os.environ:
        os.environ['DATABASE_URL'] = "sqlite:////app/data/contracts.db"
else:
    backend_path = Path(__file__).parent.parent / "backend"
    sys.path.insert(0, str(backend_path))
    if 'DATABASE_URL' not in os.environ:
        os.environ['DATABASE_URL'] = f"sqlite:///{backend_path}/app/data/contracts.db"

celery_app = Celery('hilabs_worker')
celery_app.config_from_object({
    'broker_url': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    'result_backend': os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
})

celery_app.autodiscover_tasks(['tasks'])
