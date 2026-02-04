"""
LLM Provider Abstraction Layer

Supports multiple LLM providers:
- OpenAI (GPT-4, GPT-3.5)
- Ollama (local models)
- Custom API (customer-provided endpoints)

Usage:
    from llm_provider import get_llm, LLMProvider

    # Use default provider (from env)
    llm = get_llm()

    # Use specific provider
    llm = get_llm(provider=LLMProvider.OPENAI)

    # Use custom API
    llm = get_llm(provider=LLMProvider.CUSTOM, custom_base_url="https://api.customer.com")
"""

import os
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json
import time
import requests

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    OLLAMA = "ollama"
    CUSTOM = "custom"  # Customer-provided API


@dataclass
class LLMConfig:
    """Configuration for LLM provider"""
    provider: LLMProvider
    model: str
    temperature: float = 0
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    timeout: int = 60
    json_mode: bool = False


class CustomAPIWrapper(BaseChatModel):
    """
    Wrapper for custom/customer-provided APIs.
    Implements LangChain's BaseChatModel interface.
    """

    base_url: str = ""
    api_key: str = ""
    model: str = "default"
    temperature: float = 0
    timeout: int = 60
    json_mode: bool = False

    class Config:
        arbitrary_types_allowed = True

    @property
    def _llm_type(self) -> str:
        return "custom_api"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> ChatResult:
        """Generate response from custom API"""

        # Convert LangChain messages to API format
        api_messages = []
        for msg in messages:
            if isinstance(msg, SystemMessage):
                api_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                api_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                api_messages.append({"role": "assistant", "content": msg.content})

        # Prepare request payload (OpenAI-compatible format)
        payload = {
            "model": self.model,
            "messages": api_messages,
            "temperature": self.temperature,
        }

        if self.json_mode:
            payload["response_format"] = {"type": "json_object"}

        if stop:
            payload["stop"] = stop

        # Make API request
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()

            # Extract content from response
            content = result["choices"][0]["message"]["content"]

            return ChatResult(
                generations=[ChatGeneration(message=AIMessage(content=content))]
            )

        except requests.exceptions.Timeout:
            return ChatResult(
                generations=[ChatGeneration(
                    message=AIMessage(content='{"error": "API timeout - request took too long"}')
                )]
            )
        except requests.exceptions.RequestException as e:
            return ChatResult(
                generations=[ChatGeneration(
                    message=AIMessage(content=f'{{"error": "API request failed: {str(e)}"}}')
                )]
            )
        except (KeyError, IndexError) as e:
            return ChatResult(
                generations=[ChatGeneration(
                    message=AIMessage(content=f'{{"error": "Invalid API response format: {str(e)}"}}')
                )]
            )


# Global configuration - can be overridden
_current_provider: Optional[LLMProvider] = None
_current_config: Optional[LLMConfig] = None


def get_provider_from_env() -> LLMProvider:
    """Get LLM provider from environment variable"""
    provider_str = os.getenv("LLM_PROVIDER", "ollama").lower()

    if provider_str == "openai":
        return LLMProvider.OPENAI
    elif provider_str == "custom":
        return LLMProvider.CUSTOM
    else:
        return LLMProvider.OLLAMA


def get_llm(
    provider: Optional[LLMProvider] = None,
    model: Optional[str] = None,
    temperature: float = 0,
    json_mode: bool = False,
    custom_base_url: Optional[str] = None,
    custom_api_key: Optional[str] = None
) -> BaseChatModel:
    """
    Get LLM instance for the specified provider.

    Args:
        provider: LLM provider (OpenAI, Ollama, Custom). Defaults to env LLM_PROVIDER.
        model: Model name. Defaults to provider-specific default.
        temperature: Temperature for generation. Defaults to 0.
        json_mode: Whether to request JSON output format.
        custom_base_url: Base URL for custom API.
        custom_api_key: API key for custom API.

    Returns:
        LangChain chat model instance
    """

    # Use provided provider or get from env
    if provider is None:
        provider = get_provider_from_env()

    if provider == LLMProvider.OPENAI:
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        model_name = model or os.getenv("OPENAI_MODEL", "gpt-4o")

        kwargs = {
            "model": model_name,
            "temperature": temperature,
            "api_key": api_key,
        }

        if json_mode:
            kwargs["model_kwargs"] = {"response_format": {"type": "json_object"}}

        return ChatOpenAI(**kwargs)

    elif provider == LLMProvider.OLLAMA:
        from langchain_ollama import ChatOllama

        model_name = model or os.getenv("OLLAMA_MODEL", "gpt-oss:latest")

        kwargs = {
            "model": model_name,
            "temperature": temperature,
        }

        if json_mode:
            kwargs["format"] = "json"

        return ChatOllama(**kwargs)

    elif provider == LLMProvider.CUSTOM:
        base_url = custom_base_url or os.getenv("CUSTOM_API_BASE_URL")
        api_key = custom_api_key or os.getenv("CUSTOM_API_KEY", "")
        model_name = model or os.getenv("CUSTOM_MODEL", "default")

        if not base_url:
            raise ValueError("Custom API base URL not provided")

        return CustomAPIWrapper(
            base_url=base_url,
            api_key=api_key,
            model=model_name,
            temperature=temperature,
            json_mode=json_mode
        )

    else:
        raise ValueError(f"Unknown provider: {provider}")


def set_default_provider(provider: LLMProvider):
    """Set the default LLM provider globally"""
    global _current_provider
    _current_provider = provider
    os.environ["LLM_PROVIDER"] = provider.value


def get_current_provider() -> LLMProvider:
    """Get the current LLM provider"""
    global _current_provider
    if _current_provider is None:
        _current_provider = get_provider_from_env()
    return _current_provider


def get_provider_info() -> Dict[str, Any]:
    """Get information about current provider configuration"""
    provider = get_current_provider()

    info = {
        "provider": provider.value,
        "provider_name": provider.name,
    }

    if provider == LLMProvider.OPENAI:
        info["model"] = os.getenv("OPENAI_MODEL", "gpt-4o")
        info["api_key_set"] = bool(os.getenv("OPENAI_API_KEY"))
    elif provider == LLMProvider.OLLAMA:
        info["model"] = os.getenv("OLLAMA_MODEL", "gpt-oss:latest")
        info["base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    elif provider == LLMProvider.CUSTOM:
        info["model"] = os.getenv("CUSTOM_MODEL", "default")
        info["base_url"] = os.getenv("CUSTOM_API_BASE_URL", "not set")
        info["api_key_set"] = bool(os.getenv("CUSTOM_API_KEY"))

    return info


# Convenience function for testing
def test_provider(provider: LLMProvider, test_prompt: str = "Say 'Hello' in JSON format: {\"response\": \"...\"}") -> Dict[str, Any]:
    """
    Test a provider with a simple prompt.

    Returns dict with:
        - success: bool
        - response: str (if successful)
        - error: str (if failed)
        - latency_ms: float
    """
    start_time = time.time()

    try:
        llm = get_llm(provider=provider, json_mode=True)
        response = llm.invoke([HumanMessage(content=test_prompt)])
        latency_ms = (time.time() - start_time) * 1000

        return {
            "success": True,
            "response": response.content,
            "latency_ms": round(latency_ms, 2),
            "provider": provider.value
        }
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        return {
            "success": False,
            "error": str(e),
            "latency_ms": round(latency_ms, 2),
            "provider": provider.value
        }
