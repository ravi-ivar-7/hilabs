"""
Clause extractor for the 5 required contract attributes.
Extracts specific clauses from preprocessed contract text.
"""

import re
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class ClauseExtractor:
    """Extract the 5 required attributes from contract text."""
    
    def __init__(self):
        # Define extraction patterns for each attribute
        self.attribute_patterns = {
            'Medicaid Timely Filing': {
                'section_keywords': [
                    'submission and adjudication of medicaid claims',
                    'medicaid claims submission',
                    'medicaid timely filing'
                ],
                'content_keywords': [
                    'medicaid', 'claims', 'submit', 'days', 'rendered',
                    'one hundred twenty', '120', 'regulatory requirements'
                ],
                'timeframe_pattern': r'(?:one hundred twenty|120)\s*\(\s*120\s*\)\s*days?'
            },
            'Medicare Timely Filing': {
                'section_keywords': [
                    'submission and adjudication of medicare advantage claims',
                    'medicare advantage claims',
                    'medicare timely filing'
                ],
                'content_keywords': [
                    'medicare advantage', 'claims', 'submit', 'days', 'rendered',
                    'ninety', '90', 'provider manual'
                ],
                'timeframe_pattern': r'(?:ninety|90)\s*\(\s*90\s*\)\s*days?'
            },
            'No Steerage/SOC': {
                'section_keywords': [
                    'networks and provider panels',
                    'provider networks',
                    'network participation'
                ],
                'content_keywords': [
                    'networks', 'designated', 'participating provider',
                    'sole discretion', 'eligible to participate',
                    'credentialing requirements'
                ],
                'timeframe_pattern': None
            },
            'Medicaid Fee Schedule': {
                'section_keywords': [
                    'plan compensation schedule',
                    'specific reimbursement terms',
                    'medicaid reimbursement'
                ],
                'content_keywords': [
                    'medicaid rate', 'fee schedule', 'reimbursement',
                    'professional provider market master',
                    'one hundred percent', '100%'
                ],
                'timeframe_pattern': None
            },
            'Medicare Fee Schedule': {
                'section_keywords': [
                    'plan compensation schedule',
                    'specific reimbursement terms',
                    'medicare advantage reimbursement'
                ],
                'content_keywords': [
                    'medicare advantage rate', 'eligible charges',
                    'cost shares', 'lesser of', 'full compensation'
                ],
                'timeframe_pattern': None
            }
        }
    
    def extract_all_attributes(self, contract_text: str) -> Dict[str, str]:
        """Extract all 5 required attributes from contract text."""
        extracted_attributes = {}
        
        for attribute_name in self.attribute_patterns.keys():
            clause_text = self.extract_attribute(contract_text, attribute_name)
            extracted_attributes[attribute_name] = clause_text
            
            if clause_text:
                logger.info(f"Successfully extracted {attribute_name}")
            else:
                logger.warning(f"Could not extract {attribute_name}")
        
        return extracted_attributes
    
    def extract_attribute(self, contract_text: str, attribute_name: str) -> str:
        """Extract specific attribute clause from contract text."""
        if attribute_name not in self.attribute_patterns:
            logger.error(f"Unknown attribute: {attribute_name}")
            return ""
        
        pattern_config = self.attribute_patterns[attribute_name]
        
        # Method 1: Look for section headers first
        clause_text = self._extract_by_section_header(contract_text, pattern_config)
        if clause_text:
            return clause_text
        
        # Method 2: Look for content keywords
        clause_text = self._extract_by_content_keywords(contract_text, pattern_config)
        if clause_text:
            return clause_text
        
        # Method 3: Look for specific patterns (like timeframes)
        if pattern_config.get('timeframe_pattern'):
            clause_text = self._extract_by_pattern(contract_text, pattern_config)
            if clause_text:
                return clause_text
        
        logger.debug(f"No clause found for {attribute_name}")
        return ""
    
    def _extract_by_section_header(self, text: str, pattern_config: Dict) -> str:
        """Extract clause by finding section headers."""
        text_lower = text.lower()
        lines = text.split('\n')
        
        for section_keyword in pattern_config['section_keywords']:
            # Find section header
            for i, line in enumerate(lines):
                if section_keyword.lower() in line.lower():
                    # Extract section content (next 10-20 lines)
                    section_lines = lines[i:i+20]
                    section_text = '\n'.join(section_lines)
                    
                    # Verify it contains relevant content keywords
                    if self._contains_keywords(section_text, pattern_config['content_keywords']):
                        return self._clean_extracted_text(section_text)
        
        return ""
    
    def _extract_by_content_keywords(self, text: str, pattern_config: Dict) -> str:
        """Extract clause by finding content with relevant keywords."""
        lines = text.split('\n')
        content_keywords = pattern_config['content_keywords']
        
        # Find lines with multiple keywords
        best_match_lines = []
        best_score = 0
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            keyword_count = sum(1 for keyword in content_keywords if keyword.lower() in line_lower)
            
            if keyword_count >= 2:  # At least 2 keywords
                # Include context around this line
                start_idx = max(0, i - 3)
                end_idx = min(len(lines), i + 8)
                context_lines = lines[start_idx:end_idx]
                
                # Score based on total keyword matches in context
                context_text = '\n'.join(context_lines).lower()
                total_score = sum(1 for keyword in content_keywords if keyword.lower() in context_text)
                
                if total_score > best_score:
                    best_score = total_score
                    best_match_lines = context_lines
        
        if best_match_lines and best_score >= 3:  # At least 3 keywords total
            return self._clean_extracted_text('\n'.join(best_match_lines))
        
        return ""
    
    def _extract_by_pattern(self, text: str, pattern_config: Dict) -> str:
        """Extract clause by finding specific patterns (like timeframes)."""
        timeframe_pattern = pattern_config.get('timeframe_pattern')
        if not timeframe_pattern:
            return ""
        
        # Find pattern matches
        matches = re.finditer(timeframe_pattern, text, re.IGNORECASE)
        
        for match in matches:
            # Get context around the match
            start_pos = max(0, match.start() - 200)
            end_pos = min(len(text), match.end() + 300)
            context_text = text[start_pos:end_pos]
            
            # Verify it contains relevant keywords
            if self._contains_keywords(context_text, pattern_config['content_keywords']):
                return self._clean_extracted_text(context_text)
        
        return ""
    
    def _contains_keywords(self, text: str, keywords: List[str], min_count: int = 2) -> bool:
        """Check if text contains minimum number of keywords."""
        text_lower = text.lower()
        keyword_count = sum(1 for keyword in keywords if keyword.lower() in text_lower)
        return keyword_count >= min_count
    
    def _clean_extracted_text(self, text: str) -> str:
        """Clean and format extracted clause text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common contract artifacts
        text = re.sub(r'█+', '[REDACTED]', text)  # Replace redaction blocks
        text = re.sub(r'\[.*?\]', '[REDACTED]', text)  # Replace bracketed content
        
        # Clean up line breaks and spacing
        text = text.strip()
        
        # Limit length to reasonable clause size
        if len(text) > 1000:
            # Try to find sentence boundaries
            sentences = text.split('. ')
            if len(sentences) > 1:
                # Take first few sentences that fit in 800 chars
                result = ""
                for sentence in sentences:
                    if len(result + sentence) < 800:
                        result += sentence + ". "
                    else:
                        break
                text = result.strip()
            else:
                text = text[:800] + "..."
        
        return text
    
    def validate_extraction(self, extracted_attributes: Dict[str, str]) -> Dict[str, bool]:
        """Validate that extracted attributes contain expected content."""
        validation_results = {}
        
        for attr_name, clause_text in extracted_attributes.items():
            if not clause_text:
                validation_results[attr_name] = False
                continue
            
            pattern_config = self.attribute_patterns.get(attr_name, {})
            content_keywords = pattern_config.get('content_keywords', [])
            
            # Check if clause contains expected keywords
            has_keywords = self._contains_keywords(clause_text, content_keywords, min_count=1)
            validation_results[attr_name] = has_keywords
        
        return validation_results
