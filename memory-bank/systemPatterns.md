# System Patterns

## LLM Access Pattern

- All LLM interactions must go through `src/llm_client.py` (`LiteLLMClient`) instead of direct provider SDK calls.
- `LiteLLMClient.completion()` is the single entry point for chat completion requests.
- Runtime behavior (model, api_base, retries, timeout, fallbacks, caching) is configuration-driven via `config/config.yaml`.
- Cache strategy for current phases uses LiteLLM disk cache at `.cache/litellm`.
- Usage tracking pattern: after each completion, capture prompt/completion/total token counts and estimated input/output/total cost via `get_last_usage()`.
