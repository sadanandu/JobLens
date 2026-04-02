"""
Job API Module
Handles communication with JSearch API for fetching job listings.
"""

import os
import requests
from typing import Any, Optional
import yaml


class JSearchClient:
    """Client for interacting with JSearch API (RapidAPI)."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the JSearch client.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.api_key = None
        self.base_url = None
        self._initialize()
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _initialize(self):
        """Initialize the API client."""
        jsearch_config = self.config.get('jsearch', {})
        self.api_key = os.getenv(jsearch_config.get('api_key_env', 'JSEARCH_API_KEY'))
        self.base_url = jsearch_config.get('base_url', 'https://jsearch.p.rapidapi.com')
        
        if not self.api_key:
            print("Warning: JSearch API key not found. Set JSEARCH_API_KEY environment variable.")
    
    def search_jobs(
        self,
        query: str,
        page: int = 1,
        num_pages: int = 1,
        date_posted: str = "all",
        employment_types: Optional[list] = None,
        job_requirements: Optional[list] = None,
        job_titles: Optional[list] = None,
        company_types: Optional[list] = None,
        categories: Optional[list] = None,
        remote_jobs_only: bool = False,
        exclude_job_publishers: Optional[list] = None,
        radius: Optional[int] = None,
        excluded_tags: Optional[list] = None,
        is_remote: Optional[bool] = None,
        min_salary: Optional[int] = None,
        max_salary: Optional[int] = None,
        experience_level: Optional[str] = None,
        require_uas_residency: bool = False
    ) -> list:
        """
        Search for jobs using JSearch API.
        
        Args:
            query: Search query (e.g., "software engineer in New York")
            page: Page number (starts from 1)
            num_pages: Number of pages to return
            date_posted: Date posted filter ("all", "today", "3days", "week", "month")
            employment_types: List of employment types ("FULLTIME", "PARTTIME", "CONTRACTOR", "INTERN")
            job_requirements: List of job requirements ("under3_years_experience", "mid_level", "senior", etc.)
            job_titles: List of specific job titles to include
            company_types: List of company types ("company", "recruiter", "staffing_agency")
            categories: List of job categories
            remote_jobs_only: Whether to only return remote jobs
            exclude_job_publishers: List of publishers to exclude
            radius: Search radius in miles
            excluded_tags: List of tags to exclude
            is_remote: Filter by remote status
            min_salary: Minimum salary
            max_salary: Maximum salary
            experience_level: Experience level ("entry", "mid", "senior", "director", "executive")
            require_uas_residency: Whether to require US residency
            
        Returns:
            List of job dictionaries
        """
        if not self.api_key:
            print("JSearch API key not configured. Returning empty results.")
            return []
        
        url = f"{self.base_url}/search"
        
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        params = {
            "query": query,
            "page": page,
            "num_pages": num_pages,
        }
        
        # Add optional parameters
        if date_posted and date_posted != "all":
            params["date_posted"] = date_posted
        
        if employment_types:
            params["employment_types"] = ",".join(employment_types)
        
        if job_requirements:
            params["job_requirements"] = ",".join(job_requirements)
        
        if job_titles:
            params["job_titles"] = ",".join(job_titles)
        
        if company_types:
            params["company_types"] = ",".join(company_types)
        
        if categories:
            params["categories"] = ",".join(categories)
        
        if remote_jobs_only:
            params["remote_jobs_only"] = True
        
        if exclude_job_publishers:
            params["exclude_job_publishers"] = ",".join(exclude_job_publishers)
        
        if radius:
            params["radius"] = radius
        
        if excluded_tags:
            params["excluded_tags"] = ",".join(excluded_tags)
        
        if is_remote is not None:
            params["is_remote"] = is_remote
        
        if min_salary:
            params["min_salary"] = min_salary
        
        if max_salary:
            params["max_salary"] = max_salary
        
        if experience_level:
            params["experience_level"] = experience_level
        
        if require_uas_residency:
            params["require_uas_residency"] = True
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'OK':
                return data.get('data', [])
            else:
                print(f"JSearch API error: {data.get('message', 'Unknown error')}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching jobs: {e}")
            return []
    
    def get_job_details(self, job_ids: list) -> list:
        """
        Get detailed information for specific jobs.
        
        Args:
            job_ids: List of job IDs
            
        Returns:
            List of detailed job dictionaries
        """
        if not self.api_key:
            print("JSearch API key not configured. Returning empty results.")
            return []
        
        url = f"{self.base_url}/job-details"
        
        headers = {
            "X-RapidAPI-Key": self.api_key,
            "X-RapidAPI-Host": "jsearch.p.rapidapi.com"
        }
        
        params = {
            "job_id": ",".join(job_ids)
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'OK':
                return data.get('data', [])
            else:
                print(f"JSearch API error: {data.get('message', 'Unknown error')}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching job details: {e}")
            return []
    
    def search_jobs_by_criteria(
        self,
        job_types: list,
        location: Optional[str] = None,
        config: Optional[dict] = None
    ) -> list:
        """
        Search for jobs based on user preferences from config.
        
        Args:
            job_types: List of job types to search for
            location: Optional location filter
            config: Optional config override
            
        Returns:
            List of job dictionaries
        """
        if config is None:
            config = self.config.get('search', {})
        
        # Build search query
        query_parts = job_types[:2]  # Use first 2 job types for query
        if location:
            query_parts.append(location)
        
        query = " OR ".join(query_parts)
        
        # Get search parameters from config
        num_pages = max(1, config.get('api_results_per_query', 20) // 10)
        date_posted_map = {
            1: "today",
            3: "3days",
            7: "week",
            30: "month"
        }
        date_posted_days = config.get('date_posted', 30)
        date_posted = date_posted_map.get(date_posted_days, "month")
        
        employment_types = config.get('employment_types', ["FULLTIME", "CONTRACTOR"])
        
        # Perform search
        jobs = self.search_jobs(
            query=query,
            num_pages=num_pages,
            date_posted=date_posted,
            employment_types=employment_types
        )
        
        return jobs
    
    def filter_jobs_by_location(
        self,
        jobs: list,
        preferred_locations: list,
        is_remote_ok: bool = True
    ) -> list:
        """
        Filter jobs by location preferences.
        
        Args:
            jobs: List of job dictionaries
            preferred_locations: List of preferred locations
            is_remote_ok: Whether remote jobs are acceptable
            
        Returns:
            Filtered list of jobs
        """
        if not preferred_locations and is_remote_ok:
            return jobs
        
        filtered = []
        for job in jobs:
            job_location = job.get('job_location', '').lower()
            job_is_remote = job.get('job_is_remote', False)
            
            # Include remote jobs if allowed
            if job_is_remote and is_remote_ok:
                filtered.append(job)
                continue
            
            # Check if job location matches preferred locations
            for location in preferred_locations:
                if location.lower() in job_location:
                    filtered.append(job)
                    break
        
        return filtered
    
    def deduplicate_jobs(self, jobs: list, seen_ids: set) -> list:
        """
        Remove jobs that have already been seen.
        
        Args:
            jobs: List of job dictionaries
            seen_ids: Set of job IDs already seen
            
        Returns:
            List of new jobs
        """
        return [job for job in jobs if job.get('job_id') not in seen_ids]
    
    def extract_job_info(self, job: dict) -> dict:
        """
        Extract relevant information from a job listing.
        
        Args:
            job: Raw job dictionary from API
            
        Returns:
            Extracted job information
        """
        return {
            'job_id': job.get('job_id', ''),
            'job_title': job.get('job_title', ''),
            'company_name': job.get('company_name', ''),
            'job_location': job.get('job_location', ''),
            'job_type': job.get('job_type', ''),
            'job_url': job.get('job_google_link', job.get('job_apply_link', '')),
            'job_description': job.get('job_description', ''),
            'job_posted_at_timestamp': job.get('job_posted_at_timestamp', 0),
            'job_posted_at_datetime_utc': job.get('job_posted_at_datetime_utc', ''),
            'employer_name': job.get('employer_name', ''),
            'employer_logo': job.get('employer_logo', ''),
            'employer_website': job.get('employer_website', ''),
            'employer_company_type': job.get('employer_company_type', ''),
            'job_salary_is_predicted': job.get('job_salary_is_predicted', False),
            'job_min_salary': job.get('job_min_salary'),
            'job_max_salary': job.get('job_max_salary'),
            'job_salary_currency': job.get('job_salary_currency'),
            'job_salary_period': job.get('job_salary_period', ''),
            'job_required_experience': job.get('job_required_experience', {}),
            'job_required_skills': job.get('job_required_skills', []),
            'job_required_education': job.get('job_required_education', {}),
            'job_experience_in_place_of_education': job.get('job_experience_in_place_of_education', False),
            'job_min_years_of_experience': job.get('job_min_years_of_experience'),
            'job_max_years_of_experience': job.get('job_max_years_of_experience'),
            'job_is_remote': job.get('job_is_remote', False),
            'job_city': job.get('job_city', ''),
            'job_state': job.get('job_state', ''),
            'job_country': job.get('job_country', ''),
        }