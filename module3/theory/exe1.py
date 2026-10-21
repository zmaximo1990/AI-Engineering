"""
Spec:

Objetivo: construir un DocumentProcessor que limpie y fragmente texto por tokens, no por caracteres.

Manos a la obra:
Implementá clean_text con regex para eliminar ruido y espacios duplicados.
Configurá RecursiveCharacterTextSplitter con chunk_size=500 y chunk_overlap=50, midiendo con tiktoken.

Resultado: un pipeline de limpieza → fragmentación listo para poblar tu base vectorial.
"""

import re
from typing import List

import tiktoken # use OpenAI tokenizer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Repeated page headers from an extracted PDF.
_PAGE_HEADER = re.compile(r"(?m)^.*Pág\.\s*\d+.*\n?")
# More than one blank line between paragraphs.
_EXTRA_BREAKS = re.compile(r"\n{3,}")
# Repeated spaces and tabs. Line breaks stay so the splitter can cut on paragraphs.
_MULTI_SPACE = re.compile(r"[^\S\n]+")


class DocumentProcessor:
    def __init__(
        self,
        model_encoding: str = "cl100k_base",
        chunk_size: int = 100,
        chunk_overlap: int = 20,
    ):
        self.tokenizer = tiktoken.get_encoding(model_encoding)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=self.calculate_tokens,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def clean_text(self, text: str) -> str:
        """Drop page headers, junk characters, and repeated spaces."""
        text = _PAGE_HEADER.sub("", text)
        text = text.replace("■", "")
        text = _EXTRA_BREAKS.sub("\n\n", text)
        text = _MULTI_SPACE.sub(" ", text)
        return text.strip()

    def calculate_tokens(self, text: str) -> int:
        """Measure the text in tokens."""
        return len(self.tokenizer.encode(text))

    def process_document(self, raw_text: str) -> List[str]:
        """Pipeline: clean the text, then split it into token-sized chunks."""
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

    processor = DocumentProcessor()
    chunks = processor.process_document(text)
    print(f"Chunks generados: {len(chunks)}")
    for index, chunk in enumerate(chunks):
        print(f"--- {index} ---\n{chunk}")
