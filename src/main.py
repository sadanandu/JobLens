#!/usr/bin/env python3
"""
Job Search Agent - Main CLI Entry Point

A CLI tool that helps users find jobs matching their profile.
Two modes:
1. Profile Curation Mode: Parse resume, analyze profile, select job types
2. Job Search Mode: Search for matching jobs and display top matches
"""

import os
import sys
import argparse
from dotenv import load_dotenv

from .profile_curator import ProfileCurator
from .job_searcher import JobSearcher


def main():
    """Main entry point for the Job Search Agent CLI."""
    # Load environment variables from .env file (for local development)
    load_dotenv()
    
    parser = argparse.ArgumentParser(
        description="Job Search Agent - Find jobs matching your profile",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Profile Curation Mode (first time setup)
  python -m src.main --mode profile --resume /path/to/resume.pdf

  # Job Search Mode (daily use)
  python -m src.main --mode search

  # Job Search with custom config
  python -m src.main --mode search --config /path/to/config.yaml
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['profile', 'search'],
        required=True,
        help='Operation mode: "profile" for profile curation, "search" for job search'
    )
    
    parser.add_argument(
        '--resume',
        type=str,
        help='Path to resume file (PDF or DOCX). Required for profile mode.'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config/config.yaml',
        help='Path to configuration file (default: config/config.yaml)'
    )
    
    parser.add_argument(
        '--top',
        type=int,
        default=3,
        help='Number of job matches to show (default: 3). Only for search mode.'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.mode == 'profile' and not args.resume:
        parser.error("--resume is required for profile mode")
    
    if not os.path.exists(args.config):
        print(f"❌ Configuration file not found: {args.config}")
        print("   Please create a config file or use the default: config/config.yaml")
        sys.exit(1)
    
    try:
        if args.mode == 'profile':
            run_profile_mode(args)
        else:
            run_search_mode(args)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"\n❌ Error: {e}")
            print("   Use --verbose for detailed error information.")
        sys.exit(1)


def run_profile_mode(args):
    """Run the profile curation mode."""
    print("\n" + "=" * 60)
    print("  JOB SEARCH AGENT")
    print("  Profile Curation Mode")
    print("=" * 60)
    
    # Check if resume file exists
    if not os.path.exists(args.resume):
        print(f"\n❌ Resume file not found: {args.resume}")
        sys.exit(1)
    
    # Run profile curator
    curator = ProfileCurator(config_path=args.config)
    profile = curator.run(args.resume)
    
    if not profile:
        print("\n❌ Profile curation failed.")
        sys.exit(1)
    
    print("\n✅ Profile curation completed successfully!")
    print("\nNext steps:")
    print("  1. Set up your API keys:")
    print("     - ANTHROPIC_API_KEY (for Claude AI)")
    print("     - JSEARCH_API_KEY (for job search)")
    print("  2. Run job search mode:")
    print("     python -m src.main --mode search")


def run_search_mode(args):
    """Run the job search mode."""
    print("\n" + "=" * 60)
    print("  JOB SEARCH AGENT")
    print("  Job Search Mode")
    print("=" * 60)
    
    # Check for required API keys
    check_api_keys()
    
    # Run job searcher
    searcher = JobSearcher(config_path=args.config)
    results = searcher.run(top_n=args.top)
    
    if not results:
        print("\n⚠️  No matching jobs found.")
        print("   Try running profile curation mode first to set up your profile.")
        print("   Or check your API keys and network connection.")
        sys.exit(0)
    
    print("\n✅ Job search completed successfully!")
    print(f"\nFound {len(results)} matching jobs.")
    print("View detailed history at: data/history.md")


def check_api_keys():
    """Check if required API keys are set."""
    missing_keys = []
    
    if not os.getenv('ANTHROPIC_API_KEY'):
        missing_keys.append('ANTHROPIC_API_KEY')
    
    if not os.getenv('JSEARCH_API_KEY'):
        missing_keys.append('JSEARCH_API_KEY')
    
    if missing_keys:
        print("\n⚠️  Missing API keys:")
        for key in missing_keys:
            print(f"  - {key}")
        print("\nSet these environment variables before running job search.")
        print("\nTo set API keys:")
        print("  export ANTHROPIC_API_KEY='your-anthropic-key'")
        print("  export JSEARCH_API_KEY='your-jsearch-key'")
        print("\nOr add them to your shell profile (~/.bashrc, ~/.zshrc, etc.)")
        print("\nGet your keys from:")
        print("  - Anthropic: https://console.anthropic.com/")
        print("  - JSearch: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch")
        print("\nContinuing anyway (some features may not work)...")


if __name__ == '__main__':
    main()