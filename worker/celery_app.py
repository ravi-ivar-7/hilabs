#!/usr/bin/env python3
"""
Shared Celery app configuration for contract processing
"""
import sys
import os
from pathlib import Path
from celery import Celery
from celery.signals import worker_process_init
import logging

logger = logging.getLogger(__name__)

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
    # Optimize worker settings for better performance
    'worker_prefetch_multiplier': 1,  # Prevent worker from prefetching too many tasks
    'task_acks_late': True,  # Acknowledge tasks only after completion
    'worker_max_tasks_per_child': 50,  # Restart worker after 50 tasks to prevent memory leaks
})

@worker_process_init.connect
def init_worker_process(sender=None, **kwargs):
    """Initialize database and models once per worker process."""
    try:
        # Initialize database tables once per worker
        from app.core.database import init_db
        init_db()
        logger.info("Database tables initialized for worker process")
        
        # Pre-warm model cache to avoid loading delays on first task
        from model_cache import model_cache
        model_cache.get_spacy_model()
        model_cache.get_sbert_model()
        logger.info("Models pre-loaded and cached for worker process")
        
    except Exception as e:
        logger.error(f"Failed to initialize worker process: {e}")

celery_app.autodiscover_tasks(['tasks'])
