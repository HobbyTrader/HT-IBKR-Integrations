"""Test configuration utilities."""
import os
from pathlib import Path

TEST_DIR = Path(__file__).parent
TEST_DATA_DIR = TEST_DIR / 'test_data'
TEST_DB_DIR = TEST_DATA_DIR / 'databases'

# Ensure test directories exist
TEST_DATA_DIR.mkdir(exist_ok=True)
TEST_DB_DIR.mkdir(exist_ok=True)


def get_test_db_config(in_memory: bool = True):
    """
    Get complete database configuration for testing.
    
    Args:
        in_memory: If True, use in-memory database. Otherwise, use temp file.
    
    Returns:
        dict: Complete database configuration
    """
    if in_memory:
        db_path = ':memory:'
    else:
        import tempfile
        temp_db = tempfile.NamedTemporaryFile(
            delete=False, 
            suffix='.db',
            dir=TEST_DB_DIR
        )
        temp_db.close()
        db_path = temp_db.name
    
    return {
        'filename': db_path,
        'timeout': 10,
        'check_same_thread': False,
        'tabledefinitions': 'table_definitions.sql'  # Required by SQLiteManager
    }


def get_test_ibapi_config():
    """Get IBKR API configuration for testing."""
    return {
        'HOST': 'localhost',
        'PORT': 7497,  # Paper trading port
        'CLIENTID': 999  # Test client ID
    }


def cleanup_test_databases():
    """Clean up any temporary test database files."""
    if TEST_DB_DIR.exists():
        for db_file in TEST_DB_DIR.glob('*.db'):
            try:
                os.unlink(db_file)
            except Exception as e:
                print(f"Warning: Could not delete {db_file}: {e}")