"""
spaCy-based healthcare contract clause classifier.
Implements multi-step classification using spaCy NLP, similarity matching, and analysis.
"""

import logging
import re
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
import spacy
from rapidfuzz import fuzz
from sentence_transformers import SentenceTransformer
from word2number import w2n

from templates.template_loader import TemplateClause, TemplateLoader

logger = logging.getLogger(__name__)

@dataclass
class StepResult:
    """Result of a single classification step."""
    step_name: str
    passed: bool
    score: Optional[float]
    reason: str

@dataclass
class ClassificationDecision:
    """Final classification decision for a clause."""
    clause_id: int
    attribute: str
    template_used: str
    label: str
    score: float
    rule: str
    text: str
    steps: List[StepResult]

class SpacyClassifier:
    """spaCy-based contract clause classifier using multi-step methodology."""
    
    def __init__(self, templates: List[TemplateClause], target_attributes: List[str]):
        """Initialize classifier with templates and configuration.
        
        Args:
            templates: List of template clauses for comparison
            target_attributes: List of target attributes to detect
        """
        self.templates = templates
        self.target_attributes = target_attributes
        
        self.fuzzy_threshold = 85
        self.sbert_threshold = 0.75
        self.sbert_ambig_low = 0.60
        self.sbert_ambig_high = 0.75
        
        # Initialize spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model 'en_core_web_sm' not found. Some features may be limited.")
            self.nlp = None
        
        # Initialize SBERT model
        try:
            self.sbert_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            logger.info("SBERT model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load SBERT model: {e}")
            self.sbert_model = None
        
        self.exception_tokens = TemplateLoader.get_exception_tokens()
        self.placeholder_map = TemplateLoader.get_placeholder_map()
        
        self.attribute_patterns = {
            "Medicaid Timely Filing": [
                r"medicaid.*claim.*\d+.*day", r"medicaid.*filing", r"medicaid.*submission",
                r"120.*day.*medicaid", r"medicaid.*eligibility.*date"
            ],
            "Medicare Timely Filing": [
                r"medicare.*claim.*\d+.*day", r"medicare.*filing", r"medicare.*submission",
                r"365.*day.*medicare", r"medicare.*secondary.*payor"
            ],
            "No Steerage/SOC": [
                r"network.*participation", r"provider.*network", r"steerage",
                r"standard.*care", r"network.*designated", r"participation.*attachment"
            ],
            "Medicaid Fee Schedule": [
                r"medicaid.*fee.*schedule", r"medicaid.*\d+.*percent", r"medicaid.*eligible.*charge",
                r"medicaid.*compensation", r"medicaid.*rate"
            ],
            "Medicare Fee Schedule": [
                r"medicare.*advantage", r"medicare.*fee.*schedule", r"medicare.*eligible.*charge",
                r"ma.*covered.*service", r"medicare.*rate"
            ]
        }
    
    def classify_clauses(self, clauses: List[Dict[str, Any]]) -> List[ClassificationDecision]:
        """Classify all clauses in the contract.
        
        Args:
            clauses: List of clause dictionaries
            
        Returns:
            List of classification decisions
        """
        decisions = []
        
        for clause in clauses:
            detected_attributes = self._detect_attributes(clause["text"])
            
            if not detected_attributes:
                decisions.append(ClassificationDecision(
                    clause_id=clause["clause_id"],
                    attribute="",
                    template_used="",
                    label="Skip",
                    score=0.0,
                    rule="no_target_attribute",
                    text=clause["text"],
                    steps=[]
                ))
                continue
            
            for attribute in detected_attributes:
                best_decision = self._classify_clause_for_attribute(clause, attribute)
                decisions.append(best_decision)
        
        return decisions
    
    def _detect_attributes(self, text: str) -> List[str]:
        """Detect which attributes are relevant for a clause.
        
        Args:
            text: Clause text
            
        Returns:
            List of detected attribute names
        """
        detected = []
        text_lower = text.lower()
        
        for attribute, patterns in self.attribute_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    detected.append(attribute)
                    break
        
        return detected
    
    def _classify_clause_for_attribute(self, clause: Dict[str, Any], attribute: str) -> ClassificationDecision:
        """Classify a clause against templates for a specific attribute.
        
        Args:
            clause: Clause dictionary
            attribute: Target attribute name
            
        Returns:
            Classification decision
        """
        clause_text = clause["text"]
        clause_norm = clause.get("norm_text", clause_text.lower())
        
        # Find relevant templates for this attribute
        relevant_templates = [t for t in self.templates if t.attribute == attribute]
        
        if not relevant_templates:
            return ClassificationDecision(
                clause_id=clause["clause_id"],
                attribute=attribute,
                template_used="",
                label="Non-Standard",
                score=0.0,
                rule="no_template_found",
                text=clause_text,
                steps=[]
            )
        
        best_result = None
        best_score = -1.0
        
        for template in relevant_templates:
            result = self._classify_against_template(clause_text, clause_norm, template)
            
            if result[1] > best_score:  # result[1] is the score
                best_score = result[1]
                best_result = result
        
        if best_result:
            label, score, rule, steps = best_result
            template_name = relevant_templates[0].name  # Use first template name
            
            return ClassificationDecision(
                clause_id=clause["clause_id"],
                attribute=attribute,
                template_used=template_name,
                label=label,
                score=score,
                rule=rule,
                text=clause_text,
                steps=steps
            )
        
        return ClassificationDecision(
            clause_id=clause["clause_id"],
            attribute=attribute,
            template_used="",
            label="Non-Standard",
            score=0.0,
            rule="classification_failed",
            text=clause_text,
            steps=[]
        )
    
    def _classify_against_template(self, clause_text: str, clause_norm: str, template: TemplateClause) -> Tuple[str, float, str, List[StepResult]]:
        """Classify clause against a specific template using multi-step approach.
        
        Args:
            clause_text: Original clause text
            clause_norm: Normalized clause text
            template: Template clause to compare against
            
        Returns:
            Tuple of (label, score, rule, steps)
        """
        steps = []
        
        # Step A: Exception token detection
        has_exception = self._contains_exception_tokens(clause_text, template.has_exception_tokens)
        steps.append(StepResult("exception_check", has_exception, None, "Detected conditional/exception tokens"))
        
        if has_exception:
            return "Non-Standard", 0.90, "new_condition", steps
        
        # Step B: Exact normalized match
        exact_match = (clause_norm == template.norm_text)
        steps.append(StepResult("exact_normalized_match", exact_match, None, "Exact match after normalization"))
        
        if exact_match:
            return "Standard", 0.99, "exact_norm", steps
        
        # Step C: Placeholder substitution
        placeholder_match = self._check_placeholder_substitution(clause_text, template.raw_text)
        steps.append(StepResult("placeholder_substitution", placeholder_match, None, "Placeholder/value substitutions align"))
        
        if placeholder_match:
            return "Standard", 0.95, "placeholder_subst", steps
        
        # Step D: Fuzzy lexical similarity
        fuzzy_score = fuzz.ratio(clause_norm, template.norm_text)
        fuzzy_pass = fuzzy_score >= self.fuzzy_threshold
        steps.append(StepResult("fuzzy_lexical", fuzzy_pass, float(fuzzy_score)/100.0, f"RapidFuzz ratio={fuzzy_score}"))
        
        if fuzzy_pass:
            return "Standard", 0.90, "lexical_high", steps
        
        # Step E: Semantic similarity (SBERT)
        if self.sbert_model:
            sbert_score = self._compute_sbert_similarity(clause_text, template.raw_text)
            sbert_high = sbert_score >= self.sbert_threshold
            steps.append(StepResult("semantic_sbert", sbert_high, sbert_score, f"SBERT cosine={sbert_score:.3f}"))
            
            if sbert_high:
                return "Standard", 0.85, "semantic_high", steps
            
            # Check ambiguous range
            if self.sbert_ambig_low <= sbert_score < self.sbert_ambig_high:
                steps.append(StepResult("semantic_ambiguous", True, sbert_score, "SBERT in ambiguous range"))
                return "Ambiguous", sbert_score, "semantic_ambiguous", steps
        
        # Step F: Different methodology detection
        has_diff_methodology = self._detect_methodology_reference(clause_text)
        steps.append(StepResult("different_methodology", has_diff_methodology, None, "References alternate payment methodology"))
        
        if has_diff_methodology:
            return "Non-Standard", 0.85, "different_methodology", steps
        
        # Default: Non-Standard
        final_score = fuzzy_score / 100.0 if fuzzy_score > 0 else 0.0
        steps.append(StepResult("default_nonstandard", True, final_score, "Low similarity, no rules satisfied"))
        
        return "Non-Standard", final_score, "low_similarity", steps
    
    def _contains_exception_tokens(self, text: str, template_has_exception: bool) -> bool:
        """Check if clause contains exception tokens when template doesn't."""
        if template_has_exception:
            return False  # Template already has exceptions, so clause exceptions are OK
        
        text_lower = text.lower()
        return any(token in text_lower for token in self.exception_tokens)
    
    def _check_placeholder_substitution(self, clause_text: str, template_text: str) -> bool:
        """Check if differences are due to placeholder substitutions."""
        try:
            clause_normalized = clause_text
            template_normalized = template_text
            
            for pattern, replacement in self.placeholder_map.items():
                clause_normalized = re.sub(pattern, replacement, clause_normalized, flags=re.IGNORECASE)
                template_normalized = re.sub(pattern, replacement, template_normalized, flags=re.IGNORECASE)
            
            # Check similarity after placeholder normalization
            similarity = fuzz.ratio(clause_normalized.lower(), template_normalized.lower())
            return similarity >= 90
            
        except Exception as e:
            logger.warning(f"Placeholder substitution check failed: {e}")
            return False
    
    def _compute_sbert_similarity(self, text1: str, text2: str) -> float:
        """Compute semantic similarity using SBERT."""
        try:
            embeddings = self.sbert_model.encode([text1, text2])
            # Compute cosine similarity
            import numpy as np
            similarity = np.dot(embeddings[0], embeddings[1]) / (
                np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
            )
            return float(similarity)
        except Exception as e:
            logger.warning(f"SBERT similarity computation failed: {e}")
            return 0.0
    
    def _detect_methodology_reference(self, text: str) -> bool:
        """Detect references to different payment methodologies."""
        text_lower = text.lower()
        methodology_patterns = [
            r"medicare.*rate", r"billed.*charge", r"usual.*customary",
            r"fair.*market", r"negotiated.*rate", r"contracted.*rate"
        ]
        
        return any(re.search(pattern, text_lower) for pattern in methodology_patterns)
