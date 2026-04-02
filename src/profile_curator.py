"""
Profile Curator Module
Handles the profile curation mode workflow.
"""

import os
import shutil
from typing import Optional
from datetime import datetime

from .resume_parser import parse_resume, clean_text, get_resume_info
from .llm_client import LLMClient
from .storage import save_profile, save_profile_json


class ProfileCurator:
    """
    Handles the profile curation workflow including resume parsing,
    LLM analysis, and interactive Q&A.
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the profile curator.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.llm = LLMClient(config_path)
        self.profile = {}
        self.resume_text = ""
        self.resume_analysis = {}
    
    def process_resume(self, resume_path: str) -> dict:
        """
        Process a resume file and extract information.
        
        Args:
            resume_path: Path to the resume file
            
        Returns:
            Dictionary with extracted resume information
        """
        print(f"\n📄 Processing resume: {resume_path}")
        
        # Get file info
        file_info = get_resume_info(resume_path)
        print(f"   Format: {file_info['format']}")
        print(f"   Size: {file_info['size_kb']} KB")
        
        # Parse resume
        print("   Parsing resume content...")
        self.resume_text = parse_resume(resume_path)
        self.resume_text = clean_text(self.resume_text)
        
        if not self.resume_text.strip():
            raise ValueError("Resume appears to be empty after parsing")
        
        print(f"   Extracted {len(self.resume_text)} characters")
        
        # Save resume copy
        self._save_resume_copy(resume_path)
        
        # Analyze with LLM
        print("   Analyzing resume with AI...")
        self.resume_analysis = self.llm.analyze_resume(self.resume_text)
        
        # Store in profile
        self.profile = self.resume_analysis.copy()
        
        print("   ✅ Resume analysis complete!")
        return self.resume_analysis
    
    def _save_resume_copy(self, resume_path: str):
        """Save a copy of the resume to the data directory."""
        resumes_dir = "data/resumes"
        os.makedirs(resumes_dir, exist_ok=True)
        
        filename = os.path.basename(resume_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_filename = f"{timestamp}_{filename}"
        dest_path = os.path.join(resumes_dir, new_filename)
        
        shutil.copy2(resume_path, dest_path)
        print(f"   Saved resume copy to: {dest_path}")
    
    def get_job_type_suggestions(self, num_suggestions: int = 7) -> list:
        """
        Get job type suggestions based on the resume analysis.
        
        Args:
            num_suggestions: Number of suggestions to generate
            
        Returns:
            List of job type suggestions
        """
        print("\n🎯 Generating job type suggestions...")
        
        suggestions = self.llm.suggest_job_types(self.profile, num_suggestions)
        
        if not suggestions:
            print("   ⚠️  Could not generate suggestions. Please try again.")
            return []
        
        print(f"   ✅ Generated {len(suggestions)} suggestions:\n")
        
        for i, suggestion in enumerate(suggestions, 1):
            confidence_emoji = {
                'high': '🟢',
                'medium': '🟡',
                'low': '🔴'
            }.get(suggestion.get('confidence', '').lower(), '⚪')
            
            print(f"   {i}. {confidence_emoji} {suggestion.get('title', 'Unknown')}")
            print(f"      {suggestion.get('reason', '')}")
            print()
        
        return suggestions
    
    def select_job_types(self, suggestions: list, max_selections: int = 3) -> list:
        """
        Interactive selection of job types.
        
        Args:
            suggestions: List of job type suggestions
            max_selections: Maximum number of job types to select
            
        Returns:
            List of selected job types
        """
        print(f"\n📋 Select up to {max_selections} job types (enter numbers separated by commas)")
        print("   Example: 1, 3, 5\n")
        
        selected = []
        
        while len(selected) < max_selections:
            try:
                user_input = input(f"   Your selection{f' ({len(selected)} selected so far)' if selected else ''}: ").strip()
                
                if not user_input:
                    if selected:
                        break
                    print("   Please select at least one job type.")
                    continue
                
                # Parse selection
                selections = [int(x.strip()) for x in user_input.split(',')]
                
                for sel in selections:
                    if 1 <= sel <= len(suggestions):
                        job_title = suggestions[sel - 1].get('title', '')
                        if job_title not in selected:
                            selected.append(job_title)
                            if len(selected) >= max_selections:
                                break
                    else:
                        print(f"   ⚠️  Invalid selection: {sel}")
                
                if len(selected) < max_selections:
                    remaining = max_selections - len(selected)
                    print(f"   Selected: {', '.join(selected)}")
                    print(f"   You can select {remaining} more job type(s).")
                    
            except ValueError:
                print("   ⚠️  Please enter valid numbers (e.g., 1, 3, 5)")
        
        self.profile['selected_job_types'] = selected
        
        print(f"\n   ✅ Selected job types: {', '.join(selected)}")
        return selected
    
    def ask_profile_questions(self) -> dict:
        """
        Generate and ask profile completion questions.
        
        Returns:
            Dictionary with user's answers
        """
        print("\n❓ Answer a few questions to complete your profile:\n")
        
        # Generate questions
        questions = self.llm.generate_profile_questions(self.resume_analysis)
        
        answers = {}
        
        # Default questions if LLM doesn't generate any
        if not questions:
            questions = [
                "What is your preferred work environment? (remote, hybrid, onsite)",
                "What are your location preferences? (city, country, or 'flexible')",
                "What are your salary expectations? (range or 'negotiable')",
                "What industry are you most interested in?",
                "What is your preferred company size? (startup, mid-size, enterprise)",
                "What are your career goals for the next 2-3 years?",
                "What skills would you like to develop in your next role?"
            ]
        
        preferences = {}
        
        for i, question in enumerate(questions, 1):
            try:
                answer = input(f"   {i}. {question}\n      Answer: ").strip()
                
                if not answer:
                    answer = "Not specified"
                
                # Categorize answers into preferences
                question_lower = question.lower()
                if 'work environment' in question_lower or 'remote' in question_lower:
                    preferences['work_environment'] = answer
                elif 'location' in question_lower:
                    preferences['location_preferences'] = answer
                elif 'salary' in question_lower:
                    preferences['salary_expectations'] = answer
                elif 'industry' in question_lower:
                    preferences['industry_preferences'] = answer
                elif 'company size' in question_lower:
                    preferences['company_size_preference'] = answer
                elif 'career goals' in question_lower:
                    preferences['career_goals'] = answer
                elif 'skills' in question_lower or 'develop' in question_lower:
                    preferences['skills_to_develop'] = answer
                else:
                    answers[question] = answer
                    
            except EOFError:
                break
        
        self.profile['preferences'] = preferences
        self.profile['additional_answers'] = answers
        
        print("\n   ✅ Profile questions completed!")
        return {'preferences': preferences, 'answers': answers}
    
    def review_profile(self) -> bool:
        """
        Display the complete profile for review.
        
        Returns:
            True if user confirms, False otherwise
        """
        print("\n📄 Review your profile:\n")
        print("=" * 60)
        
        # Personal Info
        pi = self.profile.get('personal_info', {})
        print(f"Name: {pi.get('name', 'Not specified')}")
        print(f"Email: {pi.get('email', 'Not specified')}")
        print(f"Location: {pi.get('location', 'Not specified')}")
        
        # Professional Summary
        ps = self.profile.get('professional_summary', {})
        print(f"\nExperience: {ps.get('years_of_experience', 'Not specified')} years")
        print(f"Current Role: {ps.get('current_role', 'Not specified')}")
        
        # Selected Job Types
        job_types = self.profile.get('selected_job_types', [])
        print(f"\nSelected Job Types: {', '.join(job_types)}")
        
        # Skills
        ts = self.profile.get('technical_skills', {})
        all_skills = []
        for category, skills in ts.items():
            if skills:
                all_skills.extend(skills)
        print(f"Key Skills: {', '.join(all_skills[:10])}{'...' if len(all_skills) > 10 else ''}")
        
        # Preferences
        pref = self.profile.get('preferences', {})
        if pref:
            print("\nPreferences:")
            for key, value in pref.items():
                print(f"  - {key.replace('_', ' ').title()}: {value}")
        
        print("=" * 60)
        
        try:
            confirm = input("\n✅ Save this profile? (yes/no): ").strip().lower()
            return confirm in ['yes', 'y']
        except EOFError:
            return True  # Auto-confirm if running non-interactively
    
    def save_profile(self, profile_path: str = "data/profile.md") -> str:
        """
        Save the profile to disk.
        
        Args:
            profile_path: Path to save the profile
            
        Returns:
            Path where profile was saved
        """
        print(f"\n💾 Saving profile to {profile_path}...")
        
        # Save as Markdown
        save_profile(self.profile, profile_path)
        
        # Also save as JSON for easy programmatic access
        json_path = profile_path.replace('.md', '.json')
        save_profile_json(self.profile, json_path)
        
        print(f"   ✅ Profile saved successfully!")
        print(f"      Markdown: {profile_path}")
        print(f"      JSON: {json_path}")
        
        return profile_path
    
    def run(self, resume_path: str) -> dict:
        """
        Run the complete profile curation workflow.
        
        Args:
            resume_path: Path to the resume file
            
        Returns:
            Complete profile dictionary
        """
        print("\n" + "=" * 60)
        print("   JOB SEARCH AGENT - PROFILE CURATION MODE")
        print("=" * 60)
        
        # Step 1: Process resume
        self.process_resume(resume_path)
        
        # Step 2: Get job type suggestions
        suggestions = self.get_job_type_suggestions()
        
        if not suggestions:
            print("\n⚠️  Could not generate job suggestions. Exiting.")
            return {}
        
        # Step 3: Select job types
        self.select_job_types(suggestions)
        
        # Step 4: Ask profile questions
        self.ask_profile_questions()
        
        # Step 5: Review and confirm
        if not self.review_profile():
            print("\n❌ Profile not saved. Exiting.")
            return {}
        
        # Step 6: Save profile
        self.save_profile()
        
        print("\n" + "=" * 60)
        print("   ✅ PROFILE CURATION COMPLETE!")
        print("=" * 60)
        print("\nYou can now run the job search mode to find matching jobs.")
        print("Run: python -m src.main --mode search\n")
        
        return self.profile