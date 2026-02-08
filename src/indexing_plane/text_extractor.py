"""
Text extraction from various file formats.
Supports PDF, DOCX, PPTX, HTML, and plain text.
"""
import logging
import io
from typing import Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class TextExtractor:
    """Extract text from various file formats."""
    
    def __init__(self, enable_ocr: bool = False, ocr_language: str = "eng"):
        """
        Initialize text extractor.
        
        Args:
            enable_ocr: Enable OCR for images
            ocr_language: OCR language code
        """
        self.enable_ocr = enable_ocr
        self.ocr_language = ocr_language
        
    def extract(self, content: bytes, content_type: str, filename: Optional[str] = None) -> str:
        """
        Extract text from content.
        
        Args:
            content: File content bytes
            content_type: MIME type
            filename: Optional filename for extension detection
            
        Returns:
            Extracted text
        """
        # Determine extraction method
        if "pdf" in content_type.lower():
            return self._extract_pdf(content)
        elif "word" in content_type.lower() or (filename and filename.endswith(".docx")):
            return self._extract_docx(content)
        elif "powerpoint" in content_type.lower() or (filename and filename.endswith(".pptx")):
            return self._extract_pptx(content)
        elif "text" in content_type.lower() or "html" in content_type.lower():
            return self._extract_text(content)
        else:
            logger.warning(f"Unsupported content type: {content_type}")
            return ""
            
    def _extract_pdf(self, content: bytes) -> str:
        """Extract text from PDF."""
        try:
            from pypdf import PdfReader
            
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
                    
            return "\n\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Failed to extract PDF text: {e}")
            return ""
            
    def _extract_docx(self, content: bytes) -> str:
        """Extract text from DOCX."""
        try:
            from docx import Document
            
            doc_file = io.BytesIO(content)
            doc = Document(doc_file)
            
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text:
                    text_parts.append(paragraph.text)
                    
            # Extract from tables
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text:
                            text_parts.append(cell.text)
                            
            return "\n\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Failed to extract DOCX text: {e}")
            return ""
            
    def _extract_pptx(self, content: bytes) -> str:
        """Extract text from PPTX."""
        try:
            from pptx import Presentation
            
            pptx_file = io.BytesIO(content)
            prs = Presentation(pptx_file)
            
            text_parts = []
            for slide in prs.slides:
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        text_parts.append(shape.text)
                        
            return "\n\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Failed to extract PPTX text: {e}")
            return ""
            
    def _extract_text(self, content: bytes) -> str:
        """Extract text from plain text or HTML."""
        try:
            # Try UTF-8 first
            text = content.decode('utf-8')
            
            # If it's HTML, strip tags
            if "<html" in text.lower() or "<!doctype" in text.lower():
                text = self._strip_html(text)
                
            return text
            
        except UnicodeDecodeError:
            # Try other encodings
            for encoding in ['latin-1', 'iso-8859-1', 'cp1252']:
                try:
                    return content.decode(encoding)
                except:
                    continue
                    
            logger.error("Failed to decode text content")
            return ""
            
    def _strip_html(self, html: str) -> str:
        """Strip HTML tags."""
        try:
            from html.parser import HTMLParser
            
            class HTMLTextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text_parts = []
                    
                def handle_data(self, data):
                    self.text_parts.append(data)
                    
            parser = HTMLTextExtractor()
            parser.feed(html)
            return " ".join(parser.text_parts)
            
        except Exception as e:
            logger.error(f"Failed to strip HTML: {e}")
            # Fallback: simple tag removal
            import re
            return re.sub(r'<[^>]+>', '', html)
            
    def extract_with_ocr(self, content: bytes, content_type: str) -> str:
        """Extract text with OCR support for images."""
        if not self.enable_ocr:
            return self.extract(content, content_type)
            
        try:
            from PIL import Image
            import pytesseract
            
            # Check if it's an image
            if "image" in content_type.lower():
                image = Image.open(io.BytesIO(content))
                text = pytesseract.image_to_string(image, lang=self.ocr_language)
                return text
            else:
                # For PDFs, extract normal text first
                return self.extract(content, content_type)
                
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return self.extract(content, content_type)


def extract_text(content: bytes, content_type: str, 
                filename: Optional[str] = None,
                enable_ocr: bool = False) -> str:
    """
    Convenience function to extract text.
    
    Args:
        content: File content bytes
        content_type: MIME type
        filename: Optional filename
        enable_ocr: Enable OCR
        
    Returns:
        Extracted text
    """
    extractor = TextExtractor(enable_ocr=enable_ocr)
    return extractor.extract(content, content_type, filename)
