import logging
from pathlib import Path
from app.utils.sqllitemanager import SQLiteManager
from app.utils import load_config_db

logger = logging.getLogger(__name__)

def initialize_database():
    config = load_config_db()
    
    """Initialize the database if it doesn't exist."""
    db_path = Path(config.get("filename"))
    
    if db_path.exists():
        logger.info(f"Database already exists at {db_path}")
        return
    
    logger.info(f"Creating database at {db_path}")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize SQLiteManager which creates tables
    manager = SQLiteManager()
    manager.initialize_tables()
    
    logger.info("Database initialized successfully")