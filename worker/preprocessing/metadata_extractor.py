import hashlib
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class MetadataExtractor:
    def __init__(self):
        pass
    
    def extract_file_metadata(self, file_bytes: bytes, filename: str, state: str) -> Dict[str, any]:
        try:
            file_size = len(file_bytes)
            file_hash = self._generate_file_hash(file_bytes)
            file_type = self._detect_file_type(filename)
            
            metadata = {
                "success": True,
                "filename": filename,
                "file_size": file_size,
                "file_hash": file_hash,
                "file_type": file_type,
                "state": state,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "processing_metadata": {
                    "extraction_method": None,
                    "text_length": None,
                    "page_count": None,
                    "processing_time": None
                },
                "error": None
            }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Metadata extraction failed: {str(e)}")
            return {
                "success": False,
                "filename": filename,
                "file_size": 0,
                "file_hash": None,
                "file_type": None,
                "state": state,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "processing_metadata": {},
                "error": str(e)
            }
    
    def extract_text_metadata(self, text: str, extraction_result: Dict = None) -> Dict[str, any]:
        try:
            word_count = len(text.split())
            char_count = len(text)
            line_count = len(text.split('\n'))
            
            text_metadata = {
                "success": True,
                "word_count": word_count,
                "character_count": char_count,
                "line_count": line_count,
                "text_density": word_count / max(char_count, 1),
                "avg_words_per_line": word_count / max(line_count, 1),
                "extraction_method": extraction_result.get("method") if extraction_result else None,
                "page_count": extraction_result.get("pages") if extraction_result else None,
                "error": None
            }
            
            return text_metadata
            
        except Exception as e:
            logger.error(f"Text metadata extraction failed: {str(e)}")
            return {
                "success": False,
                "word_count": 0,
                "character_count": 0,
                "line_count": 0,
                "text_density": 0,
                "avg_words_per_line": 0,
                "extraction_method": None,
                "page_count": None,
                "error": str(e)
            }
    
    def extract_contract_metadata(self, text: str, state: str) -> Dict[str, any]:
        try:
            contract_metadata = {
                "success": True,
                "state": state,
                "contract_type": self._detect_contract_type(text),
                "key_sections": self._identify_key_sections(text),
                "potential_attributes": self._identify_potential_attributes(text),
                "complexity_score": self._calculate_complexity_score(text),
                "error": None
            }
            
            return contract_metadata
            
        except Exception as e:
            logger.error(f"Contract metadata extraction failed: {str(e)}")
            return {
                "success": False,
                "state": state,
                "contract_type": "unknown",
                "key_sections": [],
                "potential_attributes": [],
                "complexity_score": 0,
                "error": str(e)
            }
    
    def _generate_file_hash(self, file_bytes: bytes) -> str:
        return hashlib.sha256(file_bytes).hexdigest()
    
    def _detect_file_type(self, filename: str) -> str:
        if filename.lower().endswith('.pdf'):
            return 'application/pdf'
        return 'unknown'
    
    def _detect_contract_type(self, text: str) -> str:
        text_lower = text.lower()
        
        contract_types = {
            'healthcare': ['healthcare', 'medical', 'hospital', 'clinic', 'patient'],
            'insurance': ['insurance', 'coverage', 'premium', 'deductible', 'claim'],
            'service': ['service', 'agreement', 'provider', 'vendor'],
            'employment': ['employment', 'employee', 'salary', 'benefits'],
            'lease': ['lease', 'rent', 'tenant', 'landlord', 'property']
        }
        
        for contract_type, keywords in contract_types.items():
            if any(keyword in text_lower for keyword in keywords):
                return contract_type
        
        return 'general'
    
    def _identify_key_sections(self, text: str) -> List[str]:
        sections = []
        
        section_patterns = [
            'terms and conditions',
            'payment terms',
            'termination',
            'liability',
            'confidentiality',
            'scope of work',
            'deliverables',
            'warranties',
            'indemnification'
        ]
        
        text_lower = text.lower()
        for pattern in section_patterns:
            if pattern in text_lower:
                sections.append(pattern)
        
        return sections
    
    def _identify_potential_attributes(self, text: str) -> List[str]:
        attributes = []
        
        attribute_patterns = [
            'effective date',
            'expiration date',
            'payment amount',
            'interest rate',
            'penalty clause',
            'notice period',
            'governing law',
            'jurisdiction'
        ]
        
        text_lower = text.lower()
        for pattern in attribute_patterns:
            if pattern in text_lower:
                attributes.append(pattern)
        
        return attributes
    
    def _calculate_complexity_score(self, text: str) -> float:
        word_count = len(text.split())
        unique_words = len(set(text.lower().split()))
        
        if word_count == 0:
            return 0.0
        
        complexity_factors = {
            'length': min(word_count / 1000, 1.0),
            'vocabulary_diversity': unique_words / word_count,
            'legal_terms': self._count_legal_terms(text) / max(word_count / 100, 1)
        }
        
        return sum(complexity_factors.values()) / len(complexity_factors)
    
    def _count_legal_terms(self, text: str) -> int:
        legal_terms = [
            'whereas', 'hereby', 'herein', 'thereof', 'pursuant',
            'notwithstanding', 'indemnify', 'covenant', 'warranty',
            'breach', 'default', 'remedy', 'jurisdiction', 'governing'
        ]
        
        text_lower = text.lower()
        return sum(1 for term in legal_terms if term in text_lower)
