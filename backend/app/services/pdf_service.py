"""
PDF parsing service
"""
import PyPDF2
from io import BytesIO
from typing import Optional
from app.config import settings


def extract_text_from_pdf(pdf_bytes: bytes, max_pages: Optional[int] = None) -> str:
    """
    Extract text from PDF file bytes.
    
    Args:
        pdf_bytes: PDF file as bytes
        max_pages: Maximum number of pages to extract (None = all pages)
    
    Returns:
        Extracted text content
    """
    pdf_file = BytesIO(pdf_bytes)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    
    max_pages = max_pages or settings.max_pdf_pages
    total_pages = len(pdf_reader.pages)
    pages_to_extract = min(max_pages, total_pages)
    
    text_parts = []
    for page_num in range(pages_to_extract):
        page = pdf_reader.pages[page_num]
        text = page.extract_text()
        if text.strip():
            text_parts.append(text)
    
    full_text = "\n\n".join(text_parts)
    
    if pages_to_extract < total_pages:
        full_text += f"\n\n[Note: Only first {pages_to_extract} pages extracted from {total_pages} total pages]"
    
    return full_text

