"""PDF processing for meeting transcripts."""
import os
from pathlib import Path
from typing import Dict, List
import PyPDF2
import pdfplumber
from config import Config


class PDFProcessor:
    """Processor for extracting text from PDF transcripts."""
    
    def __init__(self):
        self.transcripts_path = Config.TRANSCRIPTS_RAW
        
    def extract_text_pypdf2(self, pdf_path: Path) -> str:
        """Extract text using PyPDF2 (fast but sometimes misses formatting)."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"PyPDF2 error on {pdf_path.name}: {e}")
        return text
    
    def extract_text_pdfplumber(self, pdf_path: Path) -> str:
        """Extract text using pdfplumber (more accurate, preserves layout better)."""
        text = ""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"pdfplumber error on {pdf_path.name}: {e}")
        return text
    
    def extract_text(self, pdf_path: Path, method: str = 'pdfplumber') -> str:
        """
        Extract text from PDF using specified method.
        
        Args:
            pdf_path: Path to PDF file
            method: 'pdfplumber' (default) or 'pypdf2'
            
        Returns:
            Extracted text as string
        """
        if method == 'pdfplumber':
            return self.extract_text_pdfplumber(pdf_path)
        else:
            return self.extract_text_pypdf2(pdf_path)
    
    def extract_metadata_from_filename(self, filename: str) -> Dict:
        """
        Extract metadata from standardized filename format.
        
        Args:
            filename: e.g., "01-MK-LD-LE.pdf"
            
        Returns:
            Dict with number, attendees
        """
        # Remove .pdf extension
        name = filename.replace('.pdf', '')
        parts = name.split('-')
        
        if len(parts) < 2:
            return {
                'number': 'unknown',
                'attendees': [],
                'filename': filename
            }
        
        number = parts[0]
        attendees = parts[1:]
        
        # Map initials to full names
        name_map = {
            'MK': 'Michael Kianmahd',
            'LD': 'Laura Dolphin',
            'AB': 'Adrian Boerstra',
            'LE': 'Lyndon Elam',
            'KD': 'Kaleb Dague',
            'DK': 'Dave Kaplan'
        }
        
        attendee_names = [name_map.get(a, a) for a in attendees]
        
        return {
            'number': number,
            'attendees': attendee_names,
            'attendee_initials': attendees,
            'filename': filename
        }
    
    def process_all_transcripts(self) -> List[Dict]:
        """
        Process all PDF transcripts in the raw directory.
        
        Returns:
            List of dicts containing filename, metadata, and extracted text
        """
        results = []
        
        pdf_files = sorted(self.transcripts_path.glob('*.pdf'))
        
        if not pdf_files:
            print(f"No PDF files found in {self.transcripts_path}")
            return results
        
        print(f"Processing {len(pdf_files)} transcript PDFs...")
        
        for pdf_path in pdf_files:
            print(f"  Extracting: {pdf_path.name}")
            
            metadata = self.extract_metadata_from_filename(pdf_path.name)
            text = self.extract_text(pdf_path)
            
            results.append({
                'filename': pdf_path.name,
                'metadata': metadata,
                'text': text,
                'text_length': len(text),
                'path': str(pdf_path)
            })
        
        print(f"Extracted text from {len(results)} transcripts")
        return results
    
    def save_extracted_text(self, transcript_data: Dict, output_dir: Path = None):
        """
        Save extracted text to a markdown file.
        
        Args:
            transcript_data: Dict from process_all_transcripts
            output_dir: Output directory (defaults to Config.TRANSCRIPTS_EXTRACTED)
        """
        if output_dir is None:
            output_dir = Config.TRANSCRIPTS_EXTRACTED
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = transcript_data['filename'].replace('.pdf', '.md')
        output_path = output_dir / filename
        
        metadata = transcript_data['metadata']
        
        content = f"""# Meeting Transcript: {metadata['filename']}

**Number:** {metadata['number']}  
**Attendees:** {', '.join(metadata['attendees'])}  
**Length:** {transcript_data['text_length']} characters

---

{transcript_data['text']}
"""
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  Saved: {output_path.name}")
