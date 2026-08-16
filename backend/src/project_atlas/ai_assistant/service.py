from uuid import UUID

from project_atlas.ai_assistant.prompts import SYSTEM_PROMPT, build_user_prompt
from project_atlas.ai_assistant.providers import LLMProvider
from project_atlas.models import Project
from project_atlas.rag.providers import EmbeddingProvider, EmbeddingProviderError
from project_atlas.rag.retrieval import retrieve_chunks


def answer_project_question(
    project: Project,
    question: str,
    embedding_provider: EmbeddingProvider,
    llm_provider: LLMProvider,
    history: list[dict[str, str]],
) -> str:
    try:
        chunks = retrieve_chunks(UUID(str(project.id)), question, embedding_provider, limit=5)
    except EmbeddingProviderError:
        chunks = []
    prompt = build_user_prompt(project, question, chunks, history)
    return llm_provider.generate(SYSTEM_PROMPT, prompt)
