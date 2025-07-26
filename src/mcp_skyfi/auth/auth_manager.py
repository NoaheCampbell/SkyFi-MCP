"""Flexible authentication manager for SkyFi API keys."""
import os
import json
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class AuthManager:
    """Manage API key authentication from multiple sources."""
    
    def __init__(self):
        """Initialize the auth manager."""
        self.api_key = None
        self._load_api_key()
    
    def _load_api_key(self) -> None:
        """Load API key from available sources in priority order."""
        # 1. Try environment variable first (for backward compatibility)
        self.api_key = os.environ.get("SKYFI_API_KEY")
        if self.api_key:
            logger.info("API key loaded from environment variable")
            return
        
        # 2. Try AWS Secrets Manager
        self.api_key = self._load_from_aws_secrets()
        if self.api_key:
            logger.info("API key loaded from AWS Secrets Manager")
            return
        
        # 3. Try AWS Parameter Store
        self.api_key = self._load_from_parameter_store()
        if self.api_key:
            logger.info("API key loaded from AWS Parameter Store")
            return
        
        # 4. Try local config file
        self.api_key = self._load_from_config_file()
        if self.api_key:
            logger.info("API key loaded from config file")
            return
        
        # 5. Try runtime configuration
        self.api_key = self._load_from_runtime_config()
        if self.api_key:
            logger.info("API key loaded from runtime configuration")
            return
        
        logger.warning("No API key found in any source")
    
    def _load_from_aws_secrets(self) -> Optional[str]:
        """Load API key from AWS Secrets Manager."""
        try:
            # Check if we're on AWS (have region configured)
            region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
            if not region:
                return None
            
            client = boto3.client("secretsmanager", region_name=region)
            
            # Try to get the secret
            secret_name = os.environ.get("SKYFI_SECRET_NAME", "skyfi/api-key")
            response = client.get_secret_value(SecretId=secret_name)
            
            # Parse the secret
            if "SecretString" in response:
                secret = json.loads(response["SecretString"])
                return secret.get("api_key") or secret.get("SKYFI_API_KEY")
            
        except ClientError as e:
            logger.debug(f"AWS Secrets Manager not available: {e}")
        except Exception as e:
            logger.debug(f"Error loading from AWS Secrets: {e}")
        
        return None
    
    def _load_from_parameter_store(self) -> Optional[str]:
        """Load API key from AWS Systems Manager Parameter Store."""
        try:
            region = os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION")
            if not region:
                return None
            
            client = boto3.client("ssm", region_name=region)
            
            # Try to get the parameter
            param_name = os.environ.get("SKYFI_PARAM_NAME", "/skyfi/api-key")
            response = client.get_parameter(Name=param_name, WithDecryption=True)
            
            return response["Parameter"]["Value"]
            
        except ClientError as e:
            logger.debug(f"AWS Parameter Store not available: {e}")
        except Exception as e:
            logger.debug(f"Error loading from Parameter Store: {e}")
        
        return None
    
    def _load_from_config_file(self) -> Optional[str]:
        """Load API key from local config file."""
        config_paths = [
            Path.home() / ".skyfi" / "config.json",
            Path.home() / ".config" / "skyfi" / "config.json",
            Path("/etc/skyfi/config.json"),
            Path("./skyfi-config.json"),
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    with open(config_path, "r") as f:
                        config = json.load(f)
                        api_key = config.get("api_key") or config.get("SKYFI_API_KEY")
                        if api_key:
                            return api_key
                except Exception as e:
                    logger.debug(f"Error reading config from {config_path}: {e}")
        
        return None
    
    def _load_from_runtime_config(self) -> Optional[str]:
        """Load API key from runtime configuration file."""
        # This file is created at runtime by the MCP client
        runtime_config_path = Path("/tmp/skyfi-runtime-config.json")
        
        if runtime_config_path.exists():
            try:
                with open(runtime_config_path, "r") as f:
                    config = json.load(f)
                    return config.get("api_key")
            except Exception as e:
                logger.debug(f"Error reading runtime config: {e}")
        
        return None
    
    def get_api_key(self) -> Optional[str]:
        """Get the API key."""
        return self.api_key
    
    def set_api_key(self, api_key: str) -> None:
        """Set the API key at runtime."""
        self.api_key = api_key
        
        # Also save to runtime config for persistence
        runtime_config_path = Path("/tmp/skyfi-runtime-config.json")
        try:
            runtime_config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(runtime_config_path, "w") as f:
                json.dump({"api_key": api_key}, f)
        except Exception as e:
            logger.error(f"Failed to save runtime config: {e}")
    
    def clear_runtime_config(self) -> None:
        """Clear runtime configuration."""
        runtime_config_path = Path("/tmp/skyfi-runtime-config.json")
        if runtime_config_path.exists():
            try:
                runtime_config_path.unlink()
            except Exception:
                pass


# Global auth manager instance
auth_manager = AuthManager()