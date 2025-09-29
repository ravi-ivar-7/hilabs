#!/usr/bin/env python3
"""
Celery worker for HiLabs contract processing
"""

# Import shared Celery app
from celery_app import celery_app

# Import task modules to register them
from tasks import stage1_preprocessing, stage2_spacy_classification

if __name__ == '__main__':
    celery_app.start()
