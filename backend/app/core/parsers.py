import hashlib
from typing import Dict, Optional
from pypdf import PdfReader
from bs4 import BeautifulSoup
import requests
import markdownify

class DocumentParser:
    """Parse different document types"""
    
    @staticmethod
    def calculate_checksum(content: str) -> str:
        """Calculate SHA256 checksum for deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    @staticmethod
    def parse_pdf(file_path: str) -> Dict:
        """Extract text from PDF"""
        try:
            reader = PdfReader(file_path)
            pages = []
            
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text.strip():
                    pages.append({
                        "page_number": page_num + 1,
                        "text": text
                    })
            
            full_text = "\n\n".join([p["text"] for p in pages])
            
            return {
                "text": full_text,
                "pages": pages,
                "page_count": len(reader.pages),
                "meta_data": {
                    "source_type": "pdf",
                    "page_count": len(reader.pages)
                }
            }
        except Exception as e:
            raise Exception(f"Error parsing PDF: {str(e)}")
    
    
    @staticmethod
    def parse_url(url: str) -> Dict:
        """Extract text from web page"""
        try:
            # Add headers to avoid 403 errors
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n')
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # Get title
            title = soup.find('title')
            title_text = title.string if title else url
            
            return {
                "text": text,
                "title": title_text,
                "meta_data": {
                    "source_type": "url",
                    "url": url
                }
            }
        except Exception as e:
            raise Exception(f"Error parsing URL: {str(e)}")
    
    @staticmethod
    def parse_markdown(content: str) -> Dict:
        """Process markdown content"""
        return {
            "text": content,
            "meta_data": {
                "source_type": "markdown"
            }
        }
    
    @staticmethod
    def parse_text(content: str) -> Dict:
        """Process plain text"""
        content = content.encode('utf-8', errors='ignore').decode('utf-8')
        return {
            "text": content,
            "meta_data": {
                "source_type": "text"
            }
        }