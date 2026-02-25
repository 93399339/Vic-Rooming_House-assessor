"""
Environment configuration module for UR Happy Home Assessor.
Handles loading and validating Streamlit secrets like MAPS_API_KEY.
"""

import logging
from typing import Optional
import streamlit as st

# Configure logging
logger = logging.getLogger(__name__)

# ============================================================================
# ENVIRONMENT VARIABLE LOADING
# ============================================================================

class ConfigManager:
    """Manages environment configuration with validation and caching."""
    
    _maps_api_key: Optional[str] = None
    _vicplan_api_key: Optional[str] = None
    _config_initialized = False
    _warnings = []
    
    @classmethod
    def initialize(cls):
        """Initialize configuration on first load."""
        if not cls._config_initialized:
            cls._load_configuration()
            cls._config_initialized = True
    
    @classmethod
    def _load_configuration(cls):
        """Load and validate all secrets from Streamlit secrets.toml."""
        cls._warnings = []

        cls._maps_api_key = cls._read_secret("MAPS_API_KEY")
        cls._vicplan_api_key = cls._read_secret("VICPLAN_API_KEY")

        if not cls._maps_api_key:
            warning = (
                "⚠️  MAPS_API_KEY not found in Streamlit secrets. "
                "Map features will use OpenStreetMap tiles which do not require an API key. "
                "To enable Google Maps tiles or other premium features, set MAPS_API_KEY in .streamlit/secrets.toml."
            )
            cls._warnings.append(warning)
            logger.warning(warning)
        else:
            logger.info("✅ MAPS_API_KEY loaded successfully from Streamlit secrets")

        if not cls._vicplan_api_key:
            warning = (
                "⚠️  VICPLAN_API_KEY not found in Streamlit secrets. "
                "Public VicPlan/WFS lookups will still run where available. "
                "Set VICPLAN_API_KEY in .streamlit/secrets.toml if your deployment uses authenticated VicPlan APIs."
            )
            cls._warnings.append(warning)
            logger.warning(warning)
        else:
            logger.info("✅ VICPLAN_API_KEY loaded successfully from Streamlit secrets")

    @staticmethod
    def _read_secret(key_name: str) -> Optional[str]:
        """Read a secret key from Streamlit secrets safely."""
        try:
            value = st.secrets.get(key_name)
            if value is None:
                return None
            text = str(value).strip()
            return text if text else None
        except Exception:
            return None
    
    @classmethod
    def get_maps_api_key(cls) -> Optional[str]:
        """
        Get the Google Maps API key.
        
        Returns:
            API key if available, None otherwise
        """
        if not cls._config_initialized:
            cls.initialize()
        
        return cls._maps_api_key
    
    @classmethod
    def has_maps_api_key(cls) -> bool:
        """
        Check if MAPS_API_KEY is configured.
        
        Returns:
            True if API key is available, False otherwise
        """
        return cls.get_maps_api_key() is not None

    @classmethod
    def get_vicplan_api_key(cls) -> Optional[str]:
        """Get VicPlan API key from Streamlit secrets."""
        if not cls._config_initialized:
            cls.initialize()
        return cls._vicplan_api_key

    @classmethod
    def has_vicplan_api_key(cls) -> bool:
        """Check whether VicPlan API key is configured."""
        return cls.get_vicplan_api_key() is not None
    
    @classmethod
    def get_warnings(cls) -> list:
        """
        Get any configuration warnings.
        
        Returns:
            List of warning messages
        """
        if not cls._config_initialized:
            cls.initialize()
        
        return cls._warnings
    
    @classmethod
    def validate_maps_api_key(cls, api_key: Optional[str]) -> dict:
        """
        Validate a MAPS_API_KEY format and configuration.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Dictionary with 'valid' (bool) and 'message' (str)
        """
        if not api_key:
            return {
                'valid': True,  # Not having a key is valid (uses fallback tiles)
                'message': 'No API key provided. Using default OpenStreetMap tiles.',
                'tier': 'free'
            }
        
        # Basic validation - Google Maps API keys are typically 39+ characters
        if len(api_key) < 30:
            return {
                'valid': False,
                'message': 'API key appears too short (expected Google Maps format)',
                'tier': 'invalid'
            }
        
        # Check if it looks like a Google Maps API key format
        if not any(char in api_key for char in ['-', '_']):
            return {
                'valid': True,
                'message': 'API key format recognized',
                'tier': 'premium'
            }
        
        return {
            'valid': True,
            'message': 'API key loaded successfully',
            'tier': 'premium'
        }


# Initialize configuration on import
ConfigManager.initialize()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_maps_api_key() -> Optional[str]:
    """
    Get the MAPS_API_KEY from Streamlit secrets.
    
    Returns:
        API key if available, None otherwise
    """
    return ConfigManager.get_maps_api_key()


def get_vicplan_api_key() -> Optional[str]:
    """Get the VICPLAN_API_KEY from Streamlit secrets."""
    return ConfigManager.get_vicplan_api_key()


def has_maps_api_key() -> bool:
    """
    Check if MAPS_API_KEY is configured in Streamlit secrets.
    
    Returns:
        True if API key is available
    """
    return ConfigManager.has_maps_api_key()


def has_vicplan_api_key() -> bool:
    """Check if VICPLAN_API_KEY is configured."""
    return ConfigManager.has_vicplan_api_key()


def get_secret_status() -> dict:
    """Return runtime status of required/optional API secrets for startup checks."""
    return {
        "maps": has_maps_api_key(),
        "vicplan": has_vicplan_api_key(),
        "warnings": get_config_warnings(),
    }


def get_config_warnings() -> list:
    """
    Get configuration warnings.
    
    Returns:
        List of warning messages
    """
    return ConfigManager.get_warnings()


def log_config_status():
    """Log current configuration status for debugging."""
    print("\n" + "=" * 70)
    print("CONFIGURATION STATUS")
    print("=" * 70)
    
    if has_maps_api_key():
        print("✅ MAPS_API_KEY: Configured")
    else:
        print("⚠️  MAPS_API_KEY: Not configured (using OpenStreetMap fallback)")
    
    warnings = get_config_warnings()
    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  {warning}")
    else:
        print("\n✅ No configuration warnings")
    
    print("=" * 70 + "\n")
