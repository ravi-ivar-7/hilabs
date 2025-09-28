import PyPDF2
import pdfplumber
from typing import Dict, List, Optional
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

class PDFExtractor:
    def __init__(self):
        self.supported_methods = ["pdfplumber", "pypdf2"]
    
    def extract_text(self, pdf_bytes: bytes, method: str = "pdfplumber") -> Dict[str, any]:
        try:
            if method == "pdfplumber":
                return self._extract_with_pdfplumber(pdf_bytes)
            elif method == "pypdf2":
                return self._extract_with_pypdf2(pdf_bytes)
            else:
                raise ValueError(f"Unsupported extraction method: {method}")
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            return {
                "success": False,
                "text": "",
                "pages": 0,
                "method": method,
                "error": str(e)
            }
    
    def _extract_with_pdfplumber(self, pdf_bytes: bytes) -> Dict[str, any]:
        text_content = []
        page_count = 0
        
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            page_count = len(pdf.pages)
            
            for page_num, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    text_content.append({
                        "page": page_num,
                        "text": page_text.strip()
                    })
        
        full_text = "\n\n".join([page["text"] for page in text_content])
        
        return {
            "success": True,
            "text": full_text,
            "pages": page_count,
            "page_texts": text_content,
            "method": "pdfplumber",
            "error": None
        }
    
    def _extract_with_pypdf2(self, pdf_bytes: bytes) -> Dict[str, any]:
        text_content = []
        page_count = 0
        
        pdf_reader = PyPDF2.PdfReader(BytesIO(pdf_bytes))
        page_count = len(pdf_reader.pages)
        
        for page_num, page in enumerate(pdf_reader.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_content.append({
                    "page": page_num,
                    "text": page_text.strip()
                })
        
        full_text = "\n\n".join([page["text"] for page in text_content])
        
        return {
            "success": True,
            "text": full_text,
            "pages": page_count,
            "page_texts": text_content,
            "method": "pypdf2",
            "error": None
        }
    
    def extract_with_fallback(self, pdf_bytes: bytes) -> Dict[str, any]:
        for method in self.supported_methods:
            result = self.extract_text(pdf_bytes, method)
            if result["success"] and result["text"].strip():
                return result
        
        return {
            "success": False,
            "text": "",
            "pages": 0,
            "method": "all_failed",
            "error": "All extraction methods failed"
        }
