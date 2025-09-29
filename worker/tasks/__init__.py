# Import all task modules to ensure they are registered with Celery
from . import stage1_preprocessing
from . import stage2_spacy_classification

__all__ = [
    'stage1_preprocessing',
    'stage2_spacy_classification'
]