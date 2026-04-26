#!/usr/bin/env python3
"""
Tests for the ResumeParser module.

Tests the ResumeParser class functionality including:
- PDF text extraction
- DOCX text extraction
- Error handling for unsupported formats
- File validation
"""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from src.resume_parser import ResumeParser


class TestResumeParser(unittest.TestCase):
    """Test cases for the ResumeParser class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = ResumeParser()
        self.test_data_dir = Path(__file__).parent / "test_data"
        self.test_data_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        """Clean up test fixtures."""
        # Remove test data directory if it exists
        if self.test_data_dir.exists():
            import shutil
            shutil.rmtree(self.test_data_dir)
    
    def test_supported_formats(self):
        """Test that supported formats are correctly identified."""
        supported = self.parser.get_supported_formats()
        self.assertIn(".pdf", supported)
        self.assertIn(".docx", supported)
        self.assertEqual(len(supported), 2)
    
    def test_is_supported_format(self):
        """Test format checking utility method."""
        self.assertTrue(ResumeParser.is_supported_format("resume.pdf"))
        self.assertTrue(ResumeParser.is_supported_format("resume.DOCX"))
        self.assertTrue(ResumeParser.is_supported_format("resume.docx"))
        self.assertFalse(ResumeParser.is_supported_format("resume.txt"))
        self.assertFalse(ResumeParser.is_supported_format("resume"))
    
    def test_parse_nonexistent_file(self):
        """Test parsing a non-existent file raises FileNotFoundError."""
        nonexistent_path = self.test_data_dir / "nonexistent.pdf"
        with self.assertRaises(FileNotFoundError) as context:
            self.parser.parse(nonexistent_path)
        self.assertIn("Resume file not found", str(context.exception))
    
    def test_parse_unsupported_format(self):
        """Test parsing an unsupported file format raises ValueError."""
        # Create a temporary file with unsupported extension
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_path = Path(temp_file.name)
        
        try:
            with self.assertRaises(ValueError) as context:
                self.parser.parse(temp_path)
            self.assertIn("Unsupported resume format", str(context.exception))
        finally:
            temp_path.unlink()


class TestResumeParserPDF(unittest.TestCase):
    """Test cases for PDF parsing functionality."""
    
    def setUp(self):
        """Set up test fixtures with mocked pdfplumber."""
        # Create a mock for pdfplumber
        self.mock_pdfplumber = MagicMock()
        self.pdf_patcher = patch.dict('sys.modules', {'pdfplumber': self.mock_pdfplumber})
        self.pdf_patcher.start()
        
        # Reimport to pick up the mocked module
        import importlib
        import src.resume_parser as rp
        importlib.reload(rp)
        self.parser = rp.ResumeParser()
    
    def tearDown(self):
        """Clean up mocks."""
        self.pdf_patcher.stop()
    
    def test_parse_pdf_success(self):
        """Test successful PDF parsing."""
        # Mock pdfplumber functionality
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "Test PDF content"
        mock_pdf.pages = [mock_page]
        self.mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            result = self.parser.parse(temp_path)
            self.assertEqual(result, "Test PDF content")
            self.mock_pdfplumber.open.assert_called_once_with(temp_path)
        finally:
            temp_path.unlink()
    
    def test_parse_pdf_no_text(self):
        """Test PDF parsing when no text is extracted."""
        # Mock pdfplumber with no text content
        mock_pdf = Mock()
        mock_page = Mock()
        mock_page.extract_text.return_value = None
        mock_pdf.pages = [mock_page]
        self.mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            result = self.parser.parse(temp_path)
            self.assertEqual(result, "")
        finally:
            temp_path.unlink()
    
    def test_parse_pdf_extraction_error(self):
        """Test PDF parsing when extraction fails."""
        self.mock_pdfplumber.open.side_effect = Exception("PDF parsing failed")
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            with self.assertRaises(RuntimeError) as context:
                self.parser.parse(temp_path)
            self.assertIn("PDF parsing error", str(context.exception))
        finally:
            temp_path.unlink()
    
    def test_parse_pdf_with_multiple_pages(self):
        """Test PDF parsing with multiple pages."""
        # Mock multi-page PDF
        mock_pdf = Mock()
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "Page 2 content"
        mock_pdf.pages = [mock_page1, mock_page2]
        self.mock_pdfplumber.open.return_value.__enter__.return_value = mock_pdf
        
        # Create a temporary PDF file
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            result = self.parser.parse(temp_path)
            expected = "Page 1 content\n\nPage 2 content"
            self.assertEqual(result, expected)
        finally:
            temp_path.unlink()


class TestResumeParserPDFNotInstalled(unittest.TestCase):
    """Test cases for when pdfplumber is not installed."""
    
    def test_parse_pdf_import_error(self):
        """Test PDF parsing when pdfplumber is not installed."""
        # Ensure pdfplumber is not in sys.modules
        with patch.dict('sys.modules', {'pdfplumber': None}):
            import importlib
            import src.resume_parser as rp
            importlib.reload(rp)
            parser = rp.ResumeParser()
            
            # Create a temporary PDF file
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            
            try:
                with self.assertRaises(RuntimeError) as context:
                    parser.parse(temp_path)
                self.assertIn("pdfplumber library is not installed", str(context.exception))
            finally:
                temp_path.unlink()


class TestResumeParserDOCX(unittest.TestCase):
    """Test cases for DOCX parsing functionality."""
    
    def setUp(self):
        """Set up test fixtures with mocked docx."""
        # Create a mock for docx
        self.mock_docx = MagicMock()
        self.docx_patcher = patch.dict('sys.modules', {'docx': self.mock_docx})
        self.docx_patcher.start()
        
        # Reimport to pick up the mocked module
        import importlib
        import src.resume_parser as rp
        importlib.reload(rp)
        self.parser = rp.ResumeParser()
    
    def tearDown(self):
        """Clean up mocks."""
        self.docx_patcher.stop()
    
    def test_parse_docx_success(self):
        """Test successful DOCX parsing."""
        # Mock python-docx functionality
        mock_doc = Mock()
        mock_paragraph1 = Mock()
        mock_paragraph1.text = "Test DOCX content line 1"
        mock_paragraph2 = Mock()
        mock_paragraph2.text = "Test DOCX content line 2"
        mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2]
        self.mock_docx.Document.return_value = mock_doc
        
        # Create a temporary DOCX file
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            result = self.parser.parse(temp_path)
            expected = "Test DOCX content line 1\n\nTest DOCX content line 2"
            self.assertEqual(result, expected)
            self.mock_docx.Document.assert_called_once_with(temp_path)
        finally:
            temp_path.unlink()
    
    def test_parse_docx_no_text(self):
        """Test DOCX parsing when no text is extracted."""
        # Mock python-docx with no text content
        mock_doc = Mock()
        mock_paragraph = Mock()
        mock_paragraph.text = ""
        mock_doc.paragraphs = [mock_paragraph]
        self.mock_docx.Document.return_value = mock_doc
        
        # Create a temporary DOCX file
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            result = self.parser.parse(temp_path)
            self.assertEqual(result, "")
        finally:
            temp_path.unlink()
    
    def test_parse_docx_extraction_error(self):
        """Test DOCX parsing when extraction fails."""
        self.mock_docx.Document.side_effect = Exception("DOCX parsing failed")
        
        # Create a temporary DOCX file
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            with self.assertRaises(RuntimeError) as context:
                self.parser.parse(temp_path)
            self.assertIn("DOCX parsing error", str(context.exception))
        finally:
            temp_path.unlink()
    
    def test_parse_docx_with_multiple_paragraphs(self):
        """Test DOCX parsing with multiple paragraphs."""
        # Mock multi-paragraph DOCX
        mock_doc = Mock()
        mock_paragraph1 = Mock()
        mock_paragraph1.text = "Paragraph 1"
        mock_paragraph2 = Mock()
        mock_paragraph2.text = "Paragraph 2"
        mock_paragraph3 = Mock()
        mock_paragraph3.text = "Paragraph 3"
        mock_doc.paragraphs = [mock_paragraph1, mock_paragraph2, mock_paragraph3]
        self.mock_docx.Document.return_value = mock_doc
        
        # Create a temporary DOCX file
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
            temp_path = Path(temp_file.name)
        
        try:
            result = self.parser.parse(temp_path)
            expected = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
            self.assertEqual(result, expected)
        finally:
            temp_path.unlink()


class TestResumeParserDOCXNotInstalled(unittest.TestCase):
    """Test cases for when python-docx is not installed."""
    
    def test_parse_docx_import_error(self):
        """Test DOCX parsing when python-docx is not installed."""
        # Ensure docx is not in sys.modules
        with patch.dict('sys.modules', {'docx': None}):
            import importlib
            import src.resume_parser as rp
            importlib.reload(rp)
            parser = rp.ResumeParser()
            
            # Create a temporary DOCX file
            with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            
            try:
                with self.assertRaises(RuntimeError) as context:
                    parser.parse(temp_path)
                self.assertIn("python-docx library is not installed", str(context.exception))
            finally:
                temp_path.unlink()


if __name__ == "__main__":
    unittest.main()