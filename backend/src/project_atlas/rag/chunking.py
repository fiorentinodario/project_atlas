import re
from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    content: str
    page_number: int
    token_count: int


class TokenChunker:
    def __init__(self, chunk_size: int = 600, overlap: int = 80) -> None:
        if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
            raise ValueError("Invalid chunking configuration")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[TextChunk]:
        chunks: list[TextChunk] = []
        for page_number, page in enumerate(text.split("\f"), start=1):
            # Lexical tokens keep chunking deterministic and fully offline. Exact
            # provider tokenization remains the provider's responsibility.
            tokens = re.findall(r"\S+\s*", page.strip())
            start = 0
            while start < len(tokens):
                window = tokens[start : start + self.chunk_size]
                content = "".join(window).strip()
                if content:
                    chunks.append(
                        TextChunk(
                            content=content,
                            page_number=page_number,
                            token_count=len(window),
                        )
                    )
                if start + self.chunk_size >= len(tokens):
                    break
                start += self.chunk_size - self.overlap
        return chunks
