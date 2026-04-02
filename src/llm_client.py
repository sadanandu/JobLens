"""
LLM Client Module
Handles communication with LLM providers (Anthropic Claude and Ollama).
"""

import json
import os
from typing import Any, Optional
import yaml


class LLMClient:
    """Client for interacting with LLM providers (Anthropic Claude and Ollama)."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the LLM client.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.client = None
        self._initialize_client()
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client based on config."""
        provider = self.config.get('llm', {}).get('provider', 'anthropic')
        
        if provider == 'anthropic':
            try:
                import anthropic
                api_key = os.getenv(self.config['llm']['api_key_env'])
                if not api_key:
                    raise ValueError(
                        f"API key not found. Set {self.config['llm']['api_key_env']} "
                        "environment variable."
                    )
                self.client = anthropic.Anthropic(api_key=api_key)
                self.provider = 'anthropic'
            except ImportError:
                raise ImportError(
                    "Anthropic package not installed. Run: pip install anthropic"
                )
        elif provider == 'ollama':
            try:
                import ollama
                self.client = ollama
                self.provider = 'ollama'
                # Verify Ollama server is running by listing models
                try:
                    ollama.list()
                except Exception as e:
                    print(f"Warning: Could not connect to Ollama server: {e}")
                    print("Make sure Ollama is running: ollama serve")
            except ImportError:
                raise ImportError(
                    "Ollama package not installed. Run: pip install ollama"
                )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
    
    def _load_system_prompt(self, prompt_name: str) -> str:
        """
        Load a system prompt from the prompts file.
        
        Args:
            prompt_name: Name of the prompt to load
            
        Returns:
            The prompt text
        """
        prompts_path = self.config.get('storage', {}).get(
            'config_dir', 'config'
        ) + '/system_prompts.md'
        
        if not os.path.exists(prompts_path):
            return ""
        
        with open(prompts_path, 'r') as f:
            content = f.read()
        
        # Simple extraction - find the prompt between markers
        # This is a simplified approach; could be enhanced
        return content
    
    def chat(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Send a chat message to the LLM.
        
        Args:
            user_message: The user's message
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            
        Returns:
            LLM response text
        """
        if self.client is None:
            raise RuntimeError("LLM client not initialized")
        
        llm_config = self.config.get('llm', {})
        
        if self.provider == 'anthropic':
            message = self.client.messages.create(
                model=llm_config.get('model', 'claude-3-5-sonnet-20241022'),
                max_tokens=max_tokens or llm_config.get('max_tokens', 4096),
                temperature=temperature or llm_config.get('temperature', 0.7),
                messages=[
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                system=system_prompt or ""
            )
            return message.content[0].text
        
        elif self.provider == 'ollama':
            model = llm_config.get('model', 'mistral')
            messages = []
            
            # Add system prompt if provided
            if system_prompt:
                messages.append({
                    "role": "system",
                    "content": system_prompt
                })
            
            # Add user message
            messages.append({
                "role": "user",
                "content": user_message
            })
            
            response = self.client.chat(
                model=model,
                messages=messages,
                options={
                    'temperature': temperature or llm_config.get('temperature', 0.7),
                    'num_predict': max_tokens or llm_config.get('max_tokens', 4096),
                }
            )
            
            return response['message']['content']
        
        else:
            raise RuntimeError(f"Unknown provider: {self.provider}")
    
    def chat_with_json(
        self,
        user_message: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Any:
        """
        Send a chat message and parse the response as JSON.
        
        Args:
            user_message: The user's message
            system_prompt: Optional system prompt
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            
        Returns:
            Parsed JSON response
            
        Raises:
            ValueError: If response is not valid JSON
        """
        # Add instruction to return JSON
        enhanced_message = f"""{user_message}

IMPORTANT: Please provide your response as valid JSON. Do not include any explanatory text outside the JSON structure."""
        
        response = self.chat(
            enhanced_message,
            system_prompt,
            temperature,
            max_tokens
        )
        
        # Try to extract JSON from the response
        json_str = self._extract_json(response)
        
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\nResponse: {json_str}")
    
    def _extract_json(self, text: str) -> str:
        """
        Extract JSON from text that may contain markdown or other content.
        
        Args:
            text: Text containing JSON
            
        Returns:
            Extracted JSON string
        """
        import re
        
        # Try to find JSON between ```json and ``` markers
        json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Try to find JSON between ``` and ``` markers
        json_match = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
        if json_match:
            return json_match.group(1)
        
        # Try to find JSON object in the text
        # Look for content between { and }
        start = text.find('{')
        if start != -1:
            end = text.rfind('}')
            if end != -1 and end > start:
                return text[start:end+1]
        
        return text.strip()
    
    def analyze_resume(self, resume_text: str) -> dict:
        """
        Analyze a resume and extract structured information.
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Dictionary with extracted resume information
        """
        system_prompt = """You are an expert career analyst. Analyze the following resume and extract key information.

Please provide a structured analysis with the following sections:

1. **Personal Information**
   - Name
   - Contact (email, phone, location)
   - LinkedIn/GitHub/Portfolio links

2. **Professional Summary**
   - Years of experience
   - Current/most recent role
   - Industry focus

3. **Technical Skills** (list all skills mentioned)
   - Programming languages
   - Frameworks and libraries
   - Tools and platforms
   - Databases
   - Cloud services
   - Other technical skills

4. **Soft Skills** (list all soft skills mentioned or implied)

5. **Work Experience**
   - Company names
   - Roles and titles
   - Duration at each role
   - Key achievements and responsibilities

6. **Education**
   - Degrees
   - Institutions
   - Graduation years
   - Relevant coursework

7. **Certifications**
   - Name of certification
   - Issuing organization
   - Date (if mentioned)

Format the output as valid JSON with the following structure:
{
  "personal_info": {
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "links": {}
  },
  "professional_summary": {
    "years_of_experience": 0,
    "current_role": "",
    "industry_focus": ""
  },
  "technical_skills": {
    "programming_languages": [],
    "frameworks": [],
    "tools": [],
    "databases": [],
    "cloud_services": [],
    "other": []
  },
  "soft_skills": [],
  "work_experience": [
    {
      "company": "",
      "role": "",
      "duration": "",
      "achievements": []
    }
  ],
  "education": [
    {
      "degree": "",
      "institution": "",
      "graduation_year": "",
      "details": ""
    }
  ],
  "certifications": [
    {
      "name": "",
      "organization": "",
      "date": ""
    }
  ]
}"""
        
        user_message = f"Analyze the following resume:\n\nRESUME TEXT:\n{resume_text}"
        
        return self.chat_with_json(user_message, system_prompt)
    
    def suggest_job_types(self, profile_summary: dict, num_suggestions: int = 7) -> list:
        """
        Suggest job types based on a profile analysis.
        
        Args:
            profile_summary: Dictionary with profile information
            num_suggestions: Number of suggestions to generate
            
        Returns:
            List of job type suggestions
        """
        system_prompt = f"""Based on the following profile analysis, suggest {num_suggestions} job types/roles that would be the best fit for this candidate. Consider their skills, experience level, and career trajectory.

For each suggested job type, provide:
1. Job title
2. Why it's a good fit (1-2 sentences)
3. Match confidence (high/medium/low)

Consider roles that are currently in high demand and align with the candidate's background. Include a mix of roles that match their current level and slightly aspirational roles.

Format the output as JSON with the following structure:
{{
  "suggestions": [
    {{
      "title": "Job Title",
      "reason": "Why it's a good fit",
      "confidence": "high/medium/low"
    }}
  ]
}}"""
        
        # Create a summary string from the profile
        summary_parts = []
        if 'professional_summary' in profile_summary:
            ps = profile_summary['professional_summary']
            summary_parts.append(
                f"Experience: {ps.get('years_of_experience', 'N/A')} years"
            )
            if ps.get('current_role'):
                summary_parts.append(f"Current Role: {ps['current_role']}")
            if ps.get('industry_focus'):
                summary_parts.append(f"Industry: {ps['industry_focus']}")
        
        if 'technical_skills' in profile_summary:
            ts = profile_summary['technical_skills']
            all_skills = []
            for category, skills in ts.items():
                if skills:
                    all_skills.extend(skills)
            if all_skills:
                summary_parts.append(f"Key Skills: {', '.join(all_skills[:10])}")
        
        profile_text = "\n".join(summary_parts)
        
        user_message = f"Profile Summary:\n{profile_text}"
        
        result = self.chat_with_json(user_message, system_prompt)
        return result.get('suggestions', [])
    
    def generate_profile_questions(self, resume_analysis: dict) -> list:
        """
        Generate questions to complete the user's profile.
        
        Args:
            resume_analysis: Dictionary with resume analysis
            
        Returns:
            List of questions
        """
        system_prompt = """Based on the following resume analysis, generate 5-7 targeted questions to better understand the candidate's preferences and complete their profile. Focus on information that is NOT already clear from the resume.

Areas to explore:
- Career goals and aspirations
- Preferred work environment (remote, hybrid, onsite)
- Location preferences
- Salary expectations
- Industry preferences
- Company size preferences
- Work-life balance priorities
- Skills they want to develop
- Types of projects they enjoy

Format the output as JSON with the following structure:
{
  "questions": [
    "Question 1?",
    "Question 2?",
    ...
  ]
}"""
        
        # Create a summary of what we already know
        known_info = f"Resume Analysis:\n"
        if 'personal_info' in resume_analysis:
            pi = resume_analysis['personal_info']
            if pi.get('location'):
                known_info += f"- Current Location: {pi['location']}\n"
        
        if 'professional_summary' in resume_analysis:
            ps = resume_analysis['professional_summary']
            known_info += f"- Experience: {ps.get('years_of_experience', 'N/A')} years\n"
            known_info += f"- Current Role: {ps.get('current_role', 'N/A')}\n"
        
        if 'technical_skills' in resume_analysis:
            ts = resume_analysis['technical_skills']
            all_skills = []
            for category, skills in ts.items():
                if skills:
                    all_skills.extend(skills)
            if all_skills:
                known_info += f"- Skills: {', '.join(all_skills[:5])}...\n"
        
        user_message = known_info
        result = self.chat_with_json(user_message, system_prompt)
        return result.get('questions', [])
    
    def analyze_job_description(self, job_description: str) -> dict:
        """
        Analyze a job description and extract requirements.
        
        Args:
            job_description: Raw job description text
            
        Returns:
            Dictionary with extracted requirements
        """
        system_prompt = """Analyze the following job description and extract key requirements.

Please extract:
1. Required Technical Skills (list)
2. Preferred Technical Skills (list)
3. Required Soft Skills (list)
4. Experience Level Required (entry/mid/senior/lead/executive)
5. Years of Experience (range if specified)
6. Education Requirements
7. Industry
8. Job Type/Role Category
9. Location Type (remote/hybrid/onsite)
10. Key Responsibilities (top 5)

Format the output as JSON with the following structure:
{
  "required_technical_skills": [],
  "preferred_technical_skills": [],
  "required_soft_skills": [],
  "experience_level": "mid",
  "years_of_experience": {"min": 0, "max": 0},
  "education_requirements": "",
  "industry": "",
  "job_type": "",
  "location_type": "onsite",
  "key_responsibilities": []
}"""
        
        user_message = f"Analyze the following job description:\n\nJOB DESCRIPTION:\n{job_description}"
        
        return self.chat_with_json(user_message, system_prompt)
    
    def calculate_match_score(self, candidate_profile: dict, job_requirements: dict) -> dict:
        """
        Calculate match score between candidate and job.
        
        Args:
            candidate_profile: Candidate's profile information
            job_requirements: Extracted job requirements
            
        Returns:
            Dictionary with match analysis and score
        """
        system_prompt = """Compare the candidate profile with the job requirements and provide a detailed match analysis.

Provide:
1. Overall Match Score (0-100)
2. Skills Match Analysis
   - Matching skills
   - Missing critical skills
   - Bonus/related skills
3. Experience Match Analysis
   - How candidate's experience aligns
   - Any gaps
4. Strengths (top 3 reasons why this is a good match)
5. Concerns (top 3 potential concerns)
6. Recommendation (strong_yes / yes / maybe / no)

Format the output as JSON with the following structure:
{
  "overall_score": 0,
  "skills_match": {
    "matching_skills": [],
    "missing_skills": [],
    "bonus_skills": [],
    "score": 0
  },
  "experience_match": {
    "analysis": "",
    "score": 0
  },
  "strengths": [],
  "concerns": [],
  "recommendation": "yes"
}"""
        
        # Create profile and job summaries
        profile_summary = self._create_profile_summary(candidate_profile)
        job_summary = self._create_job_summary(job_requirements)
        
        user_message = f"""CANDIDATE PROFILE:
{profile_summary}

JOB REQUIREMENTS:
{job_summary}"""
        
        return self.chat_with_json(user_message, system_prompt)
    
    def _create_profile_summary(self, profile: dict) -> str:
        """Create a text summary of the candidate profile."""
        parts = []
        
        if 'professional_summary' in profile:
            ps = profile['professional_summary']
            parts.append(f"Experience: {ps.get('years_of_experience', 'N/A')} years")
            if ps.get('current_role'):
                parts.append(f"Current Role: {ps['current_role']}")
        
        if 'technical_skills' in profile:
            ts = profile['technical_skills']
            all_skills = []
            for category, skills in ts.items():
                if skills:
                    all_skills.extend(skills)
            if all_skills:
                parts.append(f"Technical Skills: {', '.join(all_skills)}")
        
        if 'soft_skills' in profile and profile['soft_skills']:
            parts.append(f"Soft Skills: {', '.join(profile['soft_skills'])}")
        
        if 'work_experience' in profile:
            exp_summary = []
            for exp in profile['work_experience'][:3]:
                exp_summary.append(f"{exp.get('role', '')} at {exp.get('company', '')}")
            if exp_summary:
                parts.append(f"Experience: {'; '.join(exp_summary)}")
        
        return "\n".join(parts)
    
    def _create_job_summary(self, job: dict) -> str:
        """Create a text summary of job requirements."""
        parts = []
        
        if 'required_technical_skills' in job and job['required_technical_skills']:
            parts.append(f"Required Skills: {', '.join(job['required_technical_skills'])}")
        
        if 'preferred_technical_skills' in job and job['preferred_technical_skills']:
            parts.append(f"Preferred Skills: {', '.join(job['preferred_technical_skills'])}")
        
        if 'experience_level' in job:
            parts.append(f"Experience Level: {job['experience_level']}")
        
        if 'years_of_experience' in job:
            yoe = job['years_of_experience']
            if isinstance(yoe, dict):
                parts.append(f"Years of Experience: {yoe.get('min', 0)}-{yoe.get('max', 0)}")
        
        if 'key_responsibilities' in job and job['key_responsibilities']:
            parts.append(f"Key Responsibilities: {'; '.join(job['key_responsibilities'][:3])}")
        
        return "\n".join(parts)