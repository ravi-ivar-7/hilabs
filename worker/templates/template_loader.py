"""
Template loader for TN/WA standard contract templates.
Loads and parses standard templates for comparison with contract clauses.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Optional
from preprocessing.pdf_extractor import PDFExtractor
from preprocessing.text_cleaner import TextCleaner

logger = logging.getLogger(__name__)

class TemplateLoader:
    """Load and process TN/WA standard contract templates."""
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.text_cleaner = TextCleaner()
        self.templates = {}
        
        # Dynamic path resolution - find project root and templates directory
        current_path = Path(__file__).resolve()
        project_root = current_path
        
        # Navigate up to find the project root (contains data directory)
        while project_root.parent != project_root:
            if (project_root / 'data' / 'templates').exists():
                break
            project_root = project_root.parent
        
        templates_dir = project_root / 'data' / 'templates'
        self.cache_dir = templates_dir / 'cache'
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.template_paths = {
            'TN': templates_dir / 'TN_Standard_Template_Redacted.pdf',
            'WA': templates_dir / 'WA_Standard_Redacted.pdf'
        }
        
        # Cache file paths for extracted text
        self.cache_paths = {
            'TN': self.cache_dir / 'TN_extracted_text.txt',
            'WA': self.cache_dir / 'WA_extracted_text.txt'
        }
    
    def load_template(self, state: str) -> Optional[Dict]:
        """Load and parse template for specified state (TN/WA)."""
        if state in self.templates:
            return self.templates[state]
        
        template_path = self.template_paths.get(state)
        if not template_path or not template_path.exists():
            logger.error(f"Template not found for state {state}: {template_path}")
            return None
        
        try:
            # Check if cached text exists first
            cache_path = self.cache_paths.get(state)
            
            if cache_path and cache_path.exists():
                # Load from cache
                logger.info(f"Loading cached template text for state {state}")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cleaned_text = f.read()
                extracted_text = cleaned_text  # For raw_text field
            else:
                # Extract text from template PDF
                logger.info(f"Extracting template text for state {state} (first time)")
                with open(template_path, 'rb') as file:
                    pdf_content = file.read()
                
                # Extract text
                extraction_result = self.pdf_extractor.extract_text(pdf_content)
                if not extraction_result.get("success", False):
                    logger.error(f"Failed to extract text from template {state}: {extraction_result.get('error', 'Unknown error')}")
                    return None
                
                extracted_text = extraction_result.get("text", "")
                if not extracted_text:
                    logger.error(f"No text extracted from template {state}")
                    return None
                
                # Clean text
                cleaning_result = self.text_cleaner.clean_text(extracted_text)
                cleaned_text = cleaning_result.get("cleaned_text", extracted_text)
                
                # Cache the cleaned text for future use
                if cache_path:
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_text)
                    logger.info(f"Cached template text for state {state} at {cache_path}")
            
            # Parse template attributes
            template_data = {
                'state': state,
                'raw_text': extracted_text,
                'cleaned_text': cleaned_text,
                'attributes': self._parse_template_attributes(cleaned_text)
            }
            
            self.templates[state] = template_data
            logger.info(f"Successfully loaded template for state {state}")
            return template_data
            
        except Exception as e:
            logger.error(f"Error loading template for state {state}: {str(e)}")
            return None
    
    def _parse_template_attributes(self, text: str) -> Dict[str, str]:
        """Parse the 5 required attributes from template text."""
        attributes = {}
        
        # Define attribute patterns based on Attribute Dictionary
        attribute_patterns = {
            'Medicaid Timely Filing': [
                'medicaid claims', 'submission and adjudication of medicaid',
                '120 days', 'one hundred twenty'
            ],
            'Medicare Timely Filing': [
                'medicare advantage', 'submission and adjudication of medicare',
                '90 days', 'ninety'
            ],
            'No Steerage/SOC': [
                'networks and provider panels', 'designated networks',
                'participating provider', 'sole discretion'
            ],
            'Medicaid Fee Schedule': [
                'medicaid rate', 'medicaid fee schedule',
                'reimbursement terms', 'professional provider market master'
            ],
            'Medicare Fee Schedule': [
                'medicare advantage rate', 'eligible charges',
                'cost shares', 'medicare advantage network'
            ]
        }
        
        text_lower = text.lower()
        
        for attr_name, keywords in attribute_patterns.items():
            # Find sections containing these keywords
            clause_text = self._extract_clause_by_keywords(text, keywords)
            if clause_text:
                attributes[attr_name] = clause_text
                logger.debug(f"Found template clause for {attr_name}")
            else:
                logger.warning(f"Could not find template clause for {attr_name}")
                attributes[attr_name] = ""
        
        return attributes
    
    def _extract_clause_by_keywords(self, text: str, keywords: list) -> str:
        """Extract clause text containing specified keywords."""
        lines = text.split('\n')
        text_lower = text.lower()
        
        # Find lines containing keywords
        matching_lines = []
        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in keywords):
                # Include context around matching line
                start_idx = max(0, i - 2)
                end_idx = min(len(lines), i + 5)
                context_lines = lines[start_idx:end_idx]
                matching_lines.extend(context_lines)
                break
        
        if matching_lines:
            return '\n'.join(matching_lines).strip()
        return ""
    
    def get_template_attribute(self, state: str, attribute: str) -> str:
        """Get specific attribute text from template."""
        template = self.load_template(state)
        if not template:
            return ""
        
        return template.get('attributes', {}).get(attribute, "")
    
    def get_all_templates(self) -> Dict[str, Dict]:
        """Load all available templates."""
        templates = {}
        for state in ['TN', 'WA']:
            template = self.load_template(state)
            if template:
                templates[state] = template
        return templates
