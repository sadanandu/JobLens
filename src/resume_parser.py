"""
Resume Parser Module
Handles parsing of PDF and DOCX resume files.
"""

import os
from typing import Optional


def parse_pdf(file_path: str) -> str:
    """
    Parse a PDF file and extract text.
    
    Args:
        file_path: Path to the PDF file
        
    Returns:
        Extracted text content
    """
    try:
        import pdfplumber
        text_parts = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return "\n\n".join(text_parts)
    except ImportError:
        # Fallback to PyPDF2
        try:
            import PyPDF2
            text_parts = []
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
            return "\n\n".join(text_parts)
        except ImportError:
            raise ImportError(
                "No PDF parser available. Please install pdfplumber or PyPDF2: "
                "pip install pdfplumber PyPDF2"
            )


def parse_docx(file_path: str) -> str:
    """
    Parse a DOCX file and extract text.
    
    Args:
        file_path: Path to the DOCX file
        
    Returns:
        Extracted text content
    """
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text.strip())
        return "\n\n".join(paragraphs)
    except ImportError:
        raise ImportError(
            "python-docx not installed. Please install it: pip install python-docx"
        )


def parse_resume(file_path: str) -> str:
    """
    Parse a resume file (PDF or DOCX) and extract text.
    
    Args:
        file_path: Path to the resume file
        
    Returns:
        Extracted text content
        
    Raises:
        ValueError: If file format is not supported
        FileNotFoundError: If file doesn't exist
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Resume file not found: {file_path}")
    
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == '.pdf':
        return parse_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        if ext == '.doc':
            print("Warning: .doc format may have limited support. Consider saving as .docx")
        return parse_docx(file_path)
    else:
        raise ValueError(
            f"Unsupported file format: {ext}. "
            "Please provide a PDF (.pdf) or Word (.docx) file."
        )


def clean_text(text: str) -> str:
    """
    Clean extracted text by removing extra whitespace and common artifacts.
    
    Args:
        text: Raw extracted text
        
    Returns:
        Cleaned text
    """
    import re
    
    # Remove excessive whitespace
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Remove page numbers and headers/footers (common patterns)
    text = re.sub(r'^\d+$', '', text, flags=re.MULTILINE)
    
    # Remove common PDF artifacts
    text = text.replace('- ', '')  # Remove hyphenation
    text = text.replace(' \n', '\n')
    text = text.replace('\n ', '\n')
    
    return text.strip()


def get_resume_info(file_path: str) -> dict:
    """
    Get basic information about a resume file.
    
    Args:
        file_path: Path to the resume file
        
    Returns:
        Dictionary with file information
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Resume file not found: {file_path}")
    
    ext = os.path.splitext(file_path)[1].lower()
    file_size = os.path.getsize(file_path)
    
    format_map = {
        '.pdf': 'PDF',
        '.docx': 'Word Document (DOCX)',
        '.doc': 'Word Document (DOC)'
    }
    
    return {
        'filename': os.path.basename(file_path),
        'path': os.path.abspath(file_path),
        'format': format_map.get(ext, 'Unknown'),
        'extension': ext,
        'size_bytes': file_size,
        'size_kb': round(file_size / 1024, 2)
    }