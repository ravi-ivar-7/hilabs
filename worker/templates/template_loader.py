"""
Template loader for TN/WA standard contract templates.
Loads and parses standard templates for comparison with contract clauses.
Uses pre-analyzed templates, attributes, and constants for optimal performance.
"""

import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

from classification_parameters import (
    TARGET_ATTRIBUTES, EXCEPTION_TOKENS, PLACEHOLDER_MAP, 
    TN_TEMPLATE_CLAUSES, WA_TEMPLATE_CLAUSES
)

logger = logging.getLogger(__name__)

@dataclass
class TemplateClause:
    """Represents a template clause with metadata."""
    name: str
    attribute: str
    raw_text: str
    norm_text: str
    has_exception_tokens: bool
    state: str = ""

class TemplateLoader:
    """Load and process TN/WA standard contract templates using hardcoded clauses for optimal performance."""
    
    def __init__(self, state: str = None):
        """Initialize template loader for specific state or both states.
        
        Args:
            state: 'TN', 'WA', or None for both states
        """
        self.state = state
        self.templates = {}
        
        self._load_optimized_templates()
        
        logger.info(f"TemplateLoader initialized for state: {state or 'ALL'}")
    
    def _load_optimized_templates(self):
        """Load pre-analyzed template clauses."""
        if not self.state or self.state == 'TN':
            self.templates['TN'] = TN_TEMPLATE_CLAUSES
            
        if not self.state or self.state == 'WA':
            self.templates['WA'] = WA_TEMPLATE_CLAUSES
            
        logger.info(f"Loaded templates for states: {list(self.templates.keys())}")
    
    def load_template(self, state: str = None) -> Dict:
        """Load template clauses for specified state or all states.
        
        Args:
            state: 'TN', 'WA', or None for all states
            
        Returns:
            Dictionary of template clauses by attribute
        """
        if state:
            if state in self.templates:
                return self.templates[state]
            else:
                logger.error(f"Template not found for state: {state}")
                return {}
        else:
            return self.templates
        
    
    def get_template_clauses(self, state: str) -> List[TemplateClause]:
        """Get TemplateClause objects for a specific state.
        
        Args:
            state: 'TN' or 'WA'
            
        Returns:
            List of TemplateClause objects
        """
        if state not in self.templates:
            logger.error(f"No templates found for state: {state}")
            return []
            
        template_clauses = []
        clauses_dict = self.templates[state]
        
        for attribute, clause_text in clauses_dict.items():
            norm_text = self._normalize_text(clause_text)
            has_exception = self._contains_exception_tokens(clause_text)
            
            template_clause = TemplateClause(
                name=f"{state}_{attribute.replace(' ', '_')}",
                attribute=attribute,
                raw_text=clause_text,
                norm_text=norm_text,
                has_exception_tokens=has_exception,
                state=state
            )
            template_clauses.append(template_clause)
            
        return template_clauses
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching."""
        return text.lower().strip()
    
    def _contains_exception_tokens(self, text: str) -> bool:
        """Check if text contains exception tokens."""
        text_lower = text.lower()
        return any(token in text_lower for token in EXCEPTION_TOKENS)
    
    @classmethod
    def get_target_attributes(cls) -> List[str]:
        """Get the list of target attributes."""
        return TARGET_ATTRIBUTES.copy()
    
    @classmethod
    def get_exception_tokens(cls) -> List[str]:
        """Get the list of exception tokens."""
        return EXCEPTION_TOKENS.copy()
    
    @classmethod
    def get_placeholder_map(cls) -> Dict[str, str]:
        """Get the placeholder mapping dictionary."""
        return PLACEHOLDER_MAP.copy()
    
    