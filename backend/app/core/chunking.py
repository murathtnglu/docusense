import tiktoken
from typing import List, Dict, Optional
import re

class DocumentChunker:
    """Smart document chunking with semantic awareness"""
    
    def __init__(
        self, 
        chunk_size: int = 800,
        chunk_overlap: int = 200,
        model: str = "cl100k_base"  # tiktoken model
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tiktoken.get_encoding(model)
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))
    
    def chunk_text(self, text: str) -> List[Dict]:
        """
        Smart chunking that tries to respect natural boundaries
        Returns list of chunks with metadata
        """
        # Clean the text
        text = text.strip()
        if not text:
            return []
        
        # Split by paragraphs first (preserve structure)
        paragraphs = re.split(r'\n\n+', text)
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            para_tokens = self.count_tokens(para)
            
            # If single paragraph is too large, split it
            if para_tokens > self.chunk_size:
                # Split by sentences
                sentences = re.split(r'(?<=[.!?])\s+', para)
                for sentence in sentences:
                    sentence_tokens = self.count_tokens(sentence)
                    
                    if current_tokens + sentence_tokens > self.chunk_size:
                        if current_chunk:
                            # Save current chunk
                            chunk_text = ' '.join(current_chunk)
                            chunks.append({
                                'text': chunk_text,
                                'chunk_index': chunk_index,
                                'token_count': current_tokens,
                                'start_char': len(' '.join([c['text'] for c in chunks])),
                                'meta_data': {
                                    'chunk_method': 'sentence_split',
                                    'has_overlap': chunk_index > 0
                                }
                            })
                            chunk_index += 1
                            
                            # Start new chunk with overlap
                            if self.chunk_overlap > 0 and len(current_chunk) > 1:
                                # Keep last few sentences for overlap
                                overlap_text = ' '.join(current_chunk[-2:])
                                overlap_tokens = self.count_tokens(overlap_text)
                                current_chunk = current_chunk[-2:] + [sentence]
                                current_tokens = overlap_tokens + sentence_tokens
                            else:
                                current_chunk = [sentence]
                                current_tokens = sentence_tokens
                    else:
                        current_chunk.append(sentence)
                        current_tokens += sentence_tokens
            else:
                # Paragraph fits in current chunk
                if current_tokens + para_tokens > self.chunk_size:
                    if current_chunk:
                        # Save current chunk
                        chunk_text = ' '.join(current_chunk)
                        chunks.append({
                            'text': chunk_text,
                            'chunk_index': chunk_index,
                            'token_count': current_tokens,
                            'start_char': len(' '.join([c['text'] for c in chunks])),
                            'meta_data': {
                                'chunk_method': 'paragraph_split',
                                'has_overlap': chunk_index > 0
                            }
                        })
                        chunk_index += 1
                        
                        # Start new chunk with overlap
                        if self.chunk_overlap > 0 and current_chunk:
                            overlap_text = current_chunk[-1] if len(current_chunk) > 0 else ""
                            overlap_tokens = self.count_tokens(overlap_text) if overlap_text else 0
                            current_chunk = [overlap_text, para] if overlap_text else [para]
                            current_tokens = overlap_tokens + para_tokens
                        else:
                            current_chunk = [para]
                            current_tokens = para_tokens
                else:
                    current_chunk.append(para)
                    current_tokens += para_tokens
        
        # Don't forget the last chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunks.append({
                'text': chunk_text,
                'chunk_index': chunk_index,
                'token_count': current_tokens,
                'start_char': len(' '.join([c['text'] for c in chunks])),
                'meta_data': {
                    'chunk_method': 'final_chunk',
                    'has_overlap': chunk_index > 0
                }
            })
        
        return chunks
    
    def chunk_markdown(self, text: str) -> List[Dict]:
        """Special handling for markdown documents"""
        # Split by headers
        header_pattern = r'^(#{1,6})\s+(.+)$'
        lines = text.split('\n')
        
        chunks = []
        current_section = []
        current_header = None
        
        for line in lines:
            header_match = re.match(header_pattern, line)
            if header_match:
                # Save previous section
                if current_section:
                    section_text = '\n'.join(current_section)
                    section_chunks = self.chunk_text(section_text)
                    for chunk in section_chunks:
                        chunk['meta_data']['header'] = current_header
                        chunks.append(chunk)
                
                # Start new section
                current_header = header_match.group(2)
                current_section = [line]
            else:
                current_section.append(line)
        
        # Don't forget the last section
        if current_section:
            section_text = '\n'.join(current_section)
            section_chunks = self.chunk_text(section_text)
            for chunk in section_chunks:
                chunk['meta_data']['header'] = current_header
                chunks.append(chunk)
        
        # Reindex chunks
        for i, chunk in enumerate(chunks):
            chunk['chunk_index'] = i
        
        return chunks
    
    def chunk_size_for_document(self, text: str) -> int:
        """Adjust chunk size based on document length"""
        doc_length = len(text)
        if doc_length < 3000:  # Short documents like resumes
            return min(500, doc_length)  # Smaller chunks
        return self.chunk_size  # Default for longer docs