# Active Context

## Current Phase
**Phase 3: LiteLLM Client Module** - Completed. LiteLLM client wrapper is implemented and tested.

## Recent Decisions
- Using LiteLLM as the universal LLM abstraction layer (not direct API calls)
- Ollama Mistral as the default local LLM provider
- Local file storage (JSON/Markdown) instead of database
- JSearch API for job aggregation
- Weighted scoring algorithm for job matching
- Python 3.8+ compatibility for type hints (using `Union` instead of `|`)
- Implemented a provider-agnostic `LiteLLMClient` that centralizes all LLM calls
- Configured disk cache usage at `.cache/litellm` based on config settings
- Added request retries/timeouts and pass-through fallback model routing via LiteLLM
- Added token/cost usage tracking for each completion call

## Open Questions
- None currently - following the architecture as defined

## Next Steps (Phase 4: Storage Manager Module)
1. Create `src/storage.py` with `StorageManager` class
2. Implement JSON and Markdown profile save/load methods
3. Implement history append/read with duplicate detection
4. Implement resume backup copy support into `data/resumes`
5. Add atomic write handling for file safety
6. Add tests for profile/history/resume backup storage operations

## Architecture Notes
- All LLM calls must go through LiteLLM
- LLM provider changes should require only configuration updates, not code changes
- API keys must be stored in environment variables, never in code
- Single-user CLI application (no authentication needed)

## Completed Work (Phase 2)
- Created `src/resume_parser.py` with ResumeParser class
- Supports PDF parsing via pdfplumber
- Supports DOCX parsing via python-docx
- Unified interface with proper error handling
- 14 unit tests passing
- Integrated with main.py for profile mode

## Completed Work (Phase 3)
- Created `src/llm_client.py` with `LiteLLMClient` class
- Implemented `completion()` wrapper over `litellm.completion()`
- Added configuration-driven model, timeout, retries, api_base, and fallbacks
- Added disk cache configuration support via LiteLLM cache API
- Added usage/cost tracking via `get_last_usage()`
- Added runtime model inspection via `get_model_info()`
- Added 9 unit tests in `tests/test_llm_client.py`