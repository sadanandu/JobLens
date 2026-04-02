"""
Job Searcher Module
Handles the job search mode workflow.
"""

import os
from typing import Optional
from datetime import datetime

from .job_api import JSearchClient
from .llm_client import LLMClient
from .matcher import JobMatcher
from .storage import (
    load_profile,
    save_profile_json,
    save_job_history,
    save_job_history_json,
    get_seen_job_ids,
    load_job_history
)


class JobSearcher:
    """
    Handles the job search workflow including fetching jobs,
    matching with profile, and displaying results.
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the job searcher.
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.job_api = JSearchClient(config_path)
        self.llm = LLMClient(config_path)
        self.matcher = JobMatcher(config_path)
        self.profile = {}
        self.search_history = []
    
    def load_profile(self, profile_path: str = "data/profile.json") -> bool:
        """
        Load the user's profile from disk.
        
        Args:
            profile_path: Path to the profile file
            
        Returns:
            True if profile loaded successfully
        """
        print("\n📄 Loading profile...")
        
        # Try JSON first, then Markdown
        self.profile = load_profile(profile_path)
        
        if not self.profile:
            # Try loading from .md path
            md_path = profile_path.replace('.json', '.md')
            self.profile = load_profile(md_path)
        
        if not self.profile:
            print("   ❌ Profile not found. Please run profile curation mode first.")
            print("      Run: python -m src.main --mode profile")
            return False
        
        # Validate required fields
        if not self.profile.get('selected_job_types'):
            print("   ❌ Profile incomplete. No job types selected.")
            return False
        
        print("   ✅ Profile loaded successfully!")
        print(f"      Name: {self.profile.get('personal_info', {}).get('name', 'N/A')}")
        print(f"      Job Types: {', '.join(self.profile.get('selected_job_types', []))}")
        
        return True
    
    def load_history(self, history_path: str = "data/history.json") -> set:
        """
        Load search history to avoid duplicates.
        
        Args:
            history_path: Path to the history file
            
        Returns:
            Set of seen job IDs
        """
        print("\n📋 Loading search history...")
        
        seen_ids = get_seen_job_ids(history_path)
        self.search_history = load_job_history(history_path)
        
        print(f"   Found {len(seen_ids)} previously seen jobs")
        
        return seen_ids
    
    def search_jobs(self) -> list:
        """
        Search for jobs based on profile.
        
        Returns:
            List of job dictionaries
        """
        print("\n🔍 Searching for jobs...")
        
        job_types = self.profile.get('selected_job_types', [])
        location = self.profile.get('preferences', {}).get('location_preferences', '')
        
        if not job_types:
            print("   ❌ No job types specified in profile")
            return []
        
        print(f"   Searching for: {', '.join(job_types)}")
        if location:
            print(f"   Location: {location}")
        
        # Search for each job type
        all_jobs = []
        
        for job_type in job_types:
            print(f"\n   Searching for '{job_type}'...")
            
            query = job_type
            if location:
                query += f" in {location}"
            
            jobs = self.job_api.search_jobs(
                query=query,
                num_pages=2,
                date_posted="month"
            )
            
            print(f"   Found {len(jobs)} jobs for '{job_type}'")
            all_jobs.extend(jobs)
        
        # Deduplicate
        seen_ids = self.load_history()
        unique_jobs = self.job_api.deduplicate_jobs(all_jobs, seen_ids)
        
        print(f"\n   Total unique jobs: {len(unique_jobs)} (from {len(all_jobs)} total)")
        
        return unique_jobs
    
    def analyze_and_match_jobs(self, jobs: list) -> list:
        """
        Analyze job descriptions and calculate match scores.
        
        Args:
            jobs: List of job dictionaries from API
            
        Returns:
            List of jobs with match results
        """
        print("\n🤖 Analyzing jobs and calculating match scores...")
        
        jobs_with_scores = []
        
        for i, job in enumerate(jobs, 1):
            print(f"\n   [{i}/{len(jobs)}] Analyzing: {job.get('job_title', 'N/A')} at {job.get('company_name', 'N/A')}")
            
            # Extract job info
            job_info = self.job_api.extract_job_info(job)
            
            # Get job description
            description = job.get('job_description', '')
            
            if not description:
                print("   ⚠️  No description available, skipping detailed analysis")
                # Still calculate basic match
                match_result = self.matcher.calculate_match(self.profile, job_info)
                jobs_with_scores.append({
                    'job': job_info,
                    'match_result': match_result
                })
                continue
            
            # Analyze job description with LLM
            try:
                job_requirements = self.llm.analyze_job_description(description)
                
                # Calculate match score
                match_result = self.matcher.calculate_match(
                    self.profile,
                    job_info,
                    job_requirements
                )
                
                # Add analysis details
                match_result['job_requirements'] = job_requirements
                
                print(f"   Match Score: {match_result.get('overall_score', 0)}%")
                
            except Exception as e:
                print(f"   ⚠️  Error analyzing job: {e}")
                # Still calculate basic match
                match_result = self.matcher.calculate_match(self.profile, job_info)
            
            jobs_with_scores.append({
                'job': job_info,
                'match_result': match_result
            })
        
        return jobs_with_scores
    
    def get_top_matches(self, jobs_with_scores: list, top_n: int = 3) -> list:
        """
        Get top matching jobs.
        
        Args:
            jobs_with_scores: List of jobs with match results
            top_n: Number of top jobs to return
            
        Returns:
            List of top matching jobs
        """
        return self.matcher.get_top_jobs(jobs_with_scores, top_n)
    
    def display_results(self, top_jobs: list):
        """
        Display the top job matches.
        
        Args:
            top_jobs: List of top matching jobs
        """
        print("\n" + "=" * 70)
        print("   TOP JOB MATCHES")
        print("=" * 70)
        
        if not top_jobs:
            print("   No matching jobs found.")
            return
        
        for i, item in enumerate(top_jobs, 1):
            job = item['job']
            match = item['match_result']
            
            # Determine emoji based on score
            score = match.get('overall_score', 0)
            if score >= 85:
                emoji = "🟢"
            elif score >= 70:
                emoji = "🟡"
            elif score >= 55:
                emoji = "🟠"
            else:
                emoji = "🔴"
            
            print(f"\n{i}. {emoji} {job.get('job_title', 'N/A')}")
            print(f"   Company: {job.get('company_name', 'N/A')}")
            print(f"   Location: {job.get('job_location', 'N/A')}")
            print(f"   Match Score: {score}%")
            print(f"   URL: {job.get('job_url', 'N/A')}")
            
            # Show matching details
            matching_skills = match.get('matching_skills', [])
            missing_skills = match.get('missing_skills', [])
            
            if matching_skills:
                print(f"   ✅ Matching Skills: {', '.join(matching_skills[:5])}")
            if missing_skills:
                print(f"   ⚠️  Missing Skills: {', '.join(missing_skills[:3])}")
            
            # Recommendation
            recommendation = match.get('recommendation', '')
            rec_emoji = {
                'strong_yes': '👍',
                'yes': '👍',
                'maybe': '🤔',
                'no': '👎'
            }.get(recommendation, '')
            print(f"   Recommendation: {rec_emoji} {recommendation.replace('_', ' ').title()}")
        
        print("\n" + "=" * 70)
    
    def save_results(self, top_jobs: list, history_path: str = "data/history.json"):
        """
        Save search results to history.
        
        Args:
            top_jobs: List of top matching jobs
            history_path: Path to save history
        """
        print("\n💾 Saving search results to history...")
        
        for item in top_jobs:
            job = item['job']
            match = item['match_result']
            
            # Create history entry
            history_entry = {
                'job_id': job.get('job_id', ''),
                'job_title': job.get('job_title', ''),
                'company_name': job.get('company_name', ''),
                'job_location': job.get('job_location', ''),
                'job_url': job.get('job_url', ''),
                'match_score': match.get('overall_score', 0),
                'job_description': job.get('job_description', '')[:1000],
                'matching_skills': match.get('matching_skills', []),
                'missing_skills': match.get('missing_skills', []),
                'recommendation': match.get('recommendation', ''),
                'search_date': datetime.now().isoformat()
            }
            
            # Save to Markdown history
            save_job_history(history_entry, history_path.replace('.json', '.md'))
            
            # Add to history list
            self.search_history.append(history_entry)
        
        # Save JSON history
        save_job_history_json(self.search_history, history_path)
        
        print(f"   ✅ Saved {len(top_jobs)} jobs to history")
    
    def run(self, top_n: int = 3) -> list:
        """
        Run the complete job search workflow.
        
        Args:
            top_n: Number of top jobs to return
            
        Returns:
            List of top matching jobs
        """
        print("\n" + "=" * 60)
        print("   JOB SEARCH AGENT - JOB SEARCH MODE")
        print("=" * 60)
        
        # Step 1: Load profile
        if not self.load_profile():
            return []
        
        # Step 2: Search for jobs
        jobs = self.search_jobs()
        
        if not jobs:
            print("\n⚠️  No jobs found. Try adjusting your search criteria.")
            return []
        
        # Step 3: Analyze and match jobs
        jobs_with_scores = self.analyze_and_match_jobs(jobs)
        
        # Step 4: Get top matches
        top_jobs = self.get_top_matches(jobs_with_scores, top_n)
        
        if not top_jobs:
            print("\n⚠️  No jobs matched your profile sufficiently.")
            return []
        
        # Step 5: Display results
        self.display_results(top_jobs)
        
        # Step 6: Save results
        self.save_results(top_jobs)
        
        print("\n" + "=" * 60)
        print("   ✅ JOB SEARCH COMPLETE!")
        print("=" * 60)
        print(f"\nFound {len(top_jobs)} matching jobs out of {len(jobs)} searched.")
        print("Results saved to data/history.md and data/history.json")
        print("\nRun again tomorrow for fresh job recommendations!\n")
        
        return top_jobs