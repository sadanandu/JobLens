# Job Search Agent - Development Plan

## Project Overview

The Job Search Agent is a CLI-based application that analyzes user resumes, curates profiles with AI assistance, and performs daily job searches with intelligent matching. The system uses LiteLLM as a universal LLM abstraction layer, currently configured with Ollama's Mistral model, with future support for Anthropic, OpenAI, and other providers through configuration only.

## Tech Stack Summary

| Category | Technology | Version/Notes |
|----------|------------|---------------|
| **Language** | Python | 3.8+ |
| **CLI Framework** | argparse | Built-in Python |
| **Resume Parsing** | pdfplumber, python-docx | Latest stable |
| **LLM Client** | litellm | Universal LLM library with routing, caching, fallbacks |
| **Job API** | requests | For JSearch API |
| **Configuration** | PyYAML | For config files |
| **Data Storage** | JSON, Markdown | Local files |
| **Caching** | LiteLLM built-in | SQLite or disk-based cache |

## Dependencies (requirements.txt)

```
litellm>=1.40.0
pdfplumber>=0.10.0
python-docx>=1.0.0
pyyaml>=6.0
requests>=2.31.0
python-dotenv>=1.0.0
```

## Configuration Examples

### LiteLLM Configuration (config/config.yaml)

```yaml
# LLM Configuration via LiteLLM
llm:
  # Primary model (LiteLLM format: provider/model-name)
  model: "ollama/mistral"
  
  # Ollama-specific settings
  api_base: "http://localhost:11434"
  
  # LiteLLM advanced features
  caching: true
  caching_ttl: 3600  # Cache time-to-live in seconds
  
  # Retry configuration
  num_retries: 3
  request_timeout: 30
  
  # Fallback models (optional)
  fallbacks: []
    # Example: 
    # - model: "ollama/llama2"
    #   api_base: "http://localhost:11434"
  
  # Cost tracking (enabled even for local models)
  input_cost_per_token: 0.0
  output_cost_per_token: 0.0

  # Future provider examples (uncomment and configure when needed):
  # Anthropic:
  # model: "anthropic/claude-3-sonnet-20240229"
  # api_key: "${ANTHROPIC_API_KEY}"
  
  # OpenAI:
  # model: "openai/gpt-4-turbo"
  # api_key: "${OPENAI_API_KEY}"

# Job Search Configuration
jsearch:
  api_key: "${JSEARCH_API_KEY}"
  base_url: "https://jsearch.p.rapidapi.com"

# Matching Weights
matching:
  weights:
    skills: 0.35
    experience: 0.25
    job_type: 0.20
    location: 0.10
    industry: 0.10

# Storage Configuration
storage:
  profile_dir: "data"
  history_dir: "data"
  resume_backup_dir: "data/resumes"
```

### Environment Variables (.env)

```bash
# LLM Provider Keys (for future use)
# ANTHROPIC_API_KEY=your_anthropic_key_here
# OPENAI_API_KEY=your_openai_key_here

# Job Search API
JSEARCH_API_KEY=your_jsearch_key_here

# LiteLLM Configuration (optional overrides)
# LITELLM_MASTER_KEY=your_litellm_key_if_using_proxy
```

## Phased Delivery Plan

### Phase 1: Project Foundation & Configuration

**Goal:** Establish project structure, configuration system, and basic CLI framework.

**Deliverables:**
- Project directory structure
- Configuration system with YAML support
- Basic CLI entry point with argument parsing
- Environment variable handling for API keys
- LiteLLM configuration structure

**Acceptance Criteria:**
- `python -m src.main --help` displays usage information
- Configuration loads from `config/config.yaml`
- API keys read from environment variables
- LiteLLM configuration is loadable and validated
- All directories created automatically on first run

**Files/Components:**
```
JobSearch/
├── config/
│   ├── __init__.py
│   ├── config.yaml           # Includes LiteLLM configuration
│   └── system_prompts.md
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── config_manager.py     # Enhanced for LiteLLM config
├── data/
│   └── .gitkeep
├── .cache/
│   └── .gitkeep              # For LiteLLM caching
├── .env.example
├── requirements.txt
└── README.md
```

---

### Phase 2: Resume Parser Module

**Goal:** Implement resume file parsing for PDF and DOCX formats.

**Deliverables:**
- PDF text extraction using pdfplumber
- DOCX text extraction using python-docx
- Unified parser interface
- Error handling for unsupported formats

