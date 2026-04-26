#!/usr/bin/env python3
"""
Job Search Agent - Resume Parser Module

Handles extraction of text content from resume files in PDF and DOCX formats.
"""

import logging
from pathlib import Path
from typing import Union

# Optional imports - will be loaded when needed
_pdfplumber_available = False
_docx_available = False

try:
    import pdfplumber
    _pdfplumber_available = True
except ImportError:
    pass

try:
    import docx
    _docx_available = True
except ImportError:
    pass

logger = logging.getLogger(__name__)


class ResumeParser:
    """
    A unified parser for extracting text from resume files.
    
    Supports PDF (via pdfplumber) and DOCX (via python-docx) formats.
    Provides clean extracted text suitable for further processing.
    """
    
    SUPPORTED_EXTENSIONS = {".pdf", ".docx"}
    
    def __init__(self):
        """Initialize the ResumeParser."""
        self._supported_formats = self.SUPPORTED_EXTENSIONS.copy()
    
    def parse(self, file_path: Union[str, Path]) -> str:
        """
        Extract text content from a resume file.
        
        Args:
            file_path: Path to the resume file (PDF or DOCX).
        
        Returns:
            str: Clean extracted text content from the resume.
        
        Raises:
            FileNotFoundError: If the resume file does not exist.
            ValueError: If the file format is not supported.
            RuntimeError: If there's an error during parsing.
        """
        path = Path(file_path)
        
        # Validate file exists
        if not path.exists():
            raise FileNotFoundError(f"Resume file not found: {file_path}")
        
        # Validate file extension
        extension = path.suffix.lower()
        if extension not in self._supported_formats:
            raise ValueError(
                f"Unsupported resume format: '{extension}'. "
                f"Supported formats: {', '.join(sorted(self._supported_formats))}"
            )
        
        # Extract text based on file type
        try:
            if extension == ".pdf":
                text = self._parse_pdf(path)
            elif extension == ".docx":
                text = self._parse_docx(path)
            else:
                # This shouldn't happen due to validation above, but added for safety
                raise ValueError(f"Unsupported format: {extension}")
        except Exception as e:
            logger.error(f"Failed to parse resume '{file_path}': {e}")
            raise RuntimeError(f"Failed to parse resume '{file_path}': {e}") from e
        
        logger.info(f"Successfully parsed resume: {file_path} ({len(text)} characters)")
        return text
    
    def _parse_pdf(self, file_path: Path) -> str:
        """
        Extract text from a PDF file using pdfplumber.
        
        Args:
            file_path: Path to the PDF file.
        
        Returns:
            str: Extracted text content.
        
        Raises:
            RuntimeError: If pdfplumber fails to extract text.
        """
        if not _pdfplumber_available:
            raise RuntimeError(
                "pdfplumber library is not installed. "
                "Please install it using: pip install pdfplumber"
            )
        
        try:
            text_parts = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text.strip())
            
            if not text_parts:
                logger.warning(f"No text extracted from PDF: {file_path}")
                return ""
            
            # Join pages with double newlines for readability
            return "\n\n".join(text_parts)
        
        except Exception as e:
            raise RuntimeError(f"PDF parsing error: {e}") from e
    
    def _parse_docx(self, file_path: Path) -> str:
        """
        Extract text from a DOCX file using python-docx.
        
        Args:
            file_path: Path to the DOCX file.
        
        Returns:
            str: Extracted text content.
        
        Raises:
            RuntimeError: If python-docx fails to extract text.
        """
        if not _docx_available:
            raise RuntimeError(
                "python-docx library is not installed. "
                "Please install it using: pip install python-docx"
            )
        
        try:
            doc = docx.Document(file_path)
            text_parts = []
            
            # Extract text from paragraphs
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text.strip())
            
            if not text_parts:
                logger.warning(f"No text extracted from DOCX: {file_path}")
                return ""
            
            # Join paragraphs with double newlines for readability
            return "\n\n".join(text_parts)
        
        except Exception as e:
            raise RuntimeError(f"DOCX parsing error: {e}") from e
    
    def get_supported_formats(self) -> set[str]:
        """
        Get the set of supported file formats.
        
        Returns:
            set[str]: Set of supported file extensions (e.g., {'.pdf', '.docx'}).
        """
        return self._supported_formats.copy()
    
    @staticmethod
    def is_supported_format(file_path: Union[str, Path]) -> bool:
        """
        Check if a file has a supported format.
        
        Args:
            file_path: Path to the file to check.
        
        Returns:
            bool: True if the file format is supported, False otherwise.
        """
        path = Path(file_path)
        return path.suffix.lower() in ResumeParser.SUPPORTED_EXTENSIONS