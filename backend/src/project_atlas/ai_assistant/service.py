from dataclasses import dataclass
from uuid import UUID

from project_atlas.ai_assistant.prompts import SYSTEM_PROMPT, build_user_prompt
from project_atlas.ai_assistant.providers import LLMProvider
from project_atlas.models import Project
from project_atlas.rag.providers import EmbeddingProvider, EmbeddingProviderError
from project_atlas.rag.retrieval import retrieve_chunks


@dataclass(frozen=True)
class AnswerSource:
    number: int
    chunk_id: str
    document_id: str
    filename: str
    page_number: int | None
    excerpt: str
    score: float


@dataclass(frozen=True)
class AssistantAnswer:
    content: str
    sources: list[AnswerSource]


def answer_project_question(
    project: Project,
    question: str,
    embedding_provider: EmbeddingProvider,
    llm_provider: LLMProvider,
    history: list[dict[str, str]],
) -> AssistantAnswer:
    try:
        chunks = retrieve_chunks(UUID(str(project.id)), question, embedding_provider, limit=5)
    except EmbeddingProviderError:
        chunks = []
    prompt = build_user_prompt(project, question, chunks, history)
    content = llm_provider.generate(SYSTEM_PROMPT, prompt)
    sources = [
        AnswerSource(
            number=index,
            chunk_id=str(item.chunk.id),
            document_id=str(item.document.id),
            filename=item.document.filename,
            page_number=item.chunk.page_number,
            excerpt=item.chunk.content[:320],
            score=round(item.score, 6),
        )
        for index, item in enumerate(chunks, start=1)
    ]
    return AssistantAnswer(content=content, sources=sources)