**Acceptance Criteria:**
- Parser accepts PDF and DOCX files
- Returns clean extracted text
- Handles multi-page documents
- Graceful error messages for parsing failures

**Files/Components:**
- `src/resume_parser.py` - ResumeParser class with parse(file_path) method

---

### Phase 3: LiteLLM Client Module

**Goal:** Create LiteLLM-based LLM client with routing, caching, fallbacks, and retries.

**Deliverables:**
- LiteLLM integration using `litellm.completion()`
- Configuration-driven model selection
- Caching support (disk-based)
- Fallback model support
- Automatic retry logic
- Cost tracking (even for local models)
- Provider-agnostic interface

**Acceptance Criteria:**
- LLM client uses LiteLLM library exclusively
- Model can be switched via config (e.g., `ollama/mistral` → `anthropic/claude-3-sonnet`)
- Caching reduces redundant API calls
- Fallbacks work when primary model fails
- Retries handle transient failures
- Cost tracking logs token usage
- All LLM calls go through unified interface

**Files/Components:**
- `src/llm_client.py` - LiteLLMClient class wrapping litellm.completion()
- Updates to `config/config.yaml` for LiteLLM settings

**Key Methods:**
```python
class LiteLLMClient:
    def __init__(self, config: dict):
        # Initialize with LiteLLM configuration
        pass
    
    def completion(self, messages: list, **kwargs) -> str:
        # Call litellm.completion() with configured model
        # Apply caching, fallbacks, retries
        # Return response text
        pass

        
    def get_model_info(self) -> dict:
        # Return current model configuration
        pass

```

---

### Phase 4: Storage Manager Module

**Goal:** Implement local file storage for profiles and history.

**Deliverables:**
- JSON and Markdown file writers/readers
- Profile storage (create, read, update)
- History storage (append, read, check duplicates)
- Resume file backup functionality
- LiteLLM cache directory management

**Acceptance Criteria:**
- Profile saved in both JSON and Markdown formats
- History entries appended without duplicates
- Files created automatically if missing
- Atomic write operations to prevent corruption
- Cache directory managed properly

**Files/Components:**
- `src/storage.py` - StorageManager class

---

### Phase 5: Profile Curator Mode

**Goal:** Implement interactive profile curation with AI assistance via LiteLLM.

**Deliverables:**
- Resume text analysis using LiteLLM (Ollama Mistral)
- Structured profile extraction
- Job type suggestions from LLM
- Interactive Q&A for preferences
- Profile persistence

**Acceptance Criteria:**
- `--mode profile --resume <file>` initiates curation
- LLM extracts skills, experience, education via LiteLLM
- User can select up to 3 job types
- Profile saved to disk
- Human-readable profile summary generated

**Files/Components:**
- `src/profile_curator.py` - ProfileCurator class
- `config/system_prompts.md` - Profile extraction prompts

---

### Phase 6: Job Searcher Module

**Goal:** Implement job search functionality using JSearch API.

**Deliverables:**
- JSearch API client
- Search by job type, location, filters
- Response parsing and normalization
- Rate limit handling

**Acceptance Criteria:**
- Searches jobs by job type
- Filters by date posted, employment type
- Returns structured job data
- Handles API errors and rate limits

**Files/Components:**
- `src/job_api.py` - JSearchClient class

---

### Phase 7: Matcher Engine

**Goal:** Implement job-profile matching with weighted scoring and LiteLLM enhancement.

**Deliverables:**
- Weighted scoring algorithm
- Skills matching (keyword + semantic)
- Experience level matching
- Location preference matching
- LLM-enhanced match analysis via LiteLLM

**Acceptance Criteria:**
- Calculates match score (0-100%)
- Configurable weight parameters
- Provides match breakdown by category
- Uses LiteLLM for semantic analysis

**Files/Components:**
- `src/matcher.py` - MatcherEngine class
- Updates to `config/config.yaml` for weights

---

### Phase 8: Job Search Mode & Integration

**Goal:** Complete job search mode and integrate all components.

**Deliverables:**
- Job search CLI mode
- Load profile and execute search
- Rank jobs by match score
- Display top 3 results
- Update history to prevent duplicates

**Acceptance Criteria:**
- `--mode search` executes job search
- Loads saved profile
- Shows 3 jobs with URLs and match scores
- History updated after each search
- No duplicate jobs shown

