"""
Similarity matcher for comparing contract clauses with template clauses.
Uses multiple methods to calculate similarity scores.
"""

import re
import logging
from typing import Dict, Tuple
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

class SimilarityMatcher:
    """Compare contract clauses with template clauses using multiple similarity methods."""
    
    def __init__(self):
        self.similarity_threshold = 0.7
    
    def calculate_similarity(self, contract_clause: str, template_clause: str) -> Dict[str, float]:
        """Calculate multiple similarity scores between contract and template clauses."""
        if not contract_clause or not template_clause:
            return {
                'exact_match': 0.0,
                'sequence_similarity': 0.0,
                'keyword_similarity': 0.0,
                'semantic_similarity': 0.0,
                'overall_score': 0.0
            }
        
        # Clean both texts for comparison
        contract_clean = self._clean_for_comparison(contract_clause)
        template_clean = self._clean_for_comparison(template_clause)
        
        # Calculate different similarity metrics
        exact_match = self._exact_match_score(contract_clean, template_clean)
        sequence_sim = self._sequence_similarity(contract_clean, template_clean)
        keyword_sim = self._keyword_similarity(contract_clean, template_clean)
        semantic_sim = self._semantic_similarity(contract_clean, template_clean)
        
        # Calculate weighted overall score
        overall_score = (
            exact_match * 0.4 +
            sequence_sim * 0.25 +
            keyword_sim * 0.2 +
            semantic_sim * 0.15
        )
        
        return {
            'exact_match': exact_match,
            'sequence_similarity': sequence_sim,
            'keyword_similarity': keyword_sim,
            'semantic_similarity': semantic_sim,
            'overall_score': overall_score
        }
    
    def _clean_for_comparison(self, text: str) -> str:
        """Clean text for similarity comparison."""
        # Convert to lowercase
        text = text.lower()
        
        # Replace redacted content with placeholder
        text = re.sub(r'\[redacted\]|█+', 'PLACEHOLDER', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove punctuation for some comparisons
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Remove extra spaces
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _exact_match_score(self, text1: str, text2: str) -> float:
        """Calculate exact match score."""
        if text1 == text2:
            return 1.0
        
        # Check for exact match after removing placeholders and numbers
        text1_normalized = re.sub(r'\b\d+\b|placeholder', '', text1)
        text2_normalized = re.sub(r'\b\d+\b|placeholder', '', text2)
        
        if text1_normalized.strip() == text2_normalized.strip():
            return 0.95
        
        return 0.0
    
    def _sequence_similarity(self, text1: str, text2: str) -> float:
        """Calculate sequence similarity using difflib."""
        return SequenceMatcher(None, text1, text2).ratio()
    
    def _keyword_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity based on shared keywords."""
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        # Remove common stop words
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an'}
        words1 = words1 - stop_words
        words2 = words2 - stop_words
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using simple heuristics."""
        # This is a simplified semantic similarity
        # In a production system, you might use word embeddings or transformers
        
        # Define semantic equivalents for contract language
        semantic_pairs = [
            (['ninety', '90'], ['ninety', '90']),
            (['one hundred twenty', '120'], ['one hundred twenty', '120']),
            (['submit', 'submission'], ['submit', 'submission']),
            (['claims', 'claim'], ['claims', 'claim']),
            (['days', 'day'], ['days', 'day']),
            (['rendered', 'provided', 'furnished'], ['rendered', 'provided', 'furnished']),
            (['fee schedule', 'schedule'], ['fee schedule', 'schedule']),
            (['reimbursement', 'payment', 'compensation'], ['reimbursement', 'payment', 'compensation']),
            (['medicaid', 'medicare'], ['medicaid', 'medicare']),
            (['provider', 'physician', 'hospital'], ['provider', 'physician', 'hospital'])
        ]
        
        # Replace semantic equivalents
        text1_semantic = text1
        text2_semantic = text2
        
        for group1, group2 in semantic_pairs:
            for word in group1:
                text1_semantic = text1_semantic.replace(word, group1[0])
            for word in group2:
                text2_semantic = text2_semantic.replace(word, group2[0])
        
        # Calculate similarity on semantically normalized text
        return SequenceMatcher(None, text1_semantic, text2_semantic).ratio()
    
    def detect_value_substitution(self, contract_clause: str, template_clause: str) -> Tuple[bool, Dict]:
        """Detect if differences are just value substitutions (like percentages)."""
        # Common value substitution patterns
        value_patterns = [
            r'\b\d+%\b',  # Percentages
            r'\b(?:ninety|90|one hundred twenty|120)\s*(?:\(\s*\d+\s*\))?\s*days?\b',  # Days
            r'\$[\d,]+\.?\d*',  # Dollar amounts
            r'\b\d+\.\d+%\b',  # Decimal percentages
        ]
        
        substitutions = {}
        is_substitution = False
        
        for pattern in value_patterns:
            contract_values = re.findall(pattern, contract_clause, re.IGNORECASE)
            template_values = re.findall(pattern, template_clause, re.IGNORECASE)
            
            if contract_values and template_values and contract_values != template_values:
                substitutions[pattern] = {
                    'contract_values': contract_values,
                    'template_values': template_values
                }
                
                # Check if removing these values makes texts similar
                contract_no_values = re.sub(pattern, 'VALUE', contract_clause, flags=re.IGNORECASE)
                template_no_values = re.sub(pattern, 'VALUE', template_clause, flags=re.IGNORECASE)
                
                similarity = self._sequence_similarity(
                    self._clean_for_comparison(contract_no_values),
                    self._clean_for_comparison(template_no_values)
                )
                
                if similarity > 0.8:
                    is_substitution = True
        
        return is_substitution, substitutions
    
    def detect_structural_changes(self, contract_clause: str, template_clause: str) -> Dict:
        """Detect structural changes like additional conditions or carve-outs."""
        structural_indicators = {
            'additional_conditions': [
                'except', 'unless', 'provided that', 'however', 'but',
                'excluding', 'with the exception of', 'carve out'
            ],
            'different_methodology': [
                'instead of', 'rather than', 'in lieu of', 'alternative',
                'different', 'modified', 'adjusted'
            ],
            'additional_requirements': [
                'must also', 'additionally', 'furthermore', 'in addition',
                'shall also', 'required to', 'subject to'
            ]
        }
        
        changes = {}
        contract_lower = contract_clause.lower()
        template_lower = template_clause.lower()
        
        for change_type, indicators in structural_indicators.items():
            contract_has = any(indicator in contract_lower for indicator in indicators)
            template_has = any(indicator in template_lower for indicator in indicators)
            
            if contract_has and not template_has:
                changes[change_type] = {
                    'present_in_contract': True,
                    'present_in_template': False,
                    'indicators_found': [ind for ind in indicators if ind in contract_lower]
                }
            elif template_has and not contract_has:
                changes[change_type] = {
                    'present_in_contract': False,
                    'present_in_template': True,
                    'indicators_found': [ind for ind in indicators if ind in template_lower]
                }
        
        return changes
    
    def get_match_type(self, similarity_scores: Dict[str, float], 
                      is_value_substitution: bool, 
                      structural_changes: Dict) -> str:
        """Determine the type of match between contract and template."""
        overall_score = similarity_scores['overall_score']
        exact_match = similarity_scores['exact_match']
        
        if exact_match >= 0.95:
            return 'exact_match'
        elif is_value_substitution and overall_score > 0.8:
            return 'value_substitution'
        elif overall_score > 0.85:
            return 'semantic_similarity'
        elif structural_changes:
            return 'structural_difference'
        elif overall_score > 0.6:
            return 'partial_match'
        else:
            return 'no_match'
