"""
Model cache for SBERT and spaCy models to prevent reloading on every task.
Implements singleton pattern for efficient model sharing across worker processes.
"""

import logging
import threading
from typing import Optional
import spacy
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

class ModelCache:
    """Singleton cache for ML models to prevent repeated loading."""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ModelCache, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._sbert_model = None
            self._spacy_model = None
            self._sbert_lock = threading.Lock()
            self._spacy_lock = threading.Lock()
            self._initialized = True
    
    def get_sbert_model(self) -> Optional[SentenceTransformer]:
        """Get cached SBERT model, loading if necessary."""
        if self._sbert_model is None:
            with self._sbert_lock:
                if self._sbert_model is None:
                    try:
                        logger.info("Loading SBERT model (cached for worker lifecycle)")
                        self._sbert_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
                        # Disable progress bars for cleaner logs
                        self._sbert_model.encode("test", show_progress_bar=False)
                        logger.info("SBERT model loaded and cached successfully")
                    except Exception as e:
                        logger.error(f"Failed to load SBERT model: {e}")
                        self._sbert_model = None
        
        return self._sbert_model
    
    def get_spacy_model(self) -> Optional[spacy.Language]:
        """Get cached spaCy model, loading if necessary."""
        if self._spacy_model is None:
            with self._spacy_lock:
                if self._spacy_model is None:
                    try:
                        logger.info("Loading spaCy model (cached for worker lifecycle)")
                        self._spacy_model = spacy.load("en_core_web_sm")
                        logger.info("spaCy model loaded and cached successfully")
                    except OSError:
                        logger.warning("spaCy model 'en_core_web_sm' not found. Some features may be limited.")
                        self._spacy_model = None
        
        return self._spacy_model
    
    def clear_cache(self):
        """Clear all cached models (for testing/debugging)."""
        with self._sbert_lock:
            self._sbert_model = None
        with self._spacy_lock:
            self._spacy_model = None
        logger.info("Model cache cleared")

# Global instance
model_cache = ModelCache()
