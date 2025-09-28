#!/usr/bin/env python3
"""
Shared Celery app configuration for HiLabs contract processing
"""
import sys
import os
from pathlib import Path
from celery import Celery

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

os.environ['DATABASE_URL'] = f"sqlite:///{backend_path}/contracts.db"

# Create shared Celery app
celery_app = Celery('hilabs_worker')
celery_app.config_from_object({
    'broker_url': 'redis://localhost:6379/0',
    'result_backend': 'redis://localhost:6379/0',
    'task_serializer': 'json',
    'accept_content': ['json'],
    'result_serializer': 'json',
    'timezone': 'UTC',
    'enable_utc': True,
})
