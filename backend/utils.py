"""
Utility Functions for PDF Parsing Project
"""

import os
import re
import logging
import time
from pathlib import Path

def setup_logging():
    """Setup logging configuration for the application"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/german_processor.log'),
            logging.StreamHandler()
        ]
    )

    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")

def create_safe_filename(filename):
    """Create safe filename for file system"""
    # Remove or replace unsafe characters
    safe_name = re.sub(r'[^\w\-_.]', '_', filename)

    # Ensure reasonable length
    if len(safe_name) > 100:
        name_part = safe_name[:80]
        ext_part = safe_name[-10:]
        safe_name = name_part + ext_part

    # Add timestamp if needed to ensure uniqueness
    if not safe_name:
        safe_name = f"document_{int(time.time())}"

    return safe_name

def format_file_size(size_bytes):
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"

    size_names = ["B", "KB", "MB", "GB"]
    import math

    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)

    return f"{s} {size_names[i]}"

def validate_company_name(company_name):
    """Validate company name input"""
    if not company_name or not company_name.strip():
        return False, "Company name cannot be empty"

    if len(company_name.strip()) < 3:
        return False, "Company name must be at least 3 characters"

    if len(company_name.strip()) > 200:
        return False, "Company name too long (max 200 characters)"

    # Check for suspicious patterns
    suspicious_patterns = [
        r'[<>"\'{}]',  # HTML/script injection
        r'\.\./',      # Path traversal
        r'[\x00-\x1f]'  # Control characters
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, company_name):
            return False, "Company name contains invalid characters"

    return True, "Valid company name"

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

    return text.strip()

def ensure_directory_exists(directory):
    """Ensure a directory exists, create if not"""
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to create directory {directory}: {e}")
        return False

def get_file_info(filepath):
    """Get file information"""
    try:
        if not os.path.exists(filepath):
            return None

        stat_info = os.stat(filepath)
        return {
            'size': stat_info.st_size,
            'size_formatted': format_file_size(stat_info.st_size),
            'modified': stat_info.st_mtime,
            'created': stat_info.st_ctime,
            'is_readable': os.access(filepath, os.R_OK),
            'is_writable': os.access(filepath, os.W_OK)
        }
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to get file info for {filepath}: {e}")
        return None

def sanitize_html(text):
    """Basic HTML sanitization"""
    if not text:
        return ""

    # Remove potential HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Escape special characters
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#x27;",
        ">": "&gt;",
        "<": "&lt;",
    }

    for char, escape in html_escape_table.items():
        text = text.replace(char, escape)

    return text

# Test function
def test_utils():
    """Test utility functions"""
    print("Testing utility functions...")

    # Test filename sanitization
    test_filename = "test file with spaces & special chars!@#.pdf"
    safe_filename = create_safe_filename(test_filename)
    print(f"Original: {test_filename}")
    print(f"Safe: {safe_filename}")

    # Test company name validation
    test_names = ["BMW", "A", "", "Deutsche Bank AG", "Test<script>alert('xss')</script>"]
    for name in test_names:
        valid, message = validate_company_name(name)
        print(f"'{name}': {'✅' if valid else '❌'} - {message}")

    # Test file size formatting
    sizes = [0, 1024, 1024*1024, 1024*1024*1024]
    for size in sizes:
        formatted = format_file_size(size)
        print(f"{size} bytes = {formatted}")

if __name__ == "__main__":
    test_utils()
