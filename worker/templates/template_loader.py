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

logger = logging.getLogger(__name__)

TARGET_ATTRIBUTES = [
    "Medicaid Timely Filing",
    "Medicare Timely Filing", 
    "No Steerage/SOC",
    "Medicaid Fee Schedule",
    "Medicare Fee Schedule"
]

EXCEPTION_TOKENS = [
    'except', 'unless', 'provided that',
    'subject to', 'however,', 'save that',
    'notwithstanding', 'only if'
]

PLACEHOLDER_MAP = {
    # Percentages (XX%, 100%, 95% etc.)
    r"\[\(?\s*XX\s*%\s*\)?\]": "<PCT>",                # generic percentage placeholder
    r"\b\d{1,3}\s*%\b": "<PCT>",                       # numeric percentages like 100%, 95%
    r"\b(one\s*hundred|ninety[-\s]*five|fifty)\s*percent\b": "<PCT>",

    # Compensation / Fee references
    r"\b(Fee\s+Schedule|Compensation\s+Schedule|Plan\s+Compensation\s+Schedule|WCS|PCS)\b": "<FEE_SCHEDULE>",
    r"\b(Rate|Eligible\s+Charge[s]?)\b": "<RATE>",

    # Parties / Organization
    r"\b(Plan|Company|Network|Agency|Affiliate|Other\s+Payors?)\b": "<ORG>",
    r"\b(Provider|Participating\s+Provider)\b": "<PROVIDER>",

    # Members
    r"\b(Member|Enrollee|Subscriber|Insured|Beneficiary|Covered\s+(Person|Individual)|Dependent)\b": "<MEMBER>",

    # Programs
    r"\b(Government\s+Program|Medicare|Medicaid|CMS|HCA)\b": "<GOV_PROGRAM>",

    # Documents
    r"\b(Participation\s+Attachment[s]?)\b": "<ATTACHMENT>",
    r"\b(provider\s+manual\(s\))\b": "<PROVIDER_MANUAL>",
    r"\b(Health\s+Benefit\s+Plan)\b": "<PLAN_DOC>",

    # Payments
    r"\b(Cost\s*Share[s]?|copayment[s]?|coinsurance|deductible[s]?)\b": "<COST_SHARE>",
    r"\b(Claim[s]?)\b": "<CLAIM>",

    # Legal placeholders
    r"\b(Regulatory\s+Requirements?)\b": "<REG_REQ>",
    r"\b(Effective\s+Date|MM/DD/YYYY)\b": "<DATE>",
    r"\[\s*_{2,}\s*\]": "<BLANK>",   # underscores for blanks like [_________]

    # Misc
    r"\b(Health\s+Services?|Covered\s+Services?)\b": "<SERVICE>",
    r"\b(Medically\s+Necessary|Medical\s+Necessity)\b": "<MEDICAL_NECESSITY>",
}

# Extracted from actual TN template PDF 
TN_TEMPLATE_CLAUSES = {
    "Medicaid Timely Filing": "Provider shall submit Claims to using appropriate and current Coded Service Identifier(s), within one hundred twenty (120) days from the date the Health Services are rendered or may refuse payment. If is the secondary payor, the one hundred twenty (120) day period will not begin until Provider receives notification of primary payor's responsibility",
    "Medicare Timely Filing": "Provider shall submit Claims to using appropriate and current Coded Service Identifier(s), within one hundred twenty (120) days from the date the Health Services are rendered or may refuse payment. If is the secondary payor, the one hundred twenty (120) day period will not begin until Provider receives notification of primary payor's responsibility. 3.1.1 In situations of enrollment in with a retroactive eligibility date, the time frames for filing a claim shall begin on the date that receives notification from of the Medicaid Member's eligibility/enrollment.",
    "No Steerage/SOC": "Provider shall be eligible to participate only in those Networks designated on the Provider Networks Attachment",
    "Medicaid Fee Schedule": "one hundred percent (100%) of Eligible Charges for Covered Services, or the total reimbursement amount that Provider and have agreed upon as set forth in the Compensation Schedule. The Rate includes applicable Cost Shares, and shall represent payment in full to Provider for Covered Services.",
    "Medicare Fee Schedule": "Medicare Advantage Network means Network of Providers that provides MA Covered Services to MA Members. Related Entity(ies) means any entity that is related to by common ownership or control and performs some of management functions under contract or delegation."
}

# Extracted from actual WA template PDF 
WA_TEMPLATE_CLAUSES = {
    "Medicaid Timely Filing": "Unless otherwise instructed, or required by Regulatory Requirements, Provider shall submit Claims for Medicaid Claims.",
    "Medicare Timely Filing": "Provider shall submit Claims to Plan, using appropriate and current Coded Service Identifier(s), within three hundred sixty-five (365) days from the date the Health Services are rendered or Plan may refuse payment. If Plan is the secondary payor, the three hundred sixty-five (365) day period will not begin until Provider receives notification of primary payor's responsibility.",
    "No Steerage/SOC": "Provider shall be eligible to participate only in those Networks designated on the Provider Networks Attachment of this Agreement",
    "Medicaid Fee Schedule": "one hundred percent (100%) of Eligible Charges for Covered Services, or the total reimbursement amount that Provider and have agreed upon as set forth in the Compensation Schedule. The Rate includes applicable Cost Shares, and shall represent payment in full to Provider for Covered Services.",
    "Medicare Fee Schedule": "As a participant in Plan's Medicare Advantage Network, Provider will render MA Covered Services to MA Members enrolled in Plan's Medicare Advantage Program in accordance with the terms and conditions of the Agreement."
}

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
    
    