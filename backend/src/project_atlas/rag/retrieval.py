import math
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select

from project_atlas.extensions import db
from project_atlas.models import Document, DocumentChunk
from project_atlas.rag.providers import EmbeddingProvider, EmbeddingProviderError


@dataclass(frozen=True)
class RetrievedChunk:
    chunk: DocumentChunk
    document: Document
    score: float


def _cosine_similarity(left, right: list[float]) -> float:
    left_values = [float(value) for value in left]
    dot = sum(a * b for a, b in zip(left_values, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left_values))
    right_norm = math.sqrt(sum(value * value for value in right))
    return dot / (left_norm * right_norm) if left_norm and right_norm else 0.0


def retrieve_chunks(
    project_id: UUID,
    query: str,
    provider: EmbeddingProvider,
    limit: int = 5,
) -> list[RetrievedChunk]:
    query_embedding = provider.embed([query])[0]
    if len(query_embedding) != provider.dimensions:
        raise EmbeddingProviderError("Embedding provider returned an invalid query vector.")

    statement = (
        select(DocumentChunk, Document)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.project_id == project_id, DocumentChunk.embedding.is_not(None))
    )
    if db.engine.dialect.name == "postgresql":
        distance = DocumentChunk.embedding.cosine_distance(query_embedding)
        rows = db.session.execute(statement.add_columns(distance).order_by(distance).limit(limit))
        return [
            RetrievedChunk(chunk=chunk, document=document, score=max(0.0, 1.0 - float(value)))
            for chunk, document, value in rows
        ]

    candidates = [
        RetrievedChunk(
            chunk=chunk,
            document=document,
            score=_cosine_similarity(chunk.embedding, query_embedding),
        )
        for chunk, document in db.session.execute(statement)
    ]
    return sorted(candidates, key=lambda item: item.score, reverse=True)[:limit]
