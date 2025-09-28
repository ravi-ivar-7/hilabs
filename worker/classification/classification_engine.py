"""
Classification engine for determining Standard vs Non-Standard clauses.
Uses similarity scores and business rules to classify contract clauses.
"""

import logging
from typing import Dict, Tuple
from .similarity_matcher import SimilarityMatcher

logger = logging.getLogger(__name__)

class ClassificationEngine:
    """Classify contract clauses as Standard or Non-Standard."""
    
    def __init__(self):
        self.similarity_matcher = SimilarityMatcher()
        
        # Classification thresholds
        self.thresholds = {
            'exact_match': 0.95,
            'value_substitution': 0.80,
            'semantic_similarity': 0.85,
            'partial_match': 0.60
        }
    
    def classify_clause(self, contract_clause: str, template_clause: str, 
                       attribute_name: str) -> Dict:
        """Classify a single clause as Standard or Non-Standard."""
        if not contract_clause or not template_clause:
            return {
                'classification': 'Non-Standard',
                'confidence_score': 0,
                'similarity_score': 0.0,
                'match_type': 'no_match',
                'reason': 'Missing clause text'
            }
        
        # Calculate similarity scores
        similarity_scores = self.similarity_matcher.calculate_similarity(
            contract_clause, template_clause
        )
        
        # Detect value substitutions
        is_value_substitution, substitutions = self.similarity_matcher.detect_value_substitution(
            contract_clause, template_clause
        )
        
        # Detect structural changes
        structural_changes = self.similarity_matcher.detect_structural_changes(
            contract_clause, template_clause
        )
        
        # Determine match type
        match_type = self.similarity_matcher.get_match_type(
            similarity_scores, is_value_substitution, structural_changes
        )
        
        # Apply classification logic
        classification, confidence, reason = self._apply_classification_rules(
            similarity_scores, match_type, is_value_substitution, 
            structural_changes, attribute_name
        )
        
        return {
            'classification': classification,
            'confidence_score': confidence,
            'similarity_score': similarity_scores['overall_score'],
            'match_type': match_type,
            'reason': reason,
            'similarity_details': similarity_scores,
            'value_substitutions': substitutions if is_value_substitution else {},
            'structural_changes': structural_changes
        }
    
    def _apply_classification_rules(self, similarity_scores: Dict[str, float], 
                                  match_type: str, is_value_substitution: bool,
                                  structural_changes: Dict, attribute_name: str) -> Tuple[str, int, str]:
        """Apply business rules to determine classification."""
        overall_score = similarity_scores['overall_score']
        
        # Rule 1: Exact Match -> Standard
        if match_type == 'exact_match':
            return 'Standard', 100, 'Exact match with template'
        
        # Rule 2: Value Substitution -> Standard (if similarity is high)
        if match_type == 'value_substitution' and overall_score > self.thresholds['value_substitution']:
            confidence = min(95, int(overall_score * 100))
            return 'Standard', confidence, 'Acceptable value substitution'
        
        # Rule 3: Semantic Similarity -> Standard (if high enough)
        if match_type == 'semantic_similarity' and overall_score > self.thresholds['semantic_similarity']:
            confidence = min(90, int(overall_score * 100))
            return 'Standard', confidence, 'Semantically equivalent language'
        
        # Rule 4: Structural Changes -> Non-Standard
        if structural_changes:
            confidence = max(70, int((1 - overall_score) * 100))
            change_types = list(structural_changes.keys())
            return 'Non-Standard', confidence, f'Structural changes detected: {", ".join(change_types)}'
        
        # Rule 5: Attribute-specific rules
        classification, confidence, reason = self._apply_attribute_specific_rules(
            attribute_name, similarity_scores, match_type
        )
        if classification:
            return classification, confidence, reason
        
        # Rule 6: Partial Match -> Depends on score
        if overall_score > self.thresholds['partial_match']:
            confidence = int(overall_score * 80)  # Lower confidence for partial matches
            return 'Standard', confidence, 'Partial match - acceptable similarity'
        
        # Rule 7: Default -> Non-Standard
        confidence = max(60, int((1 - overall_score) * 100))
        return 'Non-Standard', confidence, 'Insufficient similarity to template'
    
    def _apply_attribute_specific_rules(self, attribute_name: str, 
                                      similarity_scores: Dict[str, float], 
                                      match_type: str) -> Tuple[str, int, str]:
        """Apply attribute-specific classification rules."""
        overall_score = similarity_scores['overall_score']
        
        # Timely Filing attributes - strict on timeframes
        if 'Timely Filing' in attribute_name:
            if match_type == 'value_substitution':
                # Check if timeframe substitution is acceptable
                if 'Medicaid' in attribute_name and overall_score > 0.75:
                    return 'Standard', 85, 'Acceptable Medicaid timeframe variation'
                elif 'Medicare' in attribute_name and overall_score > 0.75:
                    return 'Standard', 85, 'Acceptable Medicare timeframe variation'
            
            # Strict threshold for timely filing
            if overall_score < 0.70:
                return 'Non-Standard', 75, 'Timely filing requirements differ significantly'
        
        # Fee Schedule attributes - flexible on percentages
        elif 'Fee Schedule' in attribute_name:
            if match_type == 'value_substitution' and overall_score > 0.70:
                confidence = min(90, int(overall_score * 100))
                return 'Standard', confidence, 'Acceptable fee schedule percentage variation'
            
            # Different methodology check
            if overall_score < 0.50:
                return 'Non-Standard', 80, 'Different reimbursement methodology'
        
        # No Steerage/SOC - focus on network language
        elif 'No Steerage' in attribute_name or 'SOC' in attribute_name:
            keyword_sim = similarity_scores.get('keyword_similarity', 0)
            if keyword_sim > 0.60 and overall_score > 0.65:
                confidence = int((keyword_sim + overall_score) / 2 * 100)
                return 'Standard', confidence, 'Network participation language matches'
        
        return None, 0, ""
    
    def classify_all_attributes(self, contract_attributes: Dict[str, str], 
                              template_attributes: Dict[str, str]) -> Dict[str, Dict]:
        """Classify all contract attributes against template attributes."""
        classifications = {}
        
        for attr_name in contract_attributes.keys():
            contract_clause = contract_attributes.get(attr_name, "")
            template_clause = template_attributes.get(attr_name, "")
            
            classification_result = self.classify_clause(
                contract_clause, template_clause, attr_name
            )
            
            classifications[attr_name] = classification_result
            
            logger.info(f"Classified {attr_name}: {classification_result['classification']} "
                       f"(confidence: {classification_result['confidence_score']}%)")
        
        return classifications
    
    def generate_summary(self, classifications: Dict[str, Dict]) -> Dict:
        """Generate summary statistics for all classifications."""
        total_clauses = len(classifications)
        standard_count = sum(1 for c in classifications.values() 
                           if c['classification'] == 'Standard')
        non_standard_count = total_clauses - standard_count
        
        # Calculate average confidence
        total_confidence = sum(c['confidence_score'] for c in classifications.values())
        avg_confidence = total_confidence / total_clauses if total_clauses > 0 else 0
        
        # Calculate overall compliance percentage
        compliance_percentage = (standard_count / total_clauses * 100) if total_clauses > 0 else 0
        
        # Identify high-risk clauses (Non-Standard with high confidence)
        high_risk_clauses = [
            attr_name for attr_name, result in classifications.items()
            if result['classification'] == 'Non-Standard' and result['confidence_score'] > 75
        ]
        
        return {
            'total_clauses': total_clauses,
            'standard_clauses': standard_count,
            'non_standard_clauses': non_standard_count,
            'compliance_percentage': round(compliance_percentage, 1),
            'average_confidence': round(avg_confidence, 1),
            'high_risk_clauses': high_risk_clauses,
            'classification_breakdown': {
                attr_name: {
                    'classification': result['classification'],
                    'confidence': result['confidence_score'],
                    'match_type': result['match_type']
                }
                for attr_name, result in classifications.items()
            }
        }
