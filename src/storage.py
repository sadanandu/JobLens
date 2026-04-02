"""
Storage Module
Handles reading and writing of profile and history data in Markdown and JSON formats.
"""

import json
import os
from datetime import datetime
from typing import Any, Optional


def ensure_directory(file_path: str):
    """Ensure the directory for a file exists."""
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def save_profile(profile: dict, file_path: str = "data/profile.md"):
    """
    Save user profile to a Markdown file.
    
    Args:
        profile: Profile dictionary
        file_path: Path to save the profile
    """
    ensure_directory(file_path)
    
    markdown = "# User Profile\n\n"
    markdown += f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    
    # Personal Information
    if 'personal_info' in profile:
        pi = profile['personal_info']
        markdown += "## Personal Information\n\n"
        if pi.get('name'):
            markdown += f"**Name:** {pi['name']}\n\n"
        if pi.get('email'):
            markdown += f"**Email:** {pi['email']}\n\n"
        if pi.get('phone'):
            markdown += f"**Phone:** {pi['phone']}\n\n"
        if pi.get('location'):
            markdown += f"**Location:** {pi['location']}\n\n"
        if pi.get('links'):
            markdown += "**Links:**\n"
            for key, value in pi['links'].items():
                markdown += f"- {key}: {value}\n"
            markdown += "\n"
    
    # Professional Summary
    if 'professional_summary' in profile:
        ps = profile['professional_summary']
        markdown += "## Professional Summary\n\n"
        if ps.get('years_of_experience'):
            markdown += f"**Years of Experience:** {ps['years_of_experience']}\n\n"
        if ps.get('current_role'):
            markdown += f"**Current Role:** {ps['current_role']}\n\n"
        if ps.get('industry_focus'):
            markdown += f"**Industry Focus:** {ps['industry_focus']}\n\n"
    
    # Technical Skills
    if 'technical_skills' in profile:
        ts = profile['technical_skills']
        markdown += "## Technical Skills\n\n"
        for category, skills in ts.items():
            if skills:
                category_name = category.replace('_', ' ').title()
                markdown += f"### {category_name}\n\n"
                for skill in skills:
                    markdown += f"- {skill}\n"
                markdown += "\n"
    
    # Soft Skills
    if 'soft_skills' in profile and profile['soft_skills']:
        markdown += "## Soft Skills\n\n"
        for skill in profile['soft_skills']:
            markdown += f"- {skill}\n"
        markdown += "\n"
    
    # Work Experience
    if 'work_experience' in profile:
        markdown += "## Work Experience\n\n"
        for exp in profile['work_experience']:
            markdown += f"### {exp.get('role', 'Unknown Role')} at {exp.get('company', 'Unknown Company')}\n\n"
            if exp.get('duration'):
                markdown += f"**Duration:** {exp['duration']}\n\n"
            if exp.get('achievements'):
                markdown += "**Key Achievements:**\n"
                for achievement in exp['achievements']:
                    markdown += f"- {achievement}\n"
                markdown += "\n"
    
    # Education
    if 'education' in profile:
        markdown += "## Education\n\n"
        for edu in profile['education']:
            markdown += f"### {edu.get('degree', '')} - {edu.get('institution', '')}\n\n"
            if edu.get('graduation_year'):
                markdown += f"**Graduation:** {edu['graduation_year']}\n\n"
            if edu.get('details'):
                markdown += f"{edu['details']}\n\n"
    
    # Certifications
    if 'certifications' in profile:
        markdown += "## Certifications\n\n"
        for cert in profile['certifications']:
            cert_str = f"- {cert.get('name', '')}"
            if cert.get('organization'):
                cert_str += f" ({cert['organization']})"
            if cert.get('date'):
                cert_str += f" - {cert['date']}"
            markdown += cert_str + "\n"
        markdown += "\n"
    
    # Selected Job Types
    if 'selected_job_types' in profile:
        markdown += "## Selected Job Types\n\n"
        for jt in profile['selected_job_types']:
            markdown += f"- {jt}\n"
        markdown += "\n"
    
    # Preferences
    if 'preferences' in profile:
        pref = profile['preferences']
        markdown += "## Preferences\n\n"
        if pref.get('work_environment'):
            markdown += f"**Work Environment:** {pref['work_environment']}\n\n"
        if pref.get('location_preferences'):
            markdown += f"**Location Preferences:** {pref['location_preferences']}\n\n"
        if pref.get('salary_expectations'):
            markdown += f"**Salary Expectations:** {pref['salary_expectations']}\n\n"
        if pref.get('industry_preferences'):
            markdown += f"**Industry Preferences:** {pref['industry_preferences']}\n\n"
        if pref.get('company_size_preference'):
            markdown += f"**Company Size Preference:** {pref['company_size_preference']}\n\n"
        if pref.get('career_goals'):
            markdown += f"**Career Goals:** {pref['career_goals']}\n\n"
        if pref.get('skills_to_develop'):
            markdown += f"**Skills to Develop:** {pref['skills_to_develop']}\n\n"
    
    # Additional Notes
    if 'additional_notes' in profile:
        markdown += "## Additional Notes\n\n"
        markdown += profile['additional_notes'] + "\n\n"
    
    with open(file_path, 'w') as f:
        f.write(markdown)


