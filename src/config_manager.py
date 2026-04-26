import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv


class ConfigManager:
    """Configuration manager for the Job Search Agent."""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        self.config_path = Path(config_path)
        self._config: Optional[Dict[str, Any]] = None
        
        # Load environment variables
        load_dotenv()
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            "data",
            "data/resumes",
            ".cache/litellm"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load and validate the configuration.
        
        Returns:
            Dictionary containing the configuration
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
        """
        if self._config is not None:
            return self._config
        
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        try:
            with open(self.config_path, 'r') as file:
                self._config = yaml.safe_load(file)
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Error parsing YAML configuration: {e}")
        
        # Validate required sections
        self._validate_config()
        
        return self._config
    
    def _validate_config(self) -> None:
        """Validate the configuration structure."""
        required_sections = ['llm', 'jsearch', 'matching', 'storage']
        
        for section in required_sections:
            if section not in self._config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate LLM configuration
        llm_config = self._config['llm']
        if 'model' not in llm_config:
            raise ValueError("Missing required LLM model configuration")
        
        # Validate JSearch configuration
        jsearch_config = self._config['jsearch']
        if 'api_key' not in jsearch_config:
            raise ValueError("Missing required JSearch API key configuration")
        
        # Validate matching weights
        matching_config = self._config['matching']
        if 'weights' not in matching_config:
            raise ValueError("Missing required matching weights configuration")
        
        weights = matching_config['weights']
        required_weights = ['skills', 'experience', 'job_type', 'location', 'industry']
        for weight in required_weights:
            if weight not in weights:
                raise ValueError(f"Missing required matching weight: {weight}")
        
        # Validate storage configuration
        storage_config = self._config['storage']
        required_storage = ['profile_dir', 'history_dir', 'resume_backup_dir']
        for storage_key in required_storage:
            if storage_key not in storage_config:
                raise ValueError(f"Missing required storage configuration: {storage_key}")
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration with environment variable substitution."""
        llm_config = self.load_config()['llm'].copy()
        
        # Substitute environment variables
        for key, value in llm_config.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]  # Remove ${ and }
                env_value = os.getenv(env_var)
                if env_value:
                    llm_config[key] = env_value
                else:
                    raise ValueError(f"Environment variable {env_var} not found")
        
        return llm_config
    
    def get_jsearch_config(self) -> Dict[str, Any]:
        """Get JSearch configuration with environment variable substitution."""
        jsearch_config = self.load_config()['jsearch'].copy()
        
        # Substitute API key
        if 'api_key' in jsearch_config:
            api_key = jsearch_config['api_key']
            if isinstance(api_key, str) and api_key.startswith('${') and api_key.endswith('}'):
                env_var = api_key[2:-1]  # Remove ${ and }
                env_value = os.getenv(env_var)
                if env_value:
                    jsearch_config['api_key'] = env_value
                else:
                    raise ValueError(f"Environment variable {env_var} not found")
        
        return jsearch_config
    
    def get_matching_config(self) -> Dict[str, Any]:
        """Get matching configuration."""
        return self.load_config()['matching']
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration."""
        return self.load_config()['storage']
    
    def get_system_prompts(self) -> Dict[str, str]:
        """
        Load system prompts from the prompts file.
        
        Returns:
            Dictionary with prompt names as keys and prompt text as values
        """
        prompts_path = Path("config/system_prompts.md")
        
        if not prompts_path.exists():
            raise FileNotFoundError(f"System prompts file not found: {prompts_path}")
        
        prompts = {}
        current_prompt = None
        current_content = []
        
        with open(prompts_path, 'r') as file:
            for line in file:
                line = line.rstrip()
                
                # Check if this is a prompt title
                if line.startswith('## '):
                    # Save previous prompt if exists
                    if current_prompt and current_content:
                        prompts[current_prompt] = '\n'.join(current_content).strip()
                    
                    # Start new prompt
                    current_prompt = line[3:].strip()  # Remove '## ' prefix
                    current_content = []
                elif current_prompt:
                    # Add content to current prompt
                    current_content.append(line)
        
        # Save the last prompt
        if current_prompt and current_content:
            prompts[current_prompt] = '\n'.join(current_content).strip()
        
        return prompts