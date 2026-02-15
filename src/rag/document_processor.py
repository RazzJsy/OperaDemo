import os
from typing import List, Dict, Any
from dataclasses import dataclass
import pdfplumber
from pathlib import Path


@dataclass
class DocumentChunk:
    text: str
    source: str
    page: int
    chunk_id: int
    metadata: Dict[str, Any]
    
    def __repr__(self):
        return f"Chunk(source={self.source}, page={self.page}, chars={len(self.text)})"


class DocumentProcessor:
    """
    Processes PDF documents into semantically meaningful chunks
    
    Strategy:
    1. Extract text with page/structure preservation
    2. Chunk with overlap for context continuity
    3. Enrich with metadata for better retrieval
    """
    
    def __init__(
        self, 
        chunk_size: int = 800,
        chunk_overlap: int = 200
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
    def process_pdf(self, pdf_path: str) -> List[DocumentChunk]:
        """
        Extract and chunk a PDF document
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of DocumentChunk objects
        """
        print(f"\nProcessing: {os.path.basename(pdf_path)}")
        
        chunks = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                print(f"   Pages: {total_pages}")
                
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    
                    if not text:
                        continue
                    
                    text = self._clean_text(text)
                    
                    page_chunks = self._create_chunks(
                        text=text,
                        source=os.path.basename(pdf_path),
                        page=page_num
                    )
                    
                    chunks.extend(page_chunks)
                
                print(f"   Created {len(chunks)} chunks")
                
        except Exception as e:
            print(f"   Error processing PDF: {e}")
            
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        text = " ".join(text.split())
        text = text.replace("\x00", "")
        
        return text.strip()
    
    def _create_chunks(
        self, 
        text: str, 
        source: str, 
        page: int
    ) -> List[DocumentChunk]:
        """
        Create overlapping chunks from text
        
        Overlap strategy: Helps small models maintain context across chunks
        """
        chunks = []
        start = 0
        chunk_id = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            if end < len(text):
                last_period = chunk_text.rfind('. ')
                last_newline = chunk_text.rfind('\n')
                
                break_point = max(last_period, last_newline)
                if break_point > self.chunk_size - 200:
                    chunk_text = chunk_text[:break_point + 1]
                    end = start + len(chunk_text)
            
            chunk = DocumentChunk(
                text=chunk_text.strip(),
                source=source,
                page=page,
                chunk_id=chunk_id,
                metadata={
                    "char_start": start,
                    "char_end": end,
                    "chunk_length": len(chunk_text)
                }
            )
            
            chunks.append(chunk)
            chunk_id += 1
            
            start = end - self.chunk_overlap
            
            if start >= len(text) or end >= len(text):
                break
        
        return chunks
    
    def process_directory(self, directory: str) -> List[DocumentChunk]:
        """
        Process all PDFs in a directory
        
        Args:
            directory: Path to directory containing PDFs
            
        Returns:
            Combined list of chunks from all documents
        """
        all_chunks = []
        pdf_files = list(Path(directory).glob("*.pdf"))
        
        print(f"\nProcessing directory: {directory}")
        print(f"   Found {len(pdf_files)} PDF files")
        
        for pdf_path in pdf_files:
            chunks = self.process_pdf(str(pdf_path))
            all_chunks.extend(chunks)
        
        print(f"\nTotal chunks created: {len(all_chunks)}")
        
        return all_chunks
