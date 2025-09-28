#!/usr/bin/env python3
"""
Celery worker for HiLabs contract processing
"""
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from tasks.contract_preprocessing import celery_app

if __name__ == '__main__':
    celery_app.start()
