"""
Matcher Module
Comprehensive profile-job matching engine with configurable parameters.
"""

import os
from typing import Any, Optional
import yaml


class JobMatcher:
    """
    Comprehensive job matching engine that calculates compatibility scores
    between candidate profiles and job requirements.
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the matcher with configuration.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.weights = self.config.get('matching', {}).get('weights', {})
        self.experience_levels = self.config.get('matching', {}).get('experience_levels', {})
        self.skills_config = self.config.get('matching', {}).get('skills', {})
        self.location_config = self.config.get('matching', {}).get('location', {})
    
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            # Return default config if file doesn't exist
            return {
                'matching': {
                    'weights': {
                        'skills': 0.40,
                        'experience': 0.25,
                        'job_type': 0.15,
                        'location': 0.10,
                        'industry': 0.10
                    },
                    'experience_levels': {
                        'entry': {'min_years': 0, 'max_years': 2},
                        'mid': {'min_years': 2, 'max_years': 5},
                        'senior': {'min_years': 5, 'max_years': 10},
                        'lead': {'min_years': 8, 'max_years': 15},
                        'executive': {'min_years': 12, 'max_years': 99}
                    },
                    'skills': {
                        'min_match_percentage': 30,
                        'exact_match_bonus': 1.5,
                        'related_skill_multiplier': 0.7
                    },
                    'location': {
                        'preferred': [],
                        'remote_preference': 'optional',
                        'open_to_relocation': False
                    }
                }
            }
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def calculate_match(
        self,
        candidate_profile: dict,
        job_info: dict,
        job_requirements: Optional[dict] = None
    ) -> dict:
        """
        Calculate comprehensive match score between candidate and job.
        
        Args:
            candidate_profile: Candidate's profile information
            job_info: Job information from API
            job_requirements: Optional pre-analyzed job requirements
            
        Returns:
            Dictionary with match scores and analysis
        """
        # Extract candidate skills
        candidate_skills = self._extract_candidate_skills(candidate_profile)
        
        # Extract job skills
        job_skills = self._extract_job_skills(job_info, job_requirements)
        
        # Calculate individual scores
        skills_score = self._calculate_skills_score(candidate_skills, job_skills)
        experience_score = self._calculate_experience_score(candidate_profile, job_info, job_requirements)
        job_type_score = self._calculate_job_type_score(candidate_profile, job_info)
        location_score = self._calculate_location_score(candidate_profile, job_info)
        industry_score = self._calculate_industry_score(candidate_profile, job_info, job_requirements)
        
        # Calculate weighted overall score
        overall_score = (
            skills_score * self.weights.get('skills', 0.40) +
            experience_score * self.weights.get('experience', 0.25) +
            job_type_score * self.weights.get('job_type', 0.15) +
            location_score * self.weights.get('location', 0.10) +
            industry_score * self.weights.get('industry', 0.10)
        )
        
        # Determine recommendation
        recommendation = self._get_recommendation(overall_score)
        
        return {
            'overall_score': round(overall_score, 1),
            'skills_score': round(skills_score, 1),
            'experience_score': round(experience_score, 1),
            'job_type_score': round(job_type_score, 1),
            'location_score': round(location_score, 1),
            'industry_score': round(industry_score, 1),
            'matching_skills': skills_score.get('matching', []),
            'missing_skills': skills_score.get('missing', []),
            'bonus_skills': skills_score.get('bonus', []),
            'recommendation': recommendation,
            'weights_used': self.weights
        }
    
    def _extract_candidate_skills(self, profile: dict) -> list:
        """Extract all skills from candidate profile."""
        skills = []
        
        technical_skills = profile.get('technical_skills', {})
        for category, skill_list in technical_skills.items():
            if skill_list:
                skills.extend([s.lower().strip() for s in skill_list])
        
        soft_skills = profile.get('soft_skills', [])
        if soft_skills:
            skills.extend([s.lower().strip() for s in soft_skills])
        
        return list(set(skills))
    
    def _extract_job_skills(self, job_info: dict, job_requirements: Optional[dict]) -> dict:
        """Extract skills from job information."""
        required = []
        preferred = []
        
        if job_requirements:
            required = [s.lower().strip() for s in job_requirements.get('required_technical_skills', [])]
            preferred = [s.lower().strip() for s in job_requirements.get('preferred_technical_skills', [])]
        
        # Also check job_info for skills
        if not required and not preferred:
            job_skills = job_info.get('job_required_skills', [])
            if job_skills:
                required = [s.lower().strip() for s in job_skills]
            
            # Try to extract from description
            description = job_info.get('job_description', '').lower()
            if description:
                # Common tech skills to look for
                common_skills = [
                    'python', 'java', 'javascript', 'typescript', 'react', 'node',
                    'sql', 'nosql', 'aws', 'azure', 'gcp', 'docker', 'kubernetes',
                    'git', 'agile', 'scrum', 'machine learning', 'data analysis',
                    'rest api', 'graphql', 'html', 'css', 'angular', 'vue',
                    'spring', 'django', 'flask', 'express', '.net', 'c#',
                    'ruby', 'php', 'swift', 'kotlin', 'go', 'rust', 'scala'
                ]
                
                for skill in common_skills:
                    if skill in description and skill not in required:
                        required.append(skill)
        
        return {
            'required': list(set(required)),
            'preferred': list(set(preferred))
        }
    
    def _calculate_skills_score(self, candidate_skills: list, job_skills: dict) -> dict:
        """Calculate skills match score."""
        required_skills = job_skills.get('required', [])
        preferred_skills = job_skills.get('preferred', [])
        
        if not required_skills and not preferred_skills:
            return {
                'score': 50,  # Neutral score if no skills specified
                'matching': [],
                'missing': [],
                'bonus': []
            }
        
        all_job_skills = required_skills + preferred_skills
        matching = []
        missing = []
        bonus = []
        
        # Check required skills
        for skill in required_skills:
            if skill in candidate_skills:
                matching.append(skill)
            else:
                missing.append(skill)
        
        # Check preferred skills
        for skill in preferred_skills:
            if skill in candidate_skills:
                bonus.append(skill)
            elif skill not in missing:
                missing.append(skill)
        
        # Calculate score
        if all_job_skills:
            # Base score from matching required skills
            required_match = len(matching) / len(required_skills) if required_skills else 1.0
            
            # Bonus for preferred skills
            preferred_match = len(bonus) / len(preferred_skills) if preferred_skills else 0.5
            
            # Apply exact match bonus
            exact_bonus = self.skills_config.get('exact_match_bonus', 1.5)
            related_multiplier = self.skills_config.get('related_skill_multiplier', 0.7)
            
            # Calculate final score
            base_score = (required_match * 0.7 + preferred_match * 0.3) * 100
            
            # Apply bonus for exact matches
            if len(matching) > 0:
                base_score *= exact_bonus
            
            # Normalize to 0-100
            score = min(100, max(0, base_score))
        else:
            score = 50
        
        return {
            'score': round(score, 1),
            'matching': matching,
            'missing': missing,
            'bonus': bonus
        }
    
    def _calculate_experience_score(
        self,
        candidate_profile: dict,
        job_info: dict,
        job_requirements: Optional[dict]
    ) -> float:
        """Calculate experience level match score."""
        candidate_years = candidate_profile.get('professional_summary', {}).get('years_of_experience', 0)
        
        # Get job experience requirements
        min_years = None
        max_years = None
        required_level = None
        
        if job_requirements:
            yoe = job_requirements.get('years_of_experience', {})
            if isinstance(yoe, dict):
                min_years = yoe.get('min')
                max_years = yoe.get('max')
            required_level = job_requirements.get('experience_level')
        
        # Also check job_info
        if min_years is None:
            min_years = job_info.get('job_min_years_of_experience')
        if max_years is None:
            max_years = job_info.get('job_max_years_of_experience')
        
        # If no specific requirements, give moderate score
        if min_years is None and max_years is None and required_level is None:
            return 70.0
        
        # Check if candidate meets minimum requirements
        if min_years is not None and candidate_years < min_years:
            # Candidate has less experience than required
            gap = min_years - candidate_years
            penalty = min(gap * 10, 40)  # Max 40 point penalty
            return max(30, 80 - penalty)
        
        # Check if candidate is overqualified
        if max_years is not None and candidate_years > max_years:
            # Candidate might be overqualified
            over = candidate_years - max_years
            penalty = min(over * 5, 30)  # Max 30 point penalty
            return max(50, 85 - penalty)
        
        # Check experience level match
        if required_level:
            candidate_level = self._get_experience_level(candidate_years)
            level_hierarchy = ['entry', 'mid', 'senior', 'lead', 'executive']
            
            if candidate_level == required_level:
                return 95.0
            elif candidate_level and required_level in level_hierarchy and candidate_level in level_hierarchy:
                candidate_idx = level_hierarchy.index(candidate_level)
                required_idx = level_hierarchy.index(required_level)
                diff = abs(candidate_idx - required_idx)
                return max(50, 90 - diff * 15)
        
        # Good match
        return 85.0
    
    def _get_experience_level(self, years: int) -> Optional[str]:
        """Get experience level based on years of experience."""
        levels = self.experience_levels
        
        for level_name, level_range in levels.items():
            min_years = level_range.get('min_years', 0)
            max_years = level_range.get('max_years', 99)
            
            if min_years <= years < max_years:
                return level_name
        
        return None
    
    def _calculate_job_type_score(self, candidate_profile: dict, job_info: dict) -> float:
        """Calculate job type/role match score."""
        # Get candidate's current/preferred job types
        selected_types = candidate_profile.get('selected_job_types', [])
        current_role = candidate_profile.get('professional_summary', {}).get('current_role', '').lower()
        
        # Get job title
        job_title = job_info.get('job_title', '').lower()
        
        if not selected_types and not current_role:
            return 60.0  # Neutral if no info
        
        # Check if job title matches selected types
        for job_type in selected_types:
            if job_type.lower() in job_title or job_title in job_type.lower():
                return 95.0
        
        # Check for related terms
        related_terms = {
            'software engineer': ['developer', 'programmer', 'software developer', 'engineer', 'sde', 'sse'],
            'data scientist': ['data analyst', 'ml engineer', 'machine learning', 'ai engineer', 'analytics'],
            'product manager': ['product owner', 'program manager', 'project manager', 'product lead'],
            'devops engineer': ['site reliability', 'cloud engineer', 'infrastructure', 'platform engineer'],
            'frontend engineer': ['ui developer', 'web developer', 'frontend developer', 'react developer'],
            'backend engineer': ['api developer', 'server developer', 'database developer'],
            'full stack engineer': ['fullstack', 'web developer', 'application developer']
        }
        
        for job_type in selected_types:
            job_type_lower = job_type.lower()
            terms = related_terms.get(job_type_lower, [job_type_lower])
            
            for term in terms:
                if term in job_title:
                    return 80.0
        
        # Partial match based on industry
        return 50.0
    
    def _calculate_location_score(self, candidate_profile: dict, job_info: dict) -> float:
        """Calculate location match score."""
        # Get candidate preferences
        preferences = candidate_profile.get('preferences', {})
        candidate_location = candidate_profile.get('personal_info', {}).get('location', '')
        
        preferred_locations = preferences.get('location_preferences', [])
        remote_preference = preferences.get('remote_preference', 'optional')
        open_to_relocation = preferences.get('open_to_relocation', False)
        
        # Get job location info
        job_location = job_info.get('job_location', '')
        job_is_remote = job_info.get('job_is_remote', False)
        job_city = job_info.get('job_city', '')
        
        # Perfect match: remote job and candidate wants remote
        if job_is_remote and remote_preference in ['true', True, 'preferred']:
            return 100.0
        
        # Good match: remote job and candidate is okay with remote
        if job_is_remote and remote_preference == 'optional':
            return 85.0
        
        # Check location match
        if preferred_locations:
            for pref_loc in preferred_locations:
                if pref_loc.lower() in job_location.lower() or job_city.lower() in pref_loc.lower():
                    return 95.0
            
            # If candidate is open to relocation, still give moderate score
            if open_to_relocation:
                return 70.0
            
            return 40.0  # Location doesn't match preferences
        
        # If candidate is in same location as job
        if candidate_location and job_location:
            # Simple check for location overlap
            candidate_parts = candidate_location.lower().split(',')
            job_parts = job_location.lower().split(',')
            
            for cp in candidate_parts:
                for jp in job_parts:
                    if cp.strip() in jp.strip() or jp.strip() in cp.strip():
                        return 90.0
        
        return 60.0  # Neutral if no clear match or mismatch
    
    def _calculate_industry_score(
        self,
        candidate_profile: dict,
        job_info: dict,
        job_requirements: Optional[dict]
    ) -> float:
        """Calculate industry match score."""
        # Get candidate industry preferences
        preferences = candidate_profile.get('preferences', {})
        industry_preferences = preferences.get('industry_preferences', [])
        candidate_industry = candidate_profile.get('professional_summary', {}).get('industry_focus', '')
        
        # Get job industry
        job_industry = job_info.get('employer_company_type', '')
        if job_requirements:
            job_industry = job_requirements.get('industry', job_industry)
        
        # If no preferences specified, give moderate score
        if not industry_preferences and not candidate_industry:
            return 70.0
        
        # Check if job industry matches preferences
        if industry_preferences and job_industry:
            for pref_industry in industry_preferences:
                if pref_industry.lower() in job_industry.lower() or job_industry.lower() in pref_industry.lower():
                    return 95.0
        
        # Check if job industry matches candidate's experience
        if candidate_industry and job_industry:
            if candidate_industry.lower() in job_industry.lower() or job_industry.lower() in candidate_industry.lower():
                return 85.0
        
        return 60.0
    
    def _get_recommendation(self, overall_score: float) -> str:
        """Get recommendation based on overall score."""
        if overall_score >= 85:
            return "strong_yes"
        elif overall_score >= 70:
            return "yes"
        elif overall_score >= 55:
            return "maybe"
        else:
            return "no"
    
    def rank_jobs(self, jobs_with_scores: list) -> list:
        """
        Rank jobs by their match scores.
        
        Args:
            jobs_with_scores: List of dicts with 'job' and 'match_result' keys
            
        Returns:
            Sorted list by overall score (descending)
        """
        return sorted(
            jobs_with_scores,
            key=lambda x: x.get('match_result', {}).get('overall_score', 0),
            reverse=True
        )
    
    def get_top_jobs(self, jobs_with_scores: list, top_n: int = 3) -> list:
        """
        Get top N jobs by match score.
        
        Args:
            jobs_with_scores: List of dicts with 'job' and 'match_result' keys
            top_n: Number of top jobs to return
            
        Returns:
            List of top N jobs
        """
        ranked = self.rank_jobs(jobs_with_scores)
        return ranked[:top_n]