import sqlite3
import os

class SQLiteManager:
    def __init__(self, db_path, table_definitions_file):
        self.db_path = db_path
        self.table_definitions_file = table_definitions_file
        self.conn = None

    def connect(self):
        """Connect to the SQLite database (create if not exists)."""
        self.conn = sqlite3.connect(self.db_path)
        print(f"Connected to database at {self.db_path}")

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            print("Connection closed.")

    def table_exists(self, table_name):
        """Check if a table exists in the database."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT count(name) FROM sqlite_master WHERE type='table' AND name=?
        """, (table_name,))
        exists = cursor.fetchone()[0] == 1
        cursor.close()
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
                    table_name = parts[5]
                else:
                    table_name = parts[2]
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
            print(f"Missing tables: {missing_tables}. Creating tables...")
            self.create_tables()
        else:
            print("All required tables are present.")
