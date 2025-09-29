"""
Clause extractor for healthcare contracts.
Extracts individual clauses from contract text using sentence splitting and normalization.
Based on HiLabs analysis for optimal clause detection.
"""

import logging
import re
from typing import Dict, List, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ClauseExtractionResult:
    """Result of clause extraction with metadata."""
    clauses: List[Dict[str, Any]]
    total_count: int
    extraction_method: str
    success: bool
    error: str = ""

class ClauseExtractor:
    """Extract clauses from healthcare contract text."""
    
    def __init__(self):
        """Initialize clause extractor with HiLabs-optimized settings."""
        self.min_clause_length = 20
        self.max_clause_length = 2000
        
        # Sentence boundary patterns
        self.sentence_endings = r'[.!?]'
        self.section_patterns = [
            r'\n\d+\.\d+',  # 1.1, 2.3, etc.
            r'\n[A-Z]\.',   # A., B., etc.
            r'\n\([a-z]\)', # (a), (b), etc.
        ]
    
    def extract_clauses(self, text: str) -> Dict[str, Any]:
        """Extract clauses from contract text.
        
        Args:
            text: Cleaned contract text
            
        Returns:
            Dictionary with extraction results
        """
        try:
            if not text or len(text.strip()) < 50:
                return {
                    "success": False,
                    "error": "Text too short for clause extraction",
                    "clauses": [],
                    "total_count": 0
                }
            
            raw_clauses = self._split_into_clauses(text)
            
            processed_clauses = []
            for i, clause_text in enumerate(raw_clauses):
                if self._is_valid_clause(clause_text):
                    clause_data = {
                        "clause_id": i + 1,
                        "text": clause_text.strip(),
                        "norm_text": self._normalize_text(clause_text),
                        "length": len(clause_text.strip()),
                        "detected_attributes": [],  # Will be populated in classification
                        "position": {
                            "start_char": text.find(clause_text),
                            "end_char": text.find(clause_text) + len(clause_text)
                        }
                    }
                    processed_clauses.append(clause_data)
            
            logger.info(f"Extracted {len(processed_clauses)} valid clauses from {len(raw_clauses)} raw segments")
            
            return {
                "success": True,
                "clauses": processed_clauses,
                "total_count": len(processed_clauses),
                "extraction_method": "sentence_splitting",
                "error": ""
            }
            
        except Exception as e:
            logger.error(f"Clause extraction failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "clauses": [],
                "total_count": 0
            }
    
    def _split_into_clauses(self, text: str) -> List[str]:
        """Split text into clause segments."""
        segments = []
        current_segment = ""
        
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            is_new_section = any(re.match(pattern, '\n' + line) for pattern in self.section_patterns)
            
            if is_new_section and current_segment:
                segments.append(current_segment.strip())
                current_segment = line
            else:
                if current_segment:
                    current_segment += " " + line
                else:
                    current_segment = line
        
        if current_segment:
            segments.append(current_segment.strip())
        
        final_clauses = []
        for segment in segments:
            if len(segment) > self.max_clause_length:
                sentences = re.split(self.sentence_endings, segment)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if sentence and len(sentence) >= self.min_clause_length:
                        final_clauses.append(sentence)
            else:
                final_clauses.append(segment)
        
        return final_clauses
    
    def _is_valid_clause(self, text: str) -> bool:
        """Check if text segment is a valid clause."""
        if not text or len(text.strip()) < self.min_clause_length:
            return False
            
        if len(text.strip()) > self.max_clause_length:
            return False
            
        # Filter out headers, footers, and metadata
        text_lower = text.lower().strip()
        
        # Skip common non-clause content
        skip_patterns = [
            r'^page \d+',
            r'^confidential',
            r'^proprietary',
            r'^\d+$',  # Just numbers
            r'^[a-z]$',  # Single letters
            r'^table of contents',
            r'^appendix',
            r'^exhibit',
        ]
        
        for pattern in skip_patterns:
            if re.match(pattern, text_lower):
                return False
        
        # Must contain some meaningful content (not just punctuation/numbers)
        word_count = len(re.findall(r'\b\w+\b', text))
        if word_count < 3:
            return False
            
        return True
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching purposes."""
        normalized = text.lower()
        
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove special characters but keep basic punctuation
        normalized = re.sub(r'[^\w\s.,;:()-]', '', normalized)
        
        return normalized.strip()
