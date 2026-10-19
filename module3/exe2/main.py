import re
import tiktoken
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentProcessor:
    def __init__(self, model_encoding: str = "cl100k_base"):
        # TODO: Inicializar el encoding de tiktoken
        self.tokenizer = None 
        
        # TODO: Configurar RecursiveCharacterTextSplitter
        # Debe usar una función personalizada para medir longitud por TOKENS, no caracteres.
        self.splitter = None

    def clean_text(self, text: str) -> str:
        """Limpia el texto eliminando espacios duplicados y saltos de línea innecesarios."""
        # IMPLEMENTA AQUÍ: Usa regex para limpiar el texto
        return text

    def calculate_tokens(self, text: str) -> int:
        """Calcula la cantidad de tokens usando el tokenizer de tiktoken."""
        # IMPLEMENTA AQUÍ
        return 0

    def process_document(self, raw_text: str) -> List[str]:
        """Pipeline: Limpieza -> Fragmentación."""
        # TODO: 1. Limpiar el texto
        
        # TODO: 2. Aplicar el splitter
        
        # TODO: 3. Retornar los chunks procesados
        return []

if __name__ == "__main__":
    # Texto de prueba
    text = "Tu texto largo aquí..."
    processor = DocumentProcessor()
    chunks = processor.process_document(text)
    print(f"Chunks generados: {len(chunks)}")
