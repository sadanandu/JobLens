# Job Search Agent - Requirements Document

## Problem Statement

Job seekers struggle to find relevant job opportunities that match their skills and experience. Manually searching across multiple job boards is time-consuming and often yields irrelevant results. There is a need for an intelligent agent that can understand a candidate's profile from their resume and automatically surface the most relevant job postings on a daily basis.

## Functional Requirements

1. **Resume Ingestion**
   - FR-1.1: Accept resume files in PDF and DOCX formats
   - FR-1.2: Extract text content from resume files using Python libraries

2. **Profile Analysis**
   - FR-2.1: Parse resume to extract skills, experience, education, and work history
   - FR-2.2: Use LLM via LiteLLM (Ollama Mistral) to analyze profile and suggest relevant job types
   - FR-2.3: Allow user to select up to 3 job types to focus on
   - FR-2.4: Conduct interactive Q&A to gather additional preferences (location, salary, remote/hybrid, etc.)

3. **Profile Persistence**
   - FR-3.1: Save curated profile to local storage in both human-readable (Markdown) and machine-readable (JSON) formats
   - FR-3.2: Load saved profile for subsequent job searches

4. **Job Search**
   - FR-4.1: Search jobs using JSearch API based on selected job types
   - FR-4.2: Filter jobs by date posted, employment type, and location preferences
   - FR-4.3: Retrieve sufficient job listings to enable ranking and selection

5. **Job Matching**
   - FR-5.1: Calculate match score between user profile and job description
   - FR-5.2: Use weighted scoring across multiple dimensions (skills, experience, job type, location, industry)
   - FR-5.3: Use LLM via LiteLLM to enhance matching accuracy through semantic analysis

6. **Results Delivery**
   - FR-6.1: Present top 3 most relevant jobs with URLs and match scores
   - FR-6.2: Display job details including title, company, location, and key matching factors

7. **History Management**
   - FR-7.1: Track all jobs shown to user to avoid duplicates
   - FR-7.2: Store history in local storage for persistence
   - FR-7.3: Use history to improve future recommendations

8. **LLM Configuration**
   - FR-8.1: Support configurable LLM providers via LiteLLM (starting with Ollama Mistral)
   - FR-8.2: Allow model selection within provider (e.g., Mistral via Ollama)
   - FR-8.3: Support environment variable-based API key management for future providers
   - FR-8.4: Support LiteLLM features: caching, fallbacks, retries, and cost tracking
   - FR-8.5: Enable future provider switching (Anthropic, OpenAI) through configuration only

## Non-Functional Requirements

### Scale
- NFR-1: Support individual user scale (single user, local deployment)
- NFR-2: Handle resumes up to 10 pages in length
- NFR-3: Process job search results of 20-50 listings per query

### Latency
- NFR-4: Resume parsing should complete within 10 seconds
- NFR-5: Job search and matching should complete within 30 seconds
- NFR-6: Profile curation interactive session should have sub-second response times for UI elements
- NFR-7: LLM responses via LiteLLM should have configurable timeouts (default: 30 seconds)

### Availability
- NFR-8: CLI should be available for on-demand use
- NFR-9: Graceful degradation when external APIs are unavailable
- NFR-10: LiteLLM fallback mechanisms for LLM failures

### Security
- NFR-11: API keys must be stored in environment variables, never in code or config files
- NFR-12: Resume files should be stored locally with appropriate file permissions
- NFR-13: No personal data should be transmitted to external services beyond what's necessary for API calls

### Maintainability
- NFR-14: Code should be modular with clear separation of concerns
- NFR-15: Configuration should be externalized and easily modifiable
- NFR-16: System prompts should be maintained in separate files for easy iteration
- NFR-17: LLM provider changes should require only configuration updates, not code changes

## Explicit Non-Goals

- NG-1: No graphical user interface (CLI only)
- NG-2: No multi-user support or user authentication
- NG-3: No real-time notifications (user initiates searches)
- NG-4: No automatic application submission
- NG-5: No integration with job seeker's calendar or email
- NG-6: No local LLM model management (Ollama setup is user responsibility)

## Open Questions

- OQ-1: Should the system support multiple resume versions/profiles for the same user?
- OQ-2: Should there be a mechanism to provide feedback on job recommendations to improve future matching?
- OQ-3: Should the system support exporting job listings to formats like CSV for external tracking?
- OQ-4: Should LiteLLM caching be persistent across sessions or in-memory only?

## Key Assumptions

- A-1: User has Ollama installed and running locally with Mistral model pulled
- A-2: User will run the CLI manually or via cron for daily searches
- A-3: JSearch API provides sufficient job coverage for the user's target market
- A-4: Resume text is extractable (not scanned images without OCR)
- A-5: User has Python 3.8+ installed on their system
- A-6: LiteLLM library can successfully interface with Ollama's API
- A-7: Local Mistral model performance is sufficient for resume analysis and job matching tasks