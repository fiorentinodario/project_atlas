from typing import Protocol

from openai import OpenAI


class LLMProviderError(Exception):
    pass


class LLMProvider(Protocol):
    name: str
    model: str

    def generate(self, system_prompt: str, user_prompt: str) -> str: ...


class DisabledLLMProvider:
    name = "disabled"

    def __init__(self, model: str) -> None:
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        raise LLMProviderError("AI assistant provider is not configured.")


class OpenAILLMProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str) -> None:
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=system_prompt,
                input=user_prompt,
            )
        except Exception as error:
            raise LLMProviderError("AI response generation failed.") from error
        answer = response.output_text.strip()
        if not answer:
            raise LLMProviderError("AI provider returned an empty response.")
        return answer


def build_llm_provider(config: dict) -> LLMProvider:
    provider_name = config["LLM_PROVIDER"]
    model = config["LLM_MODEL"]
    if provider_name == "disabled":
        return DisabledLLMProvider(model)
    if provider_name == "openai":
        api_key = config.get("OPENAI_API_KEY")
        if not api_key:
            return DisabledLLMProvider(model)
        return OpenAILLMProvider(api_key, model)
    raise ValueError(f"Unknown LLM provider: {provider_name}")
