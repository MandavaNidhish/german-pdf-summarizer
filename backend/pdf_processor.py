# backend/pdf_processor.py - Advanced PDF Processing (Your Kaggle Code Adapted)
import os
import time
import re
import logging
from pathlib import Path

# PDF processing libraries
try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import pypdfium2
    PYPDFIUM2_AVAILABLE = True
except ImportError:
    PYPDFIUM2_AVAILABLE = False

logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Advanced PDF processor that extracts and cleans text from German business documents
    Adapted from your Kaggle code with multiple extraction methods
    """
    
    def __init__(self):
        self.available_methods = []
        
        if PYMUPDF_AVAILABLE:
            self.available_methods.append('pymupdf')
        if PDFPLUMBER_AVAILABLE:
            self.available_methods.append('pdfplumber')
        if PYPDFIUM2_AVAILABLE:
            self.available_methods.append('pypdfium2')
        
        logger.info(f"PDF processor initialized with methods: {self.available_methods}")
        
        if not self.available_methods:
            raise RuntimeError("No PDF processing libraries available. Install PyMuPDF, pdfplumber, or pypdfium2")
    
    def process_pdf(self, file_path):
        """
        Main processing method - tries all available methods and returns best result
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            dict: Processing result with success status and cleaned text
        """
        try:
            logger.info(f"Processing PDF: {os.path.basename(file_path)}")
            
            # Validate PDF file
            validation_result = self._validate_pdf(file_path)
            if not validation_result["valid"]:
                return {"success": False, "error": validation_result["error"]}
            
            # Try all available extraction methods
            extraction_results = []
            
            for method in self.available_methods:
                try:
                    if method == 'pymupdf':
                        result = self._extract_text_pymupdf(file_path)
                    elif method == 'pdfplumber':
                        result = self._extract_text_pdfplumber(file_path)
                    elif method == 'pypdfium2':
                        result = self._extract_text_pypdfium2(file_path)
                    
                    if result["success"]:
                        extraction_results.append(result)
                        
                except Exception as e:
                    logger.warning(f"Method {method} failed: {e}")
                    continue
            
            if not extraction_results:
                return {"success": False, "error": "All text extraction methods failed"}
            
            # Choose best result (prioritize text length, then speed)
            best_result = self._choose_best_result(extraction_results)
            
            # Preprocess the extracted text
            cleaned_text = self._preprocess_german_text(best_result["text"])
            
            final_result = {
                "success": True,
                "method": best_result["method"],
                "raw_text": best_result["text"],
                "cleaned_text": cleaned_text,
                "stats": {
                    "raw_length": len(best_result["text"]),
                    "cleaned_length": len(cleaned_text),
                    "word_count": len(cleaned_text.split()),
                    "processing_time": best_result["processing_time"],
                    "pages_processed": best_result.get("pages_processed", 0)
                }
            }
            
            logger.info(f"PDF processed successfully: {final_result['stats']['word_count']} words extracted")
            return final_result
            
        except Exception as e:
            logger.error(f"PDF processing failed: {e}")
            return {"success": False, "error": str(e)}
    
    def _validate_pdf(self, file_path):
        """Validate PDF file - adapted from your Kaggle code"""
        try:
            if not os.path.exists(file_path):
                return {"valid": False, "error": "File not found"}
            
            if not file_path.lower().endswith('.pdf'):
                return {"valid": False, "error": "Not a PDF file"}
            
            file_size_mb = os.path.getsize(file_path) / (1024*1024)
            
            if file_size_mb > 50:  # Reasonable limit
                return {"valid": False, "error": "PDF file too large (>50MB)"}
            
            # Try basic PDF validation
            if PYMUPDF_AVAILABLE:
                try:
                    doc = fitz.open(file_path)
                    page_count = len(doc)
                    doc.close()
                    
                    if page_count == 0:
                        return {"valid": False, "error": "PDF has no pages"}
                    
                except Exception:
                    return {"valid": False, "error": "Invalid or corrupted PDF file"}
            
            return {"valid": True}
            
        except Exception as e:
            return {"valid": False, "error": f"Validation failed: {str(e)}"}
    
    def _extract_text_pymupdf(self, file_path):
        """Extract text using PyMuPDF - your original method"""
        logger.info("Extracting text using PyMuPDF...")
        start_time = time.time()
        
        try:
            doc = fitz.open(file_path)
            extracted_text = ""
            total_pages = len(doc)
            
            for page_num in range(total_pages):
                page = doc[page_num]
                page_text = page.get_text()
                
                extracted_text += f"\\n\\n--- PAGE {page_num + 1} ---\\n\\n"
                extracted_text += page_text
            
            doc.close()
            
            processing_time = time.time() - start_time
            text_length = len(extracted_text.strip())
            word_count = len(extracted_text.split())
            
            return {
                "method": "PyMuPDF",
                "success": True,
                "text": extracted_text.strip(),
                "text_length": text_length,
                "word_count": word_count,
                "processing_time": round(processing_time, 3),
                "pages_processed": total_pages
            }
            
        except Exception as e:
            return {
                "method": "PyMuPDF",
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _extract_text_pdfplumber(self, file_path):
        """Extract text using pdfplumber - your original method with tables"""
        logger.info("Extracting text using pdfplumber...")
        start_time = time.time()
        
        try:
            extracted_text = ""
            
            with pdfplumber.open(file_path) as pdf:
                total_pages = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += f"\\n\\n--- PAGE {page_num + 1} ---\\n\\n"
                        extracted_text += page_text
                    
                    # Extract table data if present
                    tables = page.extract_tables()
                    if tables:
                        extracted_text += f"\\n\\n[TABLES ON PAGE {page_num + 1}]\\n"
                        for table_num, table in enumerate(tables):
                            extracted_text += f"\\nTable {table_num + 1}:\\n"
                            for row in table:
                                if row:
                                    row_text = " | ".join([cell if cell else "" for cell in row])
                                    extracted_text += row_text + "\\n"
            
            processing_time = time.time() - start_time
            text_length = len(extracted_text.strip())
            word_count = len(extracted_text.split())
            
            return {
                "method": "pdfplumber",
                "success": True,
                "text": extracted_text.strip(),
                "text_length": text_length,
                "word_count": word_count,
                "processing_time": round(processing_time, 3),
                "pages_processed": total_pages,
                "includes_tables": "[TABLES ON PAGE" in extracted_text
            }
            
        except Exception as e:
            return {
                "method": "pdfplumber",
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _extract_text_pypdfium2(self, file_path):
        """Extract text using pypdfium2 - your original method"""
        logger.info("Extracting text using pypdfium2...")
        start_time = time.time()
        
        try:
            pdf = pypdfium2.PdfDocument(file_path)
            extracted_text = ""
            total_pages = len(pdf)
            
            for page_num in range(total_pages):
                page = pdf.get_page(page_num)
                textpage = page.get_textpage()
                page_text = textpage.get_text_range()
                
                extracted_text += f"\\n\\n--- PAGE {page_num + 1} ---\\n\\n"
                extracted_text += page_text
                
                textpage.close()
                page.close()
            
            pdf.close()
            
            processing_time = time.time() - start_time
            text_length = len(extracted_text.strip())
            word_count = len(extracted_text.split())
            
            return {
                "method": "pypdfium2",
                "success": True,
                "text": extracted_text.strip(),
                "text_length": text_length,
                "word_count": word_count,
                "processing_time": round(processing_time, 3),
                "pages_processed": total_pages
            }
            
        except Exception as e:
            return {
                "method": "pypdfium2",
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }
    
    def _choose_best_result(self, results):
        """Choose the best extraction result - your original logic"""
        # Filter successful results
        successful = [r for r in results if r.get("success", False)]
        
        if not successful:
            return None
        
        # Find method with most text
        most_text = max(successful, key=lambda x: x["text_length"])
        
        # If we got substantial text (>100 chars), use that
        if most_text["text_length"] > 100:
            return most_text
        
        # Otherwise, use fastest method with decent text
        fastest = min(successful, key=lambda x: x["processing_time"])
        if fastest["text_length"] > 50:
            return fastest
        
        # Last resort: first successful method
        return successful[0]
    
    def _preprocess_german_text(self, raw_text):
        """Advanced preprocessing for German text - your original method"""
        if not raw_text or not raw_text.strip():
            return ""
        
        logger.info("Preprocessing German text...")
        
        # Step 1: Remove page separators added during extraction
        text = re.sub(r'\\n\\n--- PAGE \\d+ ---\\n\\n', '\\n\\n', raw_text)
        
        # Step 2: Normalize line endings
        text = text.replace('\\r\\n', '\\n').replace('\\r', '\\n')
        
        # Step 3: Remove excessive whitespace
        text = re.sub(r' +', ' ', text)
        text = re.sub(r'\\t+', ' ', text)
        
        # Step 4: Handle excessive line breaks
        text = re.sub(r'\\n\\s*\\n\\s*\\n+', '\\n\\n', text)
        
        # Step 5: Remove page headers/footers
        page_patterns = [
            r'Seite \\d+ von \\d+',
            r'Page \\d+ of \\d+',
            r'\\d+\\s*/\\s*\\d+',
            r'Stand: \\d{2}\\.\\d{2}\\.\\d{4}',
            r'Ausgedruckt am \\d{2}\\.\\d{2}\\.\\d{4}'
        ]
        
        for pattern in page_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        # Step 6: Clean up German-specific OCR errors
        german_corrections = {
            'ä': 'ä', 'ö': 'ö', 'ü': 'ü', 'ß': 'ß',
            'ae': 'ä', 'oe': 'ö', 'ue': 'ü', 'ss': 'ß',
            'Ae': 'Ä', 'Oe': 'Ö', 'Ue': 'Ü',
        }
        
        for wrong, correct in german_corrections.items():
            text = text.replace(wrong, correct)
        
        # Step 7: Fix PDF extraction artifacts
        text = re.sub(r'-\\s*\\n\\s*', '', text)
        text = re.sub(r'\\s*\\n\\s*([a-z])', r' \\1', text)
        
        # Step 8: Handle German business document formatting
        text = re.sub(r'VR\\s+(\\d+)', r'VR \\1', text)
        text = re.sub(r'HRB\\s+(\\d+)', r'HRB \\1', text)
        text = re.sub(r'HRA\\s+(\\d+)', r'HRA \\1', text)
        
        # Step 9: Remove repeated punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[-]{3,}', '---', text)
        text = re.sub(r'[_]{3,}', '___', text)
        
        # Step 10: Final cleanup
        lines = [line.strip() for line in text.split('\\n')]
        
        cleaned_lines = []
        prev_empty = False
        
        for line in lines:
            if line:
                cleaned_lines.append(line)
                prev_empty = False
            elif not prev_empty:
                cleaned_lines.append('')
                prev_empty = True
        
        cleaned_text = '\\n'.join(cleaned_lines).strip()
        
        original_length = len(raw_text)
        cleaned_length = len(cleaned_text)
        reduction_percent = round(((original_length - cleaned_length) / original_length) * 100, 1) if original_length > 0 else 0
        
        logger.info(f"Text cleaning: {original_length} → {cleaned_length} chars ({reduction_percent}% reduction)")
        
        return cleaned_text

# Test function
def test_pdf_processor():
    """Test the PDF processor"""
    processor = PDFProcessor()
    
    # Test with a sample PDF file
    test_file = "test.pdf"  # Replace with actual test file
    
    if os.path.exists(test_file):
        result = processor.process_pdf(test_file)
        
        if result["success"]:
            print(f"✅ Processing successful")
            print(f"Method: {result['method']}")
            print(f"Words: {result['stats']['word_count']}")
            print(f"Time: {result['stats']['processing_time']}s")
            print(f"Sample text: {result['cleaned_text'][:200]}...")
        else:
            print(f"❌ Processing failed: {result['error']}")
    else:
        print(f"Test file {test_file} not found")

if __name__ == "__main__":
    test_pdf_processor()