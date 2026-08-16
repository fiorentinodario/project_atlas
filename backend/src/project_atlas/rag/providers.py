from typing import Protocol

from openai import OpenAI


class EmbeddingProviderError(Exception):
    pass


class EmbeddingProvider(Protocol):
    dimensions: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class DisabledEmbeddingProvider:
    def __init__(self, dimensions: int) -> None:
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise EmbeddingProviderError("Embedding provider is not configured.")


class OpenAIEmbeddingProvider:
    def __init__(self, api_key: str, model: str, dimensions: int) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.dimensions = dimensions

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts,
                dimensions=self.dimensions,
            )
        except Exception as error:
            raise EmbeddingProviderError("Embedding generation failed.") from error
        ordered = sorted(response.data, key=lambda item: item.index)
        return [item.embedding for item in ordered]


def build_embedding_provider(config: dict) -> EmbeddingProvider:
    provider_name = config["EMBEDDING_PROVIDER"]
    dimensions = config["EMBEDDING_DIMENSIONS"]
    if provider_name == "disabled":
        return DisabledEmbeddingProvider(dimensions)
    if provider_name == "openai":
        api_key = config.get("OPENAI_API_KEY")
        if not api_key:
            return DisabledEmbeddingProvider(dimensions)
        return OpenAIEmbeddingProvider(
            api_key,
            config["EMBEDDING_MODEL"],
            dimensions,
        )
    raise ValueError(f"Unknown embedding provider: {provider_name}")
