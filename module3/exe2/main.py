import re
import tiktoken
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentProcessor:
    def __init__(
        self,
        model_encoding: str = "cl100k_base",
        chunk_size: int = 500,
        chunk_overlap: int = 100,
    ):
        self.tokenizer = tiktoken.get_encoding(model_encoding)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self.calculate_tokens,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def clean_text(self, text: str) -> str:
        """Clean the text by removing duplicate spaces and unnecessary line breaks."""
        text = re.sub(r"(?m)^.*Pág\.\s*\d+.*\n?", "", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[^\S\n]+", " ", text)
        text = re.sub(r"■", "", text)
        return text.strip()

    def calculate_tokens(self, text: str) -> int:
        """Count tokens using the tiktoken tokenizer."""
        return len(self.tokenizer.encode(text))

    def process_document(self, raw_text: str) -> List[str]:
        """Pipeline: cleaning, then chunking."""
        cleaned = self.clean_text(raw_text)
        chunks = self.splitter.split_text(cleaned)
        for index, chunk in enumerate(chunks):
            print(f"Chunk {index}: {self.calculate_tokens(chunk)} tokens")
        return chunks

if __name__ == "__main__":
    text = """ACME S.A. — Manual interno — Pág. 1
Política de devoluciones■■
Los clientes pueden devolver un producto dentro de los 30 días    corridos desde la compra, siempre que conserven el ticket.
ACME S.A. — Manual interno — Pág. 2
El reintegro se hace por el mismo medio de pago. Si la compra fue en efectivo, se entrega una nota de crédito.
Envíos
Los envíos dentro de la ciudad demoran 48 horas hábiles. Para el interior del país, el plazo es de 5 a 7 días hábiles y el costo depende del peso del paquete.
ACME S.A. — Manual interno — Pág. 3
Garantía
Todos los productos electrónicos tienen 12 meses de garantía. La garantía no cubre daños por mal uso ni golpes."""

    # The sample text is short, so 40/10 shows where it is cut.
    processor = DocumentProcessor(chunk_size=40, chunk_overlap=10)
    chunks = processor.process_document(text)
    print(f"Chunks generated: {len(chunks)}")
    for index, chunk in enumerate(chunks):
        print(f"--- {index} ---\n{chunk}")
