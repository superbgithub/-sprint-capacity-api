"""
Configuration settings for the Sprint Capacity API.
Includes feature flags for controlling feature availability.
"""
import os
from typing import Dict


class FeatureFlags:
    """Feature flags for enabling/disabling features."""
    
    # Sprint Calendar Feature
    SPRINT_CALENDAR_ENABLED = os.getenv("FEATURE_SPRINT_CALENDAR", "false").lower() == "true"
    
    @classmethod
    def is_enabled(cls, feature_name: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature_name: Name of the feature (e.g., "sprint_calendar")
            
        Returns:
            bool: True if feature is enabled, False otherwise
        """
        feature_map: Dict[str, bool] = {
            "sprint_calendar": cls.SPRINT_CALENDAR_ENABLED,
        }
        return feature_map.get(feature_name, False)


# Singleton instance
feature_flags = FeatureFlags()
