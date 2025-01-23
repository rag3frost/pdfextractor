import pdfplumber
import PyPDF2
import re
from typing import Dict, Optional

class PDFParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        
    def extract_text_pdfplumber(self) -> str:
        """Extract text using PDFPlumber"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            print(f"Error extracting text with PDFPlumber: {str(e)}")
            return ""

    def extract_text_pypdf2(self) -> str:
        """Extract text using PyPDF2"""
        try:
            with open(self.pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() or ""
            return text
        except Exception as e:
            print(f"Error extracting text with PyPDF2: {str(e)}")
            return ""

    def extract_information(self) -> Dict[str, Optional[str]]:
        """Extract specific information from the PDF"""
        # Try PDFPlumber first, then fallback to PyPDF2 if needed
        text = self.extract_text_pdfplumber()
        if not text.strip():
            text = self.extract_text_pypdf2()

        if not text.strip():
            return {
                'name': None,
                'phone': None,
                'address': None
            }

        # Extract information using regex patterns
        info = {
            'name': self._extract_name(text),
            'phone': self._extract_phone(text),
            'address': self._extract_address(text)
        }
        return info

    def _extract_name(self, text: str) -> Optional[str]:
        """Extract name from text"""
        # Pattern for common name formats (First Last, First M. Last, etc.)
        patterns = [
            r'(?i)name[:\s]+([A-Z][a-z]+(?:\s+[A-Z]\.?\s+)?[A-Z][a-z]+)',  # Name: John Doe
            r'(?i)([A-Z][a-z]+(?:\s+[A-Z]\.?\s+)?[A-Z][a-z]+)'  # Just "John Doe"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number from text"""
        patterns = [
            r'(?i)phone[:\s]+(\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4})',  # Phone: format
            r'(\+?\d{1,3}[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4})'  # Just the number
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return None

    def _extract_address(self, text: str) -> Optional[str]:
        """Extract address from text"""
        patterns = [
            r'(?i)address[:\s]+([0-9]+\s+[A-Za-z\s,]+\s+[A-Za-z]+\s+[A-Z]{2}\s+\d{5})',  # Full address
            r'([0-9]+\s+[A-Za-z\s,]+\s+[A-Za-z]+\s+[A-Z]{2}\s+\d{5})'  # Just the address
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return None

def main():
    # Example usage
    pdf_path = "example.pdf"  # Replace with your PDF file
    parser = PDFParser(pdf_path)
    
    info = parser.extract_information()
    print("\nExtracted Information:")
    print("---------------------")
    print(f"Name: {info['name']}")
    print(f"Phone: {info['phone']}")
    print(f"Address: {info['address']}")

if __name__ == "__main__":
    main() 