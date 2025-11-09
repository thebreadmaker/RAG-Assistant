import hashlib
import yaml
from pathlib import Path
from typing import List, Dict
from PyPDF2 import PdfReader
from core.vector_manager import VectorManager
from core.config import get_settings

settings = get_settings()

class DocumentIngester:
    def __init__(self, department: str):
        self.department = department
        self.base_path = Path(__file__).parent.parent.parent
        self.memory_path = self.base_path / "memory"
        self.vector_manager = VectorManager(department)
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        config_path = Path(__file__).parent / "module.yaml"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    def ingest_all(self):
        """Ingest all documents from memory folder"""
        if not self.memory_path.exists():
            self.memory_path.mkdir(parents=True)
            print(f"Created memory folder: {self.memory_path}")
            return
        
        all_chunks = []
        
        for file_path in self.memory_path.glob("*"):
            if file_path.is_file():
                chunks = self._process_file(file_path)
                all_chunks.extend(chunks)
        
        if all_chunks:
            self.vector_manager.ingest(all_chunks)
            print(f"Ingested {len(all_chunks)} chunks from {len(list(self.memory_path.glob('*')))} files")
        else:
            print("No documents found to ingest")
    
    def _process_file(self, file_path: Path) -> List[Dict]:
        """Process a single file based on extension"""
        suffix = file_path.suffix.lower()
        
        if suffix == ".pdf":
            text = self._extract_pdf(file_path)
        elif suffix in [".txt", ".md"]:
            text = self._extract_text(file_path)
        else:
            print(f"Unsupported file type: {suffix}")
            return []
        
        return self._chunk_text(text, str(file_path.name))
    
    def _extract_pdf(self, file_path: Path) -> str:
        """Extract text from PDF"""
        try:
            reader = PdfReader(file_path)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"Error reading PDF {file_path}: {e}")
            return ""
    
    def _extract_text(self, file_path: Path) -> str:
        """Extract text from text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
            return ""
    
    def _chunk_text(self, text: str, source: str) -> List[Dict]:
        """Split text into semantic chunks"""
        chunk_size = self.config.get("chunk_size", settings.chunk_size)
        chunk_overlap = self.config.get("chunk_overlap", settings.chunk_overlap)
        
        # Simple sentence-based chunking
        sentences = text.replace('\n', ' ').split('. ')
        
        chunks = []
        current_chunk = ""
        chunk_idx = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            if len(current_chunk) + len(sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunk_id = self._generate_chunk_id(source, chunk_idx)
                    chunks.append({
                        "id": chunk_id,
                        "text": current_chunk.strip(),
                        "metadata": {
                            "source": source,
                            "department": self.department,
                            "chunk_index": chunk_idx
                        }
                    })
                    chunk_idx += 1
                
                # Start new chunk with overlap
                overlap_text = ". ".join(current_chunk.split(". ")[-2:])
                current_chunk = overlap_text + " " + sentence + ". "
        
        # Add last chunk
        if current_chunk:
            chunk_id = self._generate_chunk_id(source, chunk_idx)
            chunks.append({
                "id": chunk_id,
                "text": current_chunk.strip(),
                "metadata": {
                    "source": source,
                    "department": self.department,
                    "chunk_index": chunk_idx
                }
            })
        
        return chunks
    
    def _generate_chunk_id(self, source: str, index: int) -> str:
        """Generate unique chunk ID"""
        raw_id = f"{self.department}_{source}_{index}"
        return hashlib.md5(raw_id.encode()).hexdigest()

# Singleton for retail_digital
ingester = DocumentIngester("retail_digital")