import os
# Disable TensorFlow warnings and force PyTorch
os.environ['USE_TORCH'] = '1'
os.environ['FORCE_TORCH'] = '1'
os.environ['TRANSFORMERS_FRAMEWORK'] = 'pt'
# Suppress TensorFlow warnings
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import pdfplumber
import PyPDF2
import re
from typing import Dict, Optional, List, Tuple
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline
import torch

class AIPDFParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        try:
            # Initialize with the new Hungarian NER model
            model_name = "NYTK/named-entity-recognition-nerkor-hubert-hungarian"
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(model_name)
            
            # Device setup
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            self.model = self.model.to(self.device)
            
            # Updated label mappings for the Hungarian model
            self.label_map = {
                'B-PER': 'B-PERSON',
                'I-PER': 'I-PERSON',
                'B-LOC': 'B-LOCATION',
                'I-LOC': 'I-LOCATION',
                'B-ORG': 'B-ORGANIZATION',
                'I-ORG': 'I-ORGANIZATION'
            }
            
            self.ner_pipeline = pipeline(
                "token-classification",
                model=self.model,
                tokenizer=self.tokenizer,
                device=self.device,
                framework="pt",
                aggregation_strategy="simple"  # Use simple aggregation for better entity grouping
            )
            print(f"Hungarian NER model loaded successfully on {self.device}")
        except Exception as e:
            print(f"Error loading NER model: {str(e)}")
            raise

    def _map_entity_label(self, label: str) -> str:
        """Map Hungarian model labels to our expected format"""
        return self.label_map.get(label, label)

    def extract_text(self) -> str:
        """Extract text from PDF using multiple methods"""
        text = self._extract_with_pdfplumber()
        if not text.strip():
            text = self._extract_with_pypdf2()
        return text

    def _extract_with_pdfplumber(self) -> str:
        """Extract text using PDFPlumber"""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                return "\n".join(page.extract_text() or "" for page in pdf.pages)
        except Exception as e:
            print(f"PDFPlumber extraction error: {str(e)}")
            return ""

    def _extract_with_pypdf2(self) -> str:
        """Extract text using PyPDF2"""
        try:
            with open(self.pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
        except Exception as e:
            print(f"PyPDF2 extraction error: {str(e)}")
            return ""

    def _find_best_person_name(self, text: str) -> Optional[str]:
        """Find the most likely person name using Hungarian NER and patterns"""
        try:
            entities = self.ner_pipeline(text)
            person_names = []
            current_name = []
            current_score = 0
            
            # First try NER-based extraction
            for entity in entities:
                mapped_label = self._map_entity_label(entity['entity_group'])
                if mapped_label in ['B-PERSON', 'I-PERSON']:
                    word = entity['word'].strip()
                    if word:
                        current_name.append(word)
                        current_score += entity['score']
                elif current_name:
                    full_name = ' '.join(current_name).strip()
                    full_name = re.sub(r'\s+', ' ', full_name)
                    if full_name:
                        avg_score = current_score / len(current_name)
                        person_names.append((full_name, avg_score))
                    current_name = []
                    current_score = 0
            
            # Add fallback patterns for name detection
            if not person_names:
                name_patterns = [
                    (r'(?i)name[:\s]+([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)', 0.9),
                    (r'(?i)([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+\s*(?:MD|PhD|Jr\.?|Sr\.?)?)', 0.85),
                    (r'(?i)(?:dr\.?\s+|mr\.?\s+|mrs\.?\s+|ms\.?\s+)([A-Z][a-z]+(?:\s+[A-Z]\.?\s*)?[A-Z][a-z]+)', 0.95)
                ]
                
                for pattern, confidence in name_patterns:
                    matches = re.finditer(pattern, text)
                    for match in matches:
                        name = match.group(1).strip()
                        if name and not any(char.isdigit() for char in name):
                            person_names.append((name, confidence))
            
            if person_names:
                # Sort by confidence and return the best match
                return max(person_names, key=lambda x: x[1])[0]
            
            return None
            
        except Exception as e:
            print(f"Error in name extraction: {str(e)}")
            return None

    def _find_phone_numbers(self, text: str) -> List[Tuple[str, float]]:
        """Extract phone numbers with improved accuracy"""
        phone_numbers = []
        try:
            # More comprehensive phone patterns
            phone_patterns = [
                # Pattern with country code
                (r'(?i)(?:phone|tel|telephone|contact|mobile|cell)?[:\s]*(\+\d{1,3})?[-\s]*[\(]?(\d{3})[\)]?[-.\s]?(\d{3})[-.\s]?(\d{4})', 0.95),
                # Backup patterns
                (r'(?<!\d)(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4})(?!\d)', 0.9),
                (r'(?<!\d)(\+\d{1,3})[-.\s]?(\d{3})[-.\s]?(\d{3})[-.\s]?(\d{4})(?!\d)', 0.85)
            ]
            
            for pattern, confidence in phone_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    if len(match.groups()) >= 3:
                        # Check if country code is present
                        if len(match.groups()) == 4 and match.group(1):
                            # Use provided country code
                            country_code = match.group(1).strip()
                            phone = f"{country_code}-{match.group(2)}-{match.group(3)}-{match.group(4)}"
                        else:
                            # Default to +1 if no country code
                            phone = f"+1-{match.group(2)}-{match.group(3)}-{match.group(4)}" if len(match.groups()) == 4 else f"+1-{match.group(1)}-{match.group(2)}-{match.group(3)}"
                    else:
                        # Normalize existing format
                        phone = match.group(1)
                        phone = re.sub(r'[^\d]', '', phone)
                        phone = f"+1-{phone[:3]}-{phone[3:6]}-{phone[6:]}"
                    
                    phone_numbers.append((phone, confidence))
                    # Break after finding the first valid phone number
                    break
            
            return phone_numbers
            
        except Exception as e:
            print(f"Error in phone extraction: {str(e)}")
            return []

    def _find_addresses(self, text: str) -> List[Tuple[str, float]]:
        """Find addresses using patterns and cleanup"""
        addresses = []
        try:
            # First remove phone numbers from text
            text_without_phones = re.sub(
                r'(?i)(?:phone|tel|telephone|contact|mobile|cell)?[:\s]*(?:\+1\s*)?[\(]?\d{3}[\)]?[-.\s]?\d{3}[-.\s]?\d{4}',
                '',
                text
            )
            
            # Address patterns
            address_patterns = [
                (r'(?m)^[^\d]*(\d+[^.]*?(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)[^.]*?(?:Floor|Fl|Suite|Ste)?[^.]*?(?:San Francisco|SF)?[^.]*?(?:CA|California)[^.]*?\d{5}(?:-\d{4})?)', 0.95),
                (r'(\d+[^.]*?(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd)[^.]*?(?:Floor|Fl|Suite|Ste)?[^.]*?(?:San Francisco|SF)?[^.]*?(?:CA|California)[^.]*?\d{5}(?:-\d{4})?)', 0.9),
            ]
            
            for pattern, confidence in address_patterns:
                matches = re.finditer(pattern, text_without_phones, re.IGNORECASE)
                for match in matches:
                    addr = match.group(1).strip()
                    # Clean up the address
                    addr = re.sub(r'\s+', ' ', addr)
                    # Remove any remaining phone numbers
                    addr = re.sub(r'(?<!\d)\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)', '', addr)
                    addr = re.sub(r'\s+', ' ', addr).strip()
                    if addr:
                        addresses.append((addr, confidence))
            
            # If no address found, try the NER approach with cleaned text
            if not addresses:
                entities = self.ner_pipeline(text_without_phones)
                current_address = []
                current_score = 0
                
                for entity in entities:
                    mapped_label = self._map_entity_label(entity['entity_group'])
                    if mapped_label in ['B-LOCATION', 'I-LOCATION']:
                        word = entity['word'].strip()
                        if word:
                            current_address.append(word)
                            current_score += entity['score']
                    elif current_address:
                        addr = ' '.join(current_address)
                        addr = re.sub(r'\s+', ' ', addr).strip()
                        if addr:
                            avg_score = current_score / len(current_address)
                            addresses.append((addr, avg_score))
                        current_address = []
                        current_score = 0
            
            return addresses
            
        except Exception as e:
            print(f"Error in address extraction: {str(e)}")
            return []

    def _find_role(self, text: str) -> Optional[Tuple[str, float]]:
        """Find role/job title using patterns"""
        role_patterns = [
            (r'(?i)\b(software\s+developer)\b', 1.0),
            (r'(?i)\b(software\s+engineer)\b', 1.0),
            (r'(?i)\b(developer)\b', 0.8),
            (r'(?i)\b(engineer)\b', 0.8),
            (r'(?i)(?:position|role|title|job)[\s:]+([^.]*?(?:developer|engineer)[^.]*?)(?:\.|$)', 0.9),
            (r'(?i)(?:work\s+as|working\s+as)[\s:]+([^.]*?(?:developer|engineer)[^.]*?)(?:\.|$)', 0.9),
        ]
        
        for pattern, confidence in role_patterns:
            match = re.search(pattern, text)
            if match:
                role = match.group(1).strip()
                return (role.title(), confidence)
        
        return None

    def extract_information(self) -> Dict[str, Optional[str]]:
        """Extract information using pattern matching and NER"""
        text = self.extract_text()
        if not text.strip():
            return self._empty_result()

        try:
            print(f"Extracted text:\n{text}\n")  # Debug print

            # Extract information in specific order
            phone_numbers = self._find_phone_numbers(text)
            # Remove phone numbers from text before address extraction
            text_without_phones = text
            if phone_numbers:
                for phone, _ in phone_numbers:
                    text_without_phones = re.sub(re.escape(phone), '', text_without_phones)
            
            addresses = self._find_addresses(text_without_phones)
            name = self._find_best_person_name(text)
            role_info = self._find_role(text)

            return {
                'name': name,
                'phone': phone_numbers[0][0] if phone_numbers else None,
                'address': addresses[0][0] if addresses else None,
                'role': role_info[0] if role_info else None,
                'confidence': {
                    'name': 1.0 if name else 0.0,
                    'phone': phone_numbers[0][1] if phone_numbers else 0.0,
                    'address': addresses[0][1] if addresses else 0.0,
                    'role': role_info[1] if role_info else 0.0
                }
            }
        except Exception as e:
            print(f"Error in information extraction: {str(e)}")
            return self._empty_result()

    def _empty_result(self) -> Dict[str, Optional[str]]:
        """Return empty result structure"""
        return {
            'name': None,
            'phone': None,
            'address': None,
            'role': None,
            'confidence': {
                'name': 0.0,
                'phone': 0.0,
                'address': 0.0,
                'role': 0.0
            }
        }

def main():
    # Use the specific PDF file
    pdf_path = "D:/MLOps/backend/Saferidestoptable.pdf"
    parser = AIPDFParser(pdf_path)
    
    info = parser.extract_information()
    print("\nExtracted Information:")
    print("---------------------")
    print(f"Name: {info['name']}")
    print(f"Phone: {info['phone']}")
    print(f"Address: {info['address']}")
    print(f"Role: {info['role']}")
    print("\nConfidence Scores:")
    print(f"Name: {info['confidence']['name']:.2f}")
    print(f"Phone: {info['confidence']['phone']:.2f}")
    print(f"Address: {info['confidence']['address']:.2f}")
    print(f"Role: {info['confidence']['role']:.2f}")

if __name__ == "__main__":
    main() 