"""Pytest tests to verify ht-tools package installation.

Run these tests after installing the package to verify everything is working correctly.

Usage:
    pytest tests/test_setup.py -v
"""

import pytest
import sys

class TestSetup:
    """Test suite for package installation and accessibility"""
    
    def test_version_attribute_exists(self):
        """Test existence of version attribute in package"""
        import ht_tools
        assert hasattr(ht_tools, "__version__")
        
    def test_version_format(self):
        """Test is version follows semantic versionning format"""
        import ht_tools
        version = ht_tools.__version__        
        
        # Check version is a string
        assert isinstance(version, str), f"Version should be string, got {type(version)}"
        
        # Check basic semver format (X.Y.Z)
        parts = version.split(".")
        assert len(parts) >= 2, f"Version should have at least 2 parts, got {version}"
        
        # Check first part is numeric
        assert parts[0].isdigit(), f"Major version should be numeric, got {parts[0]}"                