def load_profile(file_path: str = "data/profile.md") -> Optional[dict]:
    """
    Load user profile from a Markdown file.
    
    Note: This is a simplified loader. For full parsing, consider using
    a more sophisticated Markdown parser.
    
    Args:
        file_path: Path to the profile file
        
    Returns:
        Profile dictionary or None if file doesn't exist
    """
    if not os.path.exists(file_path):
        return None
    
    # For now, we'll also save/load a JSON version for easier parsing
    json_path = file_path.replace('.md', '.json')
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    
    return None


def save_profile_json(profile: dict, file_path: str = "data/profile.json"):
    """
    Save user profile as JSON for easy programmatic access.
    
    Args:
        profile: Profile dictionary
        file_path: Path to save the JSON file
    """
    ensure_directory(file_path)
    with open(file_path, 'w') as f:
        json.dump(profile, f, indent=2)


def save_job_history(job: dict, file_path: str = "data/history.md"):
    """
    Append a job to the search history file.
    
    Args:
        job: Job dictionary with match info
        file_path: Path to the history file
    """
    ensure_directory(file_path)
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(file_path, 'a') as f:
        f.write(f"\n---\n\n")
        f.write(f"**Date:** {timestamp}\n\n")
        f.write(f"**Job Title:** {job.get('job_title', 'N/A')}\n\n")
        f.write(f"**Company:** {job.get('company_name', 'N/A')}\n\n")
        f.write(f"**Match Score:** {job.get('match_score', 'N/A')}%\n\n")
        f.write(f"**Location:** {job.get('job_location', 'N/A')}\n\n")
        f.write(f"**URL:** {job.get('job_url', 'N/A')}\n\n")
        if job.get('job_description'):
            # Truncate long descriptions
            desc = job['job_description'][:500] + "..." if len(job.get('job_description', '')) > 500 else job.get('job_description', '')
            f.write(f"**Description:** {desc}\n\n")
        if job.get('matching_skills'):
            f.write(f"**Matching Skills:** {', '.join(job['matching_skills'])}\n\n")
        if job.get('missing_skills'):
            f.write(f"**Missing Skills:** {', '.join(job['missing_skills'])}\n\n")


def load_job_history(file_path: str = "data/history.md") -> list:
    """
    Load job search history.
    
    Args:
        file_path: Path to the history file
        
    Returns:
        List of job entries
    """
    if not os.path.exists(file_path):
        return []
    
    # Also check for JSON version
    json_path = file_path.replace('.md', '.json')
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)
    
    return []


def save_job_history_json(history: list, file_path: str = "data/history.json"):
    """
    Save job search history as JSON.
    
    Args:
        history: List of job entries
        file_path: Path to save the JSON file
    """
    ensure_directory(file_path)
    with open(file_path, 'w') as f:
        json.dump(history, f, indent=2)


def get_seen_job_ids(file_path: str = "data/history.json") -> set:
    """
    Get a set of job IDs that have already been shown to the user.
    
    Args:
        file_path: Path to the history JSON file
        
    Returns:
        Set of job IDs
    """
    if not os.path.exists(file_path):
        return set()
    
    try:
        with open(file_path, 'r') as f:
            history = json.load(f)
        return {job.get('job_id') for job in history if job.get('job_id')}
    except (json.JSONDecodeError, KeyError):
        return set()


def save_config_backup(config: dict, backup_path: str = "data/config_backup.json"):
    """
    Save a backup of the configuration.
    
    Args:
        config: Configuration dictionary
        backup_path: Path to save the backup
    """
    ensure_directory(backup_path)
    with open(backup_path, 'w') as f:
        json.dump(config, f, indent=2)


def load_config_backup(backup_path: str = "data/config_backup.json") -> Optional[dict]:
    """
    Load a configuration backup.
    
    Args:
        backup_path: Path to the backup file
        
    Returns:
        Configuration dictionary or None
    """
    if not os.path.exists(backup_path):
        return None
    
    with open(backup_path, 'r') as f:
        return json.load(f)