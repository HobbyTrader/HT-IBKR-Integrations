import sqlite3
import os

from app.utils.logger import LoggerManager

class SQLiteManager:
    def __init__(self, logger: LoggerManager, config: dict):
    # def initialize(self, logger: LoggerManager, config: dict):
        """Initialize the SQLiteManager with configuration."""
        self.logger = logger
        self.db_path = config.get("filename", "data/ht_ibkr_integrations.db")
        self.table_definitions_file = config.get("tabledefinitions", "app/core/sqllite_tables.sql")

        self.connect()
        self.verify_and_create_tables()
        self._initialized = True
    
    def connect(self):
        """Connect to the SQLite database (create if not exists)."""
        self.conn = sqlite3.connect(self.db_path)
        self.logger.debug(f"Connected to database at {self.db_path}")

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.logger.debug("Connection closed.")

    def table_exists(self, table_name):
        """Check if a table exists in the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?
        """, (table_name,))
        exists = cursor.fetchone()[0] == 1
        cursor.close()
        self.logger.debug(f"Table '{table_name}' exists: {exists}")
        return exists

    def get_required_tables(self):
        """
        Parse the table definitions file and extract table names.
        Assumes the file contains standard CREATE TABLE statements.
        """
        tables = []
        if not os.path.isfile(self.table_definitions_file):
            raise FileNotFoundError(f"Table definition file not found: {self.table_definitions_file}")

        with open(self.table_definitions_file, 'r') as f:
            sql = f.read()

        # Simple parse: look for CREATE TABLE statements and extract table names
        for line in sql.splitlines():
            line = line.strip().upper()
            if line.startswith("CREATE TABLE"):
                # Format: CREATE TABLE [IF NOT EXISTS] table_name (
                parts = line.split()
                # Find table name position (after CREATE TABLE and optional IF NOT EXISTS)
                if parts[2] == "IF":
                    table_name = parts[5].lower()
                else:
                    table_name = parts[2].lower()
                # Remove backticks, quotes if any
                table_name = table_name.strip('`"')
                tables.append(table_name)
        return tables

    def create_tables(self):
        """Create tables from the SQL file."""
        cursor = self.conn.cursor()
        with open(self.table_definitions_file, 'r') as f:
            sql = f.read()
        try:
            cursor.executescript(sql)
            self.conn.commit()
            print("Tables created successfully.")
        except sqlite3.Error as e:
            print(f"Error creating tables: {e}")
            self.conn.rollback()
        finally:
            cursor.close()

    def verify_and_create_tables(self):
        """
        Verify if required tables exist.
        If any table is missing, create all tables using the definition file.
        """
        tables = self.get_required_tables()
        missing_tables = [t for t in tables if not self.table_exists(t)]
        if missing_tables:
            self.logger.info(f"Missing tables: {missing_tables}. Creating tables...")
            self.create_tables()
        else:
            self.logger.debug("All required tables are present.")

    def get_connection(self):
        """Get the current database connection."""
        if not self.conn:
            self.connect()
        return self.conn
    
    def get_cursor(self):
        """Get a new cursor from the current connection."""
        if not self.conn:
            self.connect()
        return self.conn.cursor()