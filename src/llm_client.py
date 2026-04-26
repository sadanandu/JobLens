"""LiteLLM client wrapper for provider-agnostic LLM calls."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import litellm


logger = logging.getLogger(__name__)


@dataclass
class CompletionUsage:
    """Token and cost usage details for a completion request."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float


class LiteLLMClient:
    """Configuration-driven LiteLLM client with caching and retries."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize LiteLLM client from validated configuration."""
        self._config = config
        self.model: str = self._config.get("model", "")
        if not self.model:
            raise ValueError("Missing required LLM model configuration")

        self.api_base: Optional[str] = self._config.get("api_base")
        self.caching: bool = bool(self._config.get("caching", False))
        self.caching_ttl: int = int(self._config.get("caching_ttl", 3600))
        self.num_retries: int = int(self._config.get("num_retries", 0))
        self.request_timeout: int = int(self._config.get("request_timeout", 30))
        self.fallbacks: List[Dict[str, Any]] = list(self._config.get("fallbacks", []))
        self.input_cost_per_token: float = float(
            self._config.get("input_cost_per_token", 0.0)
        )
        self.output_cost_per_token: float = float(
            self._config.get("output_cost_per_token", 0.0)
        )

        self._last_usage: Optional[CompletionUsage] = None
        self._configure_cache()

    def _configure_cache(self) -> None:
        """Configure LiteLLM cache based on YAML settings."""
        if self.caching:
            cache_directory = Path(".cache/litellm")
            cache_directory.mkdir(parents=True, exist_ok=True)

            litellm.cache = litellm.Cache(
                type="disk",
                disk_cache_dir=str(cache_directory),
                ttl=float(self.caching_ttl),
            )
            return

        litellm.disable_cache()

    def completion(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        """Execute completion via LiteLLM and return assistant text."""
        request_kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "timeout": kwargs.pop("timeout", self.request_timeout),
            "num_retries": kwargs.pop("num_retries", self.num_retries),
        }

        if self.api_base:
            request_kwargs["api_base"] = self.api_base

        if self.fallbacks:
            request_kwargs["fallbacks"] = self.fallbacks

        request_kwargs.update(kwargs)

        response = litellm.completion(**request_kwargs)
        response_text = self._extract_response_text(response)
        self._track_usage(response)

        return response_text

    def _extract_response_text(self, response: Any) -> str:
        """Extract first message content from LiteLLM response."""
        try:
            text = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            raise RuntimeError("Invalid response format from LiteLLM") from exc

        if not text:
            raise RuntimeError("LiteLLM returned an empty response")

        return str(text)

    def _track_usage(self, response: Any) -> None:
        """Track token usage and estimated cost for latest completion."""
        usage = getattr(response, "usage", None)
        if usage is None:
            self._last_usage = CompletionUsage(
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                input_cost=0.0,
                output_cost=0.0,
                total_cost=0.0,
            )
            logger.info("LLM usage unavailable for this completion")
            return

        prompt_tokens = int(getattr(usage, "prompt_tokens", 0) or 0)
        completion_tokens = int(getattr(usage, "completion_tokens", 0) or 0)
        total_tokens = int(getattr(usage, "total_tokens", 0) or 0)

        input_cost = prompt_tokens * self.input_cost_per_token
        output_cost = completion_tokens * self.output_cost_per_token
        total_cost = input_cost + output_cost

        self._last_usage = CompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            input_cost=input_cost,
            output_cost=output_cost,
            total_cost=total_cost,
        )

        logger.info(
            "LLM usage tokens=%s (prompt=%s, completion=%s), estimated_cost=%.6f",
            total_tokens,
            prompt_tokens,
            completion_tokens,
            total_cost,
        )

    def get_last_usage(self) -> Optional[Dict[str, Any]]:
        """Return usage details from the most recent completion call."""
        if self._last_usage is None:
            return None

        return {
            "prompt_tokens": self._last_usage.prompt_tokens,
            "completion_tokens": self._last_usage.completion_tokens,
            "total_tokens": self._last_usage.total_tokens,
            "input_cost": self._last_usage.input_cost,
            "output_cost": self._last_usage.output_cost,
            "total_cost": self._last_usage.total_cost,
        }

    def get_model_info(self) -> Dict[str, Any]:
        """Return active LiteLLM model and feature configuration."""
        return {
            "model": self.model,
            "api_base": self.api_base,
            "caching": self.caching,
            "caching_ttl": self.caching_ttl,
            "num_retries": self.num_retries,
            "request_timeout": self.request_timeout,
            "fallbacks": self.fallbacks,
        }
