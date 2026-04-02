# Job Search Agent

An intelligent CLI-based job search agent that analyzes your resume, understands your profile, and finds the most relevant job postings tailored to your skills and preferences.

## Features

- **Resume Parsing**: Upload your resume (PDF/DOCX) and let the AI analyze it
- **Smart Profile Analysis**: AI-powered extraction of skills, experience, and qualifications
- **Job Type Suggestions**: Get personalized job role recommendations based on your profile
- **Daily Job Search**: Find the top 3 most relevant jobs matching your profile
- **Match Scoring**: Comprehensive matching framework with configurable parameters
- **History Tracking**: Keeps track of jobs you've already seen
- **Configurable**: Customize matching weights, preferences, and LLM settings

## Prerequisites

- Python 3.8 or higher
- Anthropic API key (for Claude AI)
- JSearch API key (from RapidAPI)

## Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API keys**:
   ```bash
   # Anthropic API key (get from https://console.anthropic.com/)
   export ANTHROPIC_API_KEY='your-anthropic-api-key'

   # JSearch API key (get from https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)
   export JSEARCH_API_KEY='your-jsearch-api-key'
   ```

   To make these permanent, add them to your shell profile:
   ```bash
   # For bash
   echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.bashrc
   echo 'export JSEARCH_API_KEY="your-key"' >> ~/.bashrc
   source ~/.bashrc

   # For zsh
   echo 'export ANTHROPIC_API_KEY="your-key"' >> ~/.zshrc
   echo 'export JSEARCH_API_KEY="your-key"' >> ~/.zshrc
   source ~/.zshrc
   ```

## Usage

### Step 1: Profile Curation (First Time Setup)

Run the profile curation mode with your resume:

```bash
python -m src.main --mode profile --resume /path/to/your/resume.pdf
```

This will:
1. Parse your resume and extract key information
2. Suggest job types based on your profile
3. Let you select up to 3 job types to focus on
4. Ask you a few questions to complete your profile
5. Save your profile locally

### Step 2: Daily Job Search

Once your profile is set up, run the job search mode:

```bash
python -m src.main --mode search
```

This will:
1. Load your saved profile
2. Search for jobs matching your selected job types
3. Analyze each job and calculate a match score
4. Show you the top 3 most relevant jobs
5. Save the results to history (so you won't see duplicates)

## Configuration

Edit `config/config.yaml` to customize:

### LLM Settings
```yaml
llm:
  provider: "anthropic"
  model: "claude-3-5-sonnet-20241022"  # or claude-3-5-haiku-20241022
  max_tokens: 4096
  temperature: 0.7
```

### Matching Framework
```yaml
matching:
  weights:
    skills: 0.40        # Technical and soft skills match
    experience: 0.25    # Years of experience alignment
    job_type: 0.15      # Role category alignment
    location: 0.10      # Geographic preferences
    industry: 0.10      # Industry alignment
```

### Search Settings
```yaml
search:
  api_results_per_query: 20
  daily_results: 3
  date_posted: 30  # Jobs posted in last X days
  employment_types:
    - "FULLTIME"
    - "CONTRACTOR"
```

## Project Structure

```
JobSearch/
├── config/
│   ├── config.yaml          # Main configuration
│   └── system_prompts.md    # AI system prompts
├── data/
│   ├── profile.md           # Your saved profile (created after setup)
│   ├── profile.json         # JSON version of profile
│   ├── history.md           # Job search history
│   ├── history.json         # JSON version of history
│   └── resumes/             # Saved resume copies
├── src/
│   ├── __init__.py
│   ├── main.py              # CLI entry point
│   ├── resume_parser.py     # Resume parsing (PDF/DOCX)
│   ├── profile_curator.py   # Profile curation mode
│   ├── job_searcher.py      # Job search mode
│   ├── llm_client.py        # Claude API client
│   ├── job_api.py           # JSearch API client
│   ├── matcher.py           # Profile-job matching engine
│   └── storage.py           # File storage utilities
├── requirements.txt
└── README.md
```

## Data Files

### Profile (`data/profile.md` and `data/profile.json`)
Contains your parsed resume information, selected job types, and preferences.

### History (`data/history.md` and `data/history.json`)
Records of jobs that have been shown to you, used to avoid duplicates.

## Troubleshooting

### API Key Issues
If you get errors about missing API keys:
```bash
# Verify keys are set
echo $ANTHROPIC_API_KEY
echo $JSEARCH_API_KEY
```

### Resume Parsing Issues
If your resume fails to parse:
- Ensure it's a valid PDF or DOCX file
- Try converting to a simpler format
- Check that the text is selectable (not scanned images)

### No Jobs Found
If no jobs are found:
- Check your API keys are valid
- Verify your selected job types are common/standard titles
- Try broadening your location preferences

### Rate Limits
- JSearch free tier: 100 requests/month
- Anthropic API: Check your plan limits at console.anthropic.com

## Customization

### Adding Custom Matching Criteria
Edit `config/config.yaml` to adjust matching weights based on your priorities.

### Changing LLM Model
Modify the `model` field in `config/config.yaml`:
- `claude-3-5-sonnet-20241022` (recommended, more capable)
- `claude-3-5-haiku-20241022` (faster, cheaper)

### Modifying System Prompts
Edit `config/system_prompts.md` to customize how the AI analyzes resumes and job descriptions.

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - feel free to use and modify as needed.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your API keys are set correctly
3. Ensure all dependencies are installed: `pip install -r requirements.txt`

---

**Note**: This tool uses external APIs that may have usage limits and costs. Please review the pricing and terms of:
- [Anthropic API](https://www.anthropic.com/pricing)
- [JSearch API on RapidAPI](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)