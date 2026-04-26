#!/usr/bin/env python3
"""
Job Search Agent - Main CLI Entry Point

A CLI-based job search agent that analyzes resumes, curates profiles,
and finds relevant job postings using AI-powered matching.
"""

import argparse
import sys
from pathlib import Path

from .config_manager import ConfigManager


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="jobsearch",
        description="An intelligent job search agent that analyzes your resume "
                    "and finds the most relevant job postings tailored to your "
                    "skills and preferences.",
        epilog="Examples:\n"
               "  %(prog)s --mode profile --resume /path/to/resume.pdf\n"
               "  %(prog)s --mode search\n"
               "  %(prog)s --help\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        choices=["profile", "search"],
        required=True,
        help="Operation mode: 'profile' for profile curation, 'search' for job search",
    )
    
    parser.add_argument(
        "--resume",
        type=str,
        help="Path to resume file (PDF or DOCX) - required for profile mode",
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)",
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
        help="Show program version",
    )
    
    return parser


def validate_profile_mode_args(args: argparse.Namespace) -> None:
    """Validate arguments for profile mode."""
    if not args.resume:
        raise ValueError("--resume is required for profile mode")
    
    resume_path = Path(args.resume)
    if not resume_path.exists():
        raise FileNotFoundError(f"Resume file not found: {args.resume}")
    
    valid_extensions = {".pdf", ".docx"}
    if resume_path.suffix.lower() not in valid_extensions:
        raise ValueError(
            f"Unsupported resume format: {resume_path.suffix}. "
            f"Supported formats: PDF, DOCX"
        )


def run_profile_mode(args: argparse.Namespace) -> int:
    """Run the profile curation mode."""
    try:
        validate_profile_mode_args(args)
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    
    print("Profile curation mode starting...")
    print(f"Resume file: {args.resume}")
    print(f"Configuration: {args.config}")
    
    # Parse the resume file
    try:
        from .resume_parser import ResumeParser
        parser = ResumeParser()
        resume_text = parser.parse(args.resume)
        print(f"Successfully parsed resume ({len(resume_text)} characters extracted)")
        
        # TODO: Implement profile curation flow (Phase 5)
        print("Profile curation is not yet implemented.")
        print("Resume text preview:")
        print("-" * 50)
        print(resume_text[:500] + "..." if len(resume_text) > 500 else resume_text)
        print("-" * 50)
        
    except Exception as e:
        print(f"Error parsing resume: {e}", file=sys.stderr)
        return 1
    
    return 0


def run_search_mode(args: argparse.Namespace) -> int:
    """Run the job search mode."""
    print("Job search mode starting...")
    print(f"Configuration: {args.config}")
    
    # TODO: Implement job search flow (Phase 8)
    print("Job search is not yet implemented.")
    
    return 0


def main() -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Initialize configuration manager
        config_manager = ConfigManager(config_path=args.config)
        
        # Load and validate configuration
        config_manager.load_config()
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1
    
    # Route to appropriate mode
    if args.mode == "profile":
        return run_profile_mode(args)
    elif args.mode == "search":
        return run_search_mode(args)
    else:
        print(f"Unknown mode: {args.mode}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())