**Files/Components:**
- `src/job_searcher.py` - JobSearcher class
- Updates to `src/main.py` for search mode

---

### Phase 9: LiteLLM Features Integration

**Goal:** Implement advanced LiteLLM features for production robustness.

**Deliverables:**
- Caching configuration and management
- Fallback model configuration
- Retry logic with exponential backoff
- Cost tracking and reporting
- Model switching validation

**Acceptance Criteria:**
- Cache reduces redundant LLM calls
- Fallbacks activate on primary model failure
- Retries handle transient errors gracefully
- Cost tracking reports token usage
- Model can be switched via config without code changes

**Files/Components:**
- Updates to `src/llm_client.py` for advanced features
- Updates to `config/config.yaml` for feature configuration
- `src/cache_manager.py` - Optional cache management utilities

---

### Phase 10: Polish & Documentation

**Goal:** Final polish, error handling, and documentation.

**Deliverables:**
- Comprehensive error handling
- User-friendly messages
- Updated README with Ollama setup instructions
- LiteLLM configuration guide
- Troubleshooting guide

**Acceptance Criteria:**
- All error paths handled gracefully
- Clear instructions in README for Ollama setup
- LiteLLM configuration examples provided
- CLI help text complete and accurate
- Sample configuration provided

**Files/Components:**
- Updates to `README.md`
- Updates to all modules for error handling
- `docs/LLM_CONFIGURATION.md` - Guide for LLM provider setup

---

## Key Constraints

1. **No External Dependencies Beyond Specified:** Only use libraries listed in requirements.txt
2. **Environment Variables for Secrets:** API keys must never be hardcoded
3. **Backward Compatible Config:** New config options should have defaults
4. **Single User Focus:** No multi-user or concurrent access support needed
5. **CLI Only:** No GUI or web interface
6. **LiteLLM for All LLM Calls:** All LLM interactions must go through LiteLLM
7. **Configuration-Driven Provider Selection:** LLM provider changes must not require code changes
8. **Ollama User Responsibility:** Users must install and configure Ollama themselves

## File Structure Reference

```
JobSearch/
├── config/
│   ├── __init__.py
│   ├── config.yaml           # Main configuration with LiteLLM settings
│   └── system_prompts.md     # LLM system prompts
├── data/
│   ├── .gitkeep
│   ├── profile.json          # Created after profile setup
│   ├── profile.md            # Created after profile setup
│   ├── history.json          # Created after first search
│   ├── history.md            # Created after first search
│   └── resumes/              # Resume backups
├── .cache/
│   └── litellm/              # LiteLLM response cache (optional)
├── src/
│   ├── __init__.py
│   ├── main.py               # CLI entry point
│   ├── config_manager.py     # Configuration handling (including LiteLLM)
│   ├── resume_parser.py      # Resume parsing
│   ├── llm_client.py         # LiteLLM client wrapper
│   ├── storage.py            # File storage
│   ├── profile_curator.py    # Profile curation mode
│   ├── job_api.py            # JSearch API client
│   ├── job_searcher.py       # Job search mode
│   └── matcher.py            # Matching engine
├── .env.example              # Example environment variables
├── requirements.txt
└── README.md
```

## LLM Provider Migration Path

### Current State (Ollama Mistral)
```yaml
llm:
  model: "ollama/mistral"
  api_base: "http://localhost:11434"
```

### Future: Anthropic Claude
```yaml
llm:
  model: "anthropic/claude-3-sonnet-20240229"
  api_key: "${ANTHROPIC_API_KEY}"
```

### Future: OpenAI GPT-4
```yaml
llm:
  model: "openai/gpt-4-turbo"
  api_key: "${OPENAI_API_KEY}"
```

**Note:** No code changes required—only configuration updates.

## Testing Strategy

### Unit Tests
- Resume parser with various file formats
- Configuration loading and validation
- Storage operations (read/write)
- Matcher scoring algorithm

### Integration Tests
- LiteLLM client with mock Ollama responses
- End-to-end profile curation flow
- End-to-end job search flow

### Manual Testing
- Ollama integration with actual Mistral model
- Configuration switching between providers
- Caching and fallback behavior
- Error handling for LLM failures

## References

- [Requirements Document](requirements.md)
- [Architecture Design](architecture.md)
- [LiteLLM Documentation](https://docs.litellm.ai/)
- [Ollama Documentation](https://ollama.com/)