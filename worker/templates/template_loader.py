"""
Template loader for TN/WA standard contract templates.
Loads and parses standard templates for comparison with contract clauses.
"""

import os
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional
from preprocessing.pdf_extractor import PDFExtractor
from preprocessing.text_cleaner import TextCleaner

logger = logging.getLogger(__name__)

class TemplateLoader:
    """Load and process TN/WA standard contract templates."""
    
    def __init__(self):
        self.pdf_extractor = PDFExtractor()
        self.text_cleaner = TextCleaner()
        self.templates = {}
        
        current_path = Path(__file__).resolve()
        project_root = current_path
        
        while project_root.parent != project_root:
            if (project_root / 'data' / 'templates').exists():
                break
            project_root = project_root.parent
        
        templates_dir = project_root / 'data' / 'templates'
        self.cache_dir = templates_dir / 'cache'
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.template_paths = {
            'TN': templates_dir / 'TN_Standard_Template_Redacted.pdf',
            'WA': templates_dir / 'WA_Standard_Template_Redacted.pdf'
        }
        
        self.cache_paths = {
            'TN': self.cache_dir / 'TN_Standard_Template_Redacted_extracted_text.txt',
            'WA': self.cache_dir / 'WA_Standard_Template_Redacted_extracted_text.txt'
        }
        
        self.attribute_cache_paths = {
            'TN': self.cache_dir / 'TN_Standard_Template_Redacted_attributes.json',
            'WA': self.cache_dir / 'WA_Standard_Template_Redacted_attributes.json'
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
                logger.info(f"Loading cached template text for state {state}")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cleaned_text = f.read()
                extracted_text = cleaned_text  
            else:
                logger.info(f"Extracting template text for state {state} (first time)")
                with open(template_path, 'rb') as file:
                    pdf_content = file.read()
                
                extraction_result = self.pdf_extractor.extract_text(pdf_content)
                if not extraction_result.get("success", False):
                    logger.error(f"Failed to extract text from template {state}: {extraction_result.get('error', 'Unknown error')}")
                    return None
                
                extracted_text = extraction_result.get("text", "")
                if not extracted_text:
                    logger.error(f"No text extracted from template {state}")
                    return None
                
                cleaning_result = self.text_cleaner.clean_text(extracted_text)
                cleaned_text = cleaning_result.get("cleaned_text", extracted_text)
                
                if cache_path:
                    with open(cache_path, 'w', encoding='utf-8') as f:
                        f.write(cleaned_text)
                    logger.info(f"Cached template text for state {state} at {cache_path}")
            
            # Check if cached attributes exist
            attribute_cache_path = self.attribute_cache_paths.get(state)
            attributes = {}
            
            if attribute_cache_path and attribute_cache_path.exists():
                logger.info(f"Loading cached attributes for state {state}")
                try:
                    with open(attribute_cache_path, 'r', encoding='utf-8') as f:
                        attributes = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load cached attributes for {state}: {e}")
                    attributes = self._parse_template_attributes(cleaned_text, state)
            else:
                logger.info(f"Parsing attributes for state {state} (first time)")
                attributes = self._parse_template_attributes(cleaned_text, state)
                
                # Cache the parsed attributes
                if attribute_cache_path:
                    try:
                        with open(attribute_cache_path, 'w', encoding='utf-8') as f:
                            json.dump(attributes, f, indent=2, ensure_ascii=False)
                        logger.info(f"Cached attributes for state {state} at {attribute_cache_path}")
                    except Exception as e:
                        logger.warning(f"Failed to cache attributes for {state}: {e}")
            
            template_data = {
                'state': state,
                'raw_text': extracted_text,
                'cleaned_text': cleaned_text,
                'attributes': attributes
            }
            
            self.templates[state] = template_data
            logger.info(f"Successfully loaded template for state {state}")
            return template_data
            
        except Exception as e:
            logger.error(f"Error loading template for state {state}: {str(e)}")
            return None
    
    def _parse_template_attributes(self, text: str, state: str) -> Dict[str, str]:
        """Parse the 5 required attributes from template text using direct extraction."""
        attributes = {}
        
        # Extract specific sections based on known positions in the contract
        if state == 'TN':
            # Extract MEDICAID Fee Schedule section
            medicaid_start = text.find('MEDICAID Fee Schedule:')
            if medicaid_start != -1:
                medicaid_end = text.find('Provider acknowledges that', medicaid_start)
                if medicaid_end == -1:
                    medicaid_end = medicaid_start + 500
                attributes['Medicaid Fee Schedule'] = text[medicaid_start:medicaid_end].strip()
            
            # Extract Medicare Advantage reimbursement section
            medicare_start = text.find('Medicare Advantage reimbursement terms')
            if medicare_start != -1:
                medicare_end = text.find('shall not compensate Provider', medicare_start)
                if medicare_end == -1:
                    medicare_end = medicare_start + 400
                attributes['Medicare Fee Schedule'] = text[medicare_start:medicare_end].strip()
            
            # Extract Tennessee Medicaid Rate section
            tn_medicaid_start = text.find('Tennessee Medicaid Rate(s)/Fee Schedule(s)/Methodologies')
            if tn_medicaid_start != -1:
                tn_medicaid_end = tn_medicaid_start + 200
                attributes['Medicaid Timely Filing'] = text[tn_medicaid_start:tn_medicaid_end].strip()
            
            # Extract Medicaid Affiliate section for No Steerage
            affiliate_start = text.find('Provider acknowledges that is affiliated with health plans')
            if affiliate_start != -1:
                affiliate_end = text.find('Upon request,', affiliate_start)
                if affiliate_end == -1:
                    affiliate_end = affiliate_start + 300
                attributes['No Steerage/SOC'] = text[affiliate_start:affiliate_end].strip()
            
            # Set default for Medicare Timely Filing if not found
            if 'Medicare Timely Filing' not in attributes:
                attributes['Medicare Timely Filing'] = "Medicare timely filing requirements not explicitly specified in template."
        
        elif state == 'WA':
            # Extract WA-specific sections (similar approach to TN)
            # Extract Medicaid Fee Schedule section
            medicaid_start = text.find('medicaid fee schedule')
            if medicaid_start == -1:
                medicaid_start = text.find('Medicaid Rate')
            if medicaid_start != -1:
                medicaid_end = medicaid_start + 400
                attributes['Medicaid Fee Schedule'] = text[medicaid_start:medicaid_end].strip()
            
            # Extract Medicare section
            medicare_start = text.find('medicare')
            if medicare_start != -1:
                medicare_end = medicare_start + 350
                attributes['Medicare Fee Schedule'] = text[medicare_start:medicare_end].strip()
            
            # Extract provider network/steerage section
            network_start = text.find('provider')
            if network_start == -1:
                network_start = text.find('network')
            if network_start != -1:
                network_end = network_start + 300
                attributes['No Steerage/SOC'] = text[network_start:network_end].strip()
            
            # Set defaults for timely filing
            attributes['Medicaid Timely Filing'] = "WA Medicaid timely filing requirements to be determined from contract text"
            attributes['Medicare Timely Filing'] = "WA Medicare timely filing requirements to be determined from contract text"
        
        # Set empty strings for any missing attributes
        required_attrs = ['Medicaid Timely Filing', 'Medicare Timely Filing', 'No Steerage/SOC', 
                         'Medicaid Fee Schedule', 'Medicare Fee Schedule']
        for attr in required_attrs:
            if attr not in attributes:
                attributes[attr] = ""
        
        return attributes
    
    def _extract_clause_by_keywords(self, text: str, keywords: list) -> str:
        """Extract clause text containing specified keywords from contract."""
        # Search for keyword matches in the full text
        text_lower = text.lower()
        best_match = ""
        best_score = 0
        
        for keyword in keywords:
            if keyword in text_lower:
                # Find the position of the keyword
                start_pos = text_lower.find(keyword)
                if start_pos != -1:
                    # Extract context around the keyword (±200 characters)
                    context_start = max(0, start_pos - 100)
                    context_end = min(len(text), start_pos + 300)
                    
                    # Try to find sentence boundaries within this context
                    context = text[context_start:context_end]
                    
                    # Look for natural break points
                    sentences = context.split('. ')
                    if len(sentences) > 1:
                        # Find the sentence containing the keyword
                        for sentence in sentences:
                            if keyword in sentence.lower():
                                # Clean up the sentence
                                clean_sentence = sentence.strip()
                                if clean_sentence and len(clean_sentence) > 30:
                                    # Score based on keyword relevance and length
                                    keyword_count = sum(1 for kw in keywords if kw in clean_sentence.lower())
                                    score = keyword_count * 50 + len(clean_sentence)
                                    
                                    if score > best_score:
                                        best_score = score
                                        best_match = clean_sentence
                    else:
                        # No sentence boundaries found, use the context
                        clean_context = context.strip()
                        if clean_context and len(clean_context) > 30:
                            keyword_count = sum(1 for kw in keywords if kw in clean_context.lower())
                            score = keyword_count * 50 + len(clean_context)
                            
                            if score > best_score:
                                best_score = score
                                best_match = clean_context
        
        return best_match