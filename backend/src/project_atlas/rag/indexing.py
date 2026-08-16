from datetime import UTC, datetime

from sqlalchemy import delete, select

from project_atlas.extensions import db
from project_atlas.models import Document, DocumentChunk
from project_atlas.rag.chunking import TokenChunker
from project_atlas.rag.providers import EmbeddingProvider, EmbeddingProviderError


def index_document(
    document: Document,
    provider: EmbeddingProvider,
    *,
    force: bool = False,
    batch_size: int = 64,
) -> None:
    existing_chunks = list(
        db.session.scalars(
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.chunk_index)
        )
    )
    is_fully_indexed = existing_chunks and all(
        chunk.embedding is not None for chunk in existing_chunks
    )
    if is_fully_indexed and not force:
        return

    if force or not existing_chunks:
        db.session.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
        chunks = TokenChunker().chunk(document.extracted_text or "")
        existing_chunks = [
            DocumentChunk(
                document=document,
                chunk_index=index,
                content=chunk.content,
                page_number=chunk.page_number,
                token_count=chunk.token_count,
                chunk_metadata={},
            )
            for index, chunk in enumerate(chunks)
        ]
        db.session.add_all(existing_chunks)
        db.session.commit()

    try:
        for start in range(0, len(existing_chunks), batch_size):
            batch = existing_chunks[start : start + batch_size]
            embeddings = provider.embed([chunk.content for chunk in batch])
            if len(embeddings) != len(batch) or any(
                len(embedding) != provider.dimensions for embedding in embeddings
            ):
                raise EmbeddingProviderError("Embedding provider returned an invalid response.")
            for chunk, embedding in zip(batch, embeddings, strict=True):
                chunk.embedding = embedding
        document.indexed_at = datetime.now(UTC)
        document.indexing_error = None
    except EmbeddingProviderError as error:
        document.indexed_at = None
        document.indexing_error = str(error)
    db.session.commit()
