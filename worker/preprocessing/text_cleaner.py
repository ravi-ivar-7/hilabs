import re
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class TextCleaner:
    def __init__(self):
        self.whitespace_pattern = re.compile(r'\s+')
        self.special_chars_pattern = re.compile(r'[^\w\s\.\,\;\:\!\?\-\(\)\[\]\{\}\"\'\/]')
        self.page_break_pattern = re.compile(r'\n\s*\n\s*\n+')
        
    def clean_text(self, text: str, options: Dict[str, bool] = None) -> Dict[str, any]:
        if options is None:
            options = {
                "normalize_whitespace": True,
                "remove_extra_newlines": True,
                "remove_special_chars": False,
                "preserve_structure": True,
                "remove_headers_footers": True
            }
        
        try:
            cleaned_text = text
            operations_applied = []
            
            if options.get("remove_headers_footers", True):
                cleaned_text = self._remove_headers_footers(cleaned_text)
                operations_applied.append("headers_footers_removed")
            
            if options.get("normalize_whitespace", True):
                cleaned_text = self._normalize_whitespace(cleaned_text)
                operations_applied.append("whitespace_normalized")
            
            if options.get("remove_extra_newlines", True):
                cleaned_text = self._remove_extra_newlines(cleaned_text)
                operations_applied.append("extra_newlines_removed")
            
            if options.get("remove_special_chars", False):
                cleaned_text = self._remove_special_chars(cleaned_text)
                operations_applied.append("special_chars_removed")
            
            if options.get("preserve_structure", True):
                cleaned_text = self._preserve_structure(cleaned_text)
                operations_applied.append("structure_preserved")
            
            return {
                "success": True,
                "original_text": text,
                "cleaned_text": cleaned_text,
                "original_length": len(text),
                "cleaned_length": len(cleaned_text),
                "operations_applied": operations_applied,
                "error": None
            }
            
        except Exception as e:
            logger.error(f"Text cleaning failed: {str(e)}")
            return {
                "success": False,
                "original_text": text,
                "cleaned_text": text,
                "original_length": len(text),
                "cleaned_length": len(text),
                "operations_applied": [],
                "error": str(e)
            }
    
    def _normalize_whitespace(self, text: str) -> str:
        return self.whitespace_pattern.sub(' ', text)
    
    def _remove_extra_newlines(self, text: str) -> str:
        return self.page_break_pattern.sub('\n\n', text)
    
    def _remove_special_chars(self, text: str) -> str:
        return self.special_chars_pattern.sub('', text)
    
    def _remove_headers_footers(self, text: str) -> str:
        lines = text.split('\n')
        if len(lines) <= 10:
            return text
        
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if self._is_likely_header_footer(line):
                continue
            cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _is_likely_header_footer(self, line: str) -> bool:
        line = line.strip().lower()
        
        if len(line) < 3:
            return True
        
        header_footer_patterns = [
            r'page\s+\d+',
            r'\d+\s+of\s+\d+',
            r'confidential',
            r'proprietary',
            r'copyright',
            r'©',
            r'all rights reserved'
        ]
        
        for pattern in header_footer_patterns:
            if re.search(pattern, line):
                return True
        
        return False
    
    def _preserve_structure(self, text: str) -> str:
        lines = text.split('\n')
        structured_lines = []
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                structured_lines.append('')
                continue
            
            if self._is_section_header(stripped):
                structured_lines.append(f"\n{stripped}\n")
            elif self._is_list_item(stripped):
                structured_lines.append(f"  {stripped}")
            else:
                structured_lines.append(stripped)
        
        return '\n'.join(structured_lines)
    
    def _is_section_header(self, line: str) -> bool:
        section_patterns = [
            r'^\d+\.\s+[A-Z]',
            r'^[A-Z][A-Z\s]+:$',
            r'^SECTION\s+\d+',
            r'^ARTICLE\s+\d+'
        ]
        
        for pattern in section_patterns:
            if re.match(pattern, line):
                return True
        
        return False
    
    def _is_list_item(self, line: str) -> bool:
        list_patterns = [
            r'^\d+\)',
            r'^[a-z]\)',
            r'^•',
            r'^-\s+',
            r'^\*\s+'
        ]
        
        for pattern in list_patterns:
            if re.match(pattern, line):
                return True
        
        return False
