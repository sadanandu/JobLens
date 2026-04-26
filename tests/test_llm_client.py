#!/usr/bin/env python3
"""Tests for LiteLLMClient module."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.llm_client import LiteLLMClient


def build_config(**overrides):
    """Build baseline LLM config for tests."""
    config = {
        "model": "ollama/mistral",
        "api_base": "http://localhost:11434",
        "caching": True,
        "caching_ttl": 3600,
        "num_retries": 3,
        "request_timeout": 30,
        "fallbacks": [{"model": "ollama/llama2", "api_base": "http://localhost:11434"}],
        "input_cost_per_token": 0.001,
        "output_cost_per_token": 0.002,
    }
    config.update(overrides)
    return config


def build_response(content="hello", prompt_tokens=10, completion_tokens=5):
    """Build fake LiteLLM completion response."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        ),
    )


class TestLiteLLMClient(unittest.TestCase):
    """Unit tests for LiteLLMClient."""

    def test_init_raises_when_model_missing(self):
        """Client should fail fast when model config is not provided."""
        with self.assertRaisesRegex(
            ValueError,
            "Missing required LLM model configuration",
        ):
            LiteLLMClient(config={})

    def test_init_enables_disk_cache_when_caching_true(self):
        """Client should configure LiteLLM disk cache from config."""
        with patch("src.llm_client.litellm.Cache") as mock_cache:
            with patch("src.llm_client.litellm.disable_cache") as mock_disable_cache:
                LiteLLMClient(build_config(caching=True, caching_ttl=120))

        mock_cache.assert_called_once_with(
            type="disk",
            disk_cache_dir=".cache/litellm",
            ttl=120.0,
        )
        mock_disable_cache.assert_not_called()

    def test_init_disables_cache_when_caching_false(self):
        """Client should disable LiteLLM cache when caching config is false."""
        with patch("src.llm_client.litellm.disable_cache") as mock_disable_cache:
            with patch("src.llm_client.litellm.Cache") as mock_cache:
                LiteLLMClient(build_config(caching=False))

        mock_disable_cache.assert_called_once()
        mock_cache.assert_not_called()

    def test_completion_returns_text_and_tracks_usage(self):
        """Completion should return text and store token/cost usage."""
        fake_response = build_response(content="generated response")

        with patch("src.llm_client.litellm.Cache"):
            with patch("src.llm_client.litellm.completion", return_value=fake_response):
                client = LiteLLMClient(build_config())
                result = client.completion(
                    messages=[{"role": "user", "content": "hi"}]
                )

        self.assertEqual(result, "generated response")
        self.assertEqual(
            client.get_last_usage(),
            {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
                "input_cost": 0.01,
                "output_cost": 0.01,
                "total_cost": 0.02,
            },
        )

    def test_completion_passes_expected_litellm_kwargs(self):
        """Completion should pass configured routing and retry settings."""
        fake_response = build_response(content="ok")

        with patch("src.llm_client.litellm.Cache"):
            with patch(
                "src.llm_client.litellm.completion",
                return_value=fake_response,
            ) as mock_completion:
                client = LiteLLMClient(build_config())
                client.completion(
                    messages=[{"role": "user", "content": "hello"}],
                    temperature=0.2,
                )

        kwargs = mock_completion.call_args.kwargs
        self.assertEqual(kwargs["model"], "ollama/mistral")
        self.assertEqual(kwargs["api_base"], "http://localhost:11434")
        self.assertEqual(kwargs["num_retries"], 3)
        self.assertEqual(kwargs["timeout"], 30)
        self.assertEqual(
            kwargs["fallbacks"],
            [{"model": "ollama/llama2", "api_base": "http://localhost:11434"}],
        )
        self.assertEqual(kwargs["temperature"], 0.2)

    def test_completion_raises_for_invalid_response_shape(self):
        """Completion should raise RuntimeError for malformed response."""
        malformed_response = SimpleNamespace(choices=[])

        with patch("src.llm_client.litellm.Cache"):
            with patch(
                "src.llm_client.litellm.completion",
                return_value=malformed_response,
            ):
                client = LiteLLMClient(build_config())
                with self.assertRaisesRegex(
                    RuntimeError,
                    "Invalid response format from LiteLLM",
                ):
                    client.completion(messages=[{"role": "user", "content": "hello"}])

    def test_completion_raises_for_empty_response_text(self):
        """Completion should raise RuntimeError if content is empty."""
        fake_response = build_response(content="")

        with patch("src.llm_client.litellm.Cache"):
            with patch("src.llm_client.litellm.completion", return_value=fake_response):
                client = LiteLLMClient(build_config())
                with self.assertRaisesRegex(
                    RuntimeError,
                    "LiteLLM returned an empty response",
                ):
                    client.completion(messages=[{"role": "user", "content": "hello"}])

    def test_completion_sets_zero_usage_when_usage_missing(self):
        """Completion should set usage to zero if usage metadata is absent."""
        fake_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok"))]
        )

        with patch("src.llm_client.litellm.Cache"):
            with patch("src.llm_client.litellm.completion", return_value=fake_response):
                client = LiteLLMClient(build_config())
                result = client.completion(
                    messages=[{"role": "user", "content": "hello"}]
                )

        self.assertEqual(result, "ok")
        self.assertEqual(
            client.get_last_usage(),
            {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "input_cost": 0.0,
                "output_cost": 0.0,
                "total_cost": 0.0,
            },
        )

    def test_get_model_info_returns_runtime_configuration(self):
        """Model info should expose active runtime LLM settings."""
        with patch("src.llm_client.litellm.Cache"):
            client = LiteLLMClient(build_config())

        model_info = client.get_model_info()
        self.assertEqual(model_info["model"], "ollama/mistral")
        self.assertEqual(model_info["api_base"], "http://localhost:11434")
        self.assertTrue(model_info["caching"])
        self.assertEqual(model_info["caching_ttl"], 3600)
        self.assertEqual(model_info["num_retries"], 3)
        self.assertEqual(model_info["request_timeout"], 30)


if __name__ == "__main__":
    unittest.main()
