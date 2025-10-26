"""
Database management system for LeetCode Analytics API.

This module provides optional SQL database persistence with proper indexing,
connection management, and error handling for scalable data storage.
"""

import logging
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import pandas as pd
import sqlite3
from pathlib import Path

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

logger = logging.getLogger(__name__)


class DatabaseConfig:
    """Configuration for database connections."""
    
    def __init__(self, db_type: str = "sqlite", **kwargs):
        """
        Initialize database configuration.
        
        Args:
            db_type: Database type ("sqlite" or "postgresql")
            **kwargs: Database-specific connection parameters
        """
        self.db_type = db_type.lower()
        self.config = kwargs
        
        if self.db_type == "sqlite":
            self.db_path = kwargs.get("db_path", "leetcode_analytics.db")
        elif self.db_type == "postgresql":
            if not POSTGRES_AVAILABLE:
                raise ImportError("psycopg2 is required for PostgreSQL support")
            self.host = kwargs.get("host", "localhost")
            self.port = kwargs.get("port", 5432)
            self.database = kwargs.get("database", "leetcode_analytics")
            self.username = kwargs.get("username", "postgres")
            self.password = kwargs.get("password", "")
        else:
            raise ValueError(f"Unsupported database type: {db_type}")


class DatabaseManager:
    """
    Manages SQL database operations for the LeetCode Analytics system.
    
    Features:
    - Support for SQLite and PostgreSQL
    - Automatic table creation with proper indexing
    - Batch data insertion with error handling
    - Connection pooling and management
    - Data validation and type conversion
    """
    
    def __init__(self, config: DatabaseConfig):
        """
        Initialize the database manager.
        
        Args:
            config: Database configuration
        """
        self.config = config
        self.connection = None
        self._table_schemas = self._get_table_schemas()
        
        logger.info(f"DatabaseManager initialized for {config.db_type}")
    
    def _get_table_schemas(self) -> Dict[str, Dict[str, str]]:
        """
        Define table schemas for different database types.
        
        Returns:
            Dictionary mapping table names to column definitions
        """
        if self.config.db_type == "sqlite":
            return {
                "problems": {
                    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "difficulty": "TEXT NOT NULL",
                    "title": "TEXT NOT NULL",
                    "frequency": "REAL NOT NULL",
                    "acceptance_rate": "REAL NOT NULL",
                    "link": "TEXT",
                    "topics": "TEXT",
                    "company": "TEXT NOT NULL",
                    "timeframe": "TEXT NOT NULL",
                    "source_file": "TEXT",
                    "last_updated": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                },
                "problem_topics": {
                    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "problem_id": "INTEGER NOT NULL",
                    "topic": "TEXT NOT NULL",
                    "FOREIGN KEY (problem_id)": "REFERENCES problems(id)"
                },
                "company_stats": {
                    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
                    "company": "TEXT NOT NULL UNIQUE",
                    "total_problems": "INTEGER NOT NULL",
                    "unique_problems": "INTEGER NOT NULL",
                    "avg_frequency": "REAL NOT NULL",
                    "max_frequency": "REAL NOT NULL",
                    "min_frequency": "REAL NOT NULL",
                    "avg_acceptance_rate": "REAL NOT NULL",
                    "easy_count": "INTEGER DEFAULT 0",
                    "medium_count": "INTEGER DEFAULT 0",
                    "hard_count": "INTEGER DEFAULT 0",
                    "timeframe_30d": "INTEGER DEFAULT 0",
                    "timeframe_3m": "INTEGER DEFAULT 0",
                    "timeframe_6m": "INTEGER DEFAULT 0",
                    "timeframe_6m_plus": "INTEGER DEFAULT 0",
                    "timeframe_all": "INTEGER DEFAULT 0",
                    "top_topics": "TEXT",
                    "total_unique_topics": "INTEGER DEFAULT 0",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                }
            }
        else:  # PostgreSQL
            return {
                "problems": {
                    "id": "SERIAL PRIMARY KEY",
                    "difficulty": "VARCHAR(10) NOT NULL",
                    "title": "TEXT NOT NULL",
                    "frequency": "REAL NOT NULL",
                    "acceptance_rate": "REAL NOT NULL",
                    "link": "TEXT",
                    "topics": "TEXT",
                    "company": "VARCHAR(100) NOT NULL",
                    "timeframe": "VARCHAR(10) NOT NULL",
                    "source_file": "TEXT",
                    "last_updated": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                },
                "problem_topics": {
                    "id": "SERIAL PRIMARY KEY",
                    "problem_id": "INTEGER NOT NULL REFERENCES problems(id)",
                    "topic": "VARCHAR(100) NOT NULL"
                },
                "company_stats": {
                    "id": "SERIAL PRIMARY KEY",
                    "company": "VARCHAR(100) NOT NULL UNIQUE",
                    "total_problems": "INTEGER NOT NULL",
                    "unique_problems": "INTEGER NOT NULL",
                    "avg_frequency": "REAL NOT NULL",
                    "max_frequency": "REAL NOT NULL",
                    "min_frequency": "REAL NOT NULL",
                    "avg_acceptance_rate": "REAL NOT NULL",
                    "easy_count": "INTEGER DEFAULT 0",
                    "medium_count": "INTEGER DEFAULT 0",
                    "hard_count": "INTEGER DEFAULT 0",
                    "timeframe_30d": "INTEGER DEFAULT 0",
                    "timeframe_3m": "INTEGER DEFAULT 0",
                    "timeframe_6m": "INTEGER DEFAULT 0",
                    "timeframe_6m_plus": "INTEGER DEFAULT 0",
                    "timeframe_all": "INTEGER DEFAULT 0",
                    "top_topics": "JSONB",
                    "total_unique_topics": "INTEGER DEFAULT 0",
                    "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                }
            }
    
    def _get_indexes(self) -> Dict[str, List[str]]:
        """
        Define indexes for optimal query performance.
        
        Returns:
            Dictionary mapping table names to index definitions
        """
        return {
            "problems": [
                "CREATE INDEX IF NOT EXISTS idx_problems_company ON problems(company)",
                "CREATE INDEX IF NOT EXISTS idx_problems_timeframe ON problems(timeframe)",
                "CREATE INDEX IF NOT EXISTS idx_problems_difficulty ON problems(difficulty)",
                "CREATE INDEX IF NOT EXISTS idx_problems_title ON problems(title)",
                "CREATE INDEX IF NOT EXISTS idx_problems_frequency ON problems(frequency DESC)",
                "CREATE INDEX IF NOT EXISTS idx_problems_company_timeframe ON problems(company, timeframe)",
                "CREATE INDEX IF NOT EXISTS idx_problems_difficulty_frequency ON problems(difficulty, frequency DESC)"
            ],
            "problem_topics": [
                "CREATE INDEX IF NOT EXISTS idx_problem_topics_topic ON problem_topics(topic)",
                "CREATE INDEX IF NOT EXISTS idx_problem_topics_problem_id ON problem_topics(problem_id)"
            ],
            "company_stats": [
                "CREATE INDEX IF NOT EXISTS idx_company_stats_company ON company_stats(company)"
            ]
        }
    
    def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if self.config.db_type == "sqlite":
                # Ensure directory exists for SQLite
                db_path = Path(self.config.db_path)
                db_path.parent.mkdir(parents=True, exist_ok=True)
                
                self.connection = sqlite3.connect(
                    self.config.db_path,
                    check_same_thread=False
                )
                self.connection.row_factory = sqlite3.Row
                
            elif self.config.db_type == "postgresql":
                self.connection = psycopg2.connect(
                    host=self.config.host,
                    port=self.config.port,
                    database=self.config.database,
                    user=self.config.username,
                    password=self.config.password,
                    cursor_factory=RealDictCursor
                )
                self.connection.autocommit = False
            
            logger.info(f"Connected to {self.config.db_type} database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            return False
    
    def disconnect(self) -> None:
        """Close database connection."""
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
                logger.info("Database connection closed")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
    
    def create_tables(self) -> bool:
        """
        Create all required tables with proper schemas and indexes.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.connection:
            logger.error("No database connection available")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Create tables
            for table_name, schema in self._table_schemas.items():
                columns = []
                constraints = []
                
                for column_def, column_type in schema.items():
                    if column_def.startswith("FOREIGN KEY"):
                        constraints.append(f"{column_def} {column_type}")
                    else:
                        columns.append(f"{column_def} {column_type}")
                
                # Build CREATE TABLE statement
                create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
                create_sql += ",\n".join(columns)
                if constraints:
                    create_sql += ",\n" + ",\n".join(constraints)
                create_sql += "\n)"
                
                cursor.execute(create_sql)
                logger.debug(f"Created table: {table_name}")
            
            # Create indexes
            indexes = self._get_indexes()
            for table_name, index_list in indexes.items():
                for index_sql in index_list:
                    cursor.execute(index_sql)
                    logger.debug(f"Created index for table: {table_name}")
            
            self.connection.commit()
            logger.info("All tables and indexes created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating tables: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def insert_problems(self, df: pd.DataFrame, batch_size: int = 1000) -> bool:
        """
        Insert problem data into the database.
        
        Args:
            df: DataFrame containing problem data
            batch_size: Number of records to insert per batch
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connection:
            logger.error("No database connection available")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Clear existing data
            cursor.execute("DELETE FROM problem_topics")
            cursor.execute("DELETE FROM problems")
            
            # Prepare data for insertion
            df_clean = df.copy()
            
            # Handle missing values and data types
            df_clean['difficulty'] = df_clean['difficulty'].fillna('UNKNOWN')
            df_clean['frequency'] = pd.to_numeric(df_clean['frequency'], errors='coerce').fillna(0.0)
            df_clean['acceptance_rate'] = pd.to_numeric(df_clean['acceptance_rate'], errors='coerce').fillna(0.0)
            df_clean['topics'] = df_clean['topics'].fillna('')
            df_clean['link'] = df_clean['link'].fillna('')
            df_clean['source_file'] = df_clean['source_file'].fillna('')
            
            # Insert problems in batches
            total_records = len(df_clean)
            logger.info(f"Inserting {total_records} problem records in batches of {batch_size}")
            
            for i in range(0, total_records, batch_size):
                batch_df = df_clean.iloc[i:i + batch_size]
                
                if self.config.db_type == "sqlite":
                    insert_sql = """
                        INSERT INTO problems (difficulty, title, frequency, acceptance_rate, 
                                            link, topics, company, timeframe, source_file, last_updated)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    batch_data = []
                    for _, row in batch_df.iterrows():
                        batch_data.append((
                            row['difficulty'], row['title'], row['frequency'], row['acceptance_rate'],
                            row['link'], row['topics'], row['company'], row['timeframe'],
                            row['source_file'], datetime.now()
                        ))
                    
                    cursor.executemany(insert_sql, batch_data)
                    
                else:  # PostgreSQL
                    insert_sql = """
                        INSERT INTO problems (difficulty, title, frequency, acceptance_rate, 
                                            link, topics, company, timeframe, source_file, last_updated)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    batch_data = []
                    for _, row in batch_df.iterrows():
                        batch_data.append((
                            row['difficulty'], row['title'], row['frequency'], row['acceptance_rate'],
                            row['link'], row['topics'], row['company'], row['timeframe'],
                            row['source_file'], datetime.now()
                        ))
                    
                    cursor.executemany(insert_sql, batch_data)
                
                logger.debug(f"Inserted batch {i//batch_size + 1}/{(total_records-1)//batch_size + 1}")
            
            self.connection.commit()
            logger.info(f"Successfully inserted {total_records} problem records")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting problems: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def insert_problem_topics(self, df: pd.DataFrame) -> bool:
        """
        Insert exploded topic data into the problem_topics table.
        
        Args:
            df: DataFrame with exploded topics (one topic per row)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connection:
            logger.error("No database connection available")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Get problem IDs by title and company (assuming unique combination)
            problem_id_map = {}
            cursor.execute("SELECT id, title, company FROM problems")
            for row in cursor.fetchall():
                key = (row['title'], row['company'])
                problem_id_map[key] = row['id']
            
            # Prepare topic data
            topic_data = []
            for _, row in df.iterrows():
                if pd.notna(row.get('topic')) and row['topic'].strip():
                    key = (row['title'], row['company'])
                    if key in problem_id_map:
                        topic_data.append((problem_id_map[key], row['topic'].strip()))
            
            if not topic_data:
                logger.warning("No valid topic data to insert")
                return True
            
            # Insert topics
            if self.config.db_type == "sqlite":
                insert_sql = "INSERT INTO problem_topics (problem_id, topic) VALUES (?, ?)"
            else:
                insert_sql = "INSERT INTO problem_topics (problem_id, topic) VALUES (%s, %s)"
            
            cursor.executemany(insert_sql, topic_data)
            self.connection.commit()
            
            logger.info(f"Successfully inserted {len(topic_data)} topic records")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting problem topics: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def insert_company_stats(self, df: pd.DataFrame) -> bool:
        """
        Insert company statistics into the database.
        
        Args:
            df: DataFrame containing company statistics
            
        Returns:
            True if successful, False otherwise
        """
        if not self.connection:
            logger.error("No database connection available")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Clear existing stats
            cursor.execute("DELETE FROM company_stats")
            
            # Prepare data
            df_clean = df.copy()
            
            # Handle JSON serialization for top_topics
            if 'top_topics' in df_clean.columns:
                if self.config.db_type == "sqlite":
                    import json
                    df_clean['top_topics'] = df_clean['top_topics'].apply(
                        lambda x: json.dumps(x) if isinstance(x, dict) else '{}'
                    )
                # For PostgreSQL, psycopg2 handles dict to JSONB conversion automatically
            
            # Insert company stats
            for _, row in df_clean.iterrows():
                if self.config.db_type == "sqlite":
                    insert_sql = """
                        INSERT INTO company_stats (
                            company, total_problems, unique_problems, avg_frequency, max_frequency,
                            min_frequency, avg_acceptance_rate, easy_count, medium_count, hard_count,
                            timeframe_30d, timeframe_3m, timeframe_6m, timeframe_6m_plus, timeframe_all,
                            top_topics, total_unique_topics
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                    
                    cursor.execute(insert_sql, (
                        row['company'], row['total_problems'], row['unique_problems'],
                        row['avg_frequency'], row['max_frequency'], row['min_frequency'],
                        row['avg_acceptance_rate'], row.get('easy_count', 0),
                        row.get('medium_count', 0), row.get('hard_count', 0),
                        row.get('timeframe_30d', 0), row.get('timeframe_3m', 0),
                        row.get('timeframe_6m', 0), row.get('timeframe_6m_plus', 0),
                        row.get('timeframe_all', 0), row.get('top_topics', '{}'),
                        row.get('total_unique_topics', 0)
                    ))
                    
                else:  # PostgreSQL
                    insert_sql = """
                        INSERT INTO company_stats (
                            company, total_problems, unique_problems, avg_frequency, max_frequency,
                            min_frequency, avg_acceptance_rate, easy_count, medium_count, hard_count,
                            timeframe_30d, timeframe_3m, timeframe_6m, timeframe_6m_plus, timeframe_all,
                            top_topics, total_unique_topics
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(insert_sql, (
                        row['company'], row['total_problems'], row['unique_problems'],
                        row['avg_frequency'], row['max_frequency'], row['min_frequency'],
                        row['avg_acceptance_rate'], row.get('easy_count', 0),
                        row.get('medium_count', 0), row.get('hard_count', 0),
                        row.get('timeframe_30d', 0), row.get('timeframe_3m', 0),
                        row.get('timeframe_6m', 0), row.get('timeframe_6m_plus', 0),
                        row.get('timeframe_all', 0), row.get('top_topics', {}),
                        row.get('total_unique_topics', 0)
                    ))
            
            self.connection.commit()
            logger.info(f"Successfully inserted {len(df_clean)} company statistics")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting company stats: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def query(self, sql: str, params: tuple = None) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SELECT query and return results.
        
        Args:
            sql: SQL query string
            params: Query parameters
            
        Returns:
            List of dictionaries representing rows, or None if error
        """
        if not self.connection:
            logger.error("No database connection available")
            return None
        
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            
            if self.config.db_type == "sqlite":
                rows = [dict(row) for row in cursor.fetchall()]
            else:
                rows = cursor.fetchall()
            
            return rows
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            return None
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics and health information.
        
        Returns:
            Dictionary with database statistics
        """
        if not self.connection:
            return {"status": "disconnected"}
        
        try:
            stats = {
                "status": "connected",
                "database_type": self.config.db_type,
                "tables": {}
            }
            
            # Get table row counts
            for table_name in self._table_schemas.keys():
                result = self.query(f"SELECT COUNT(*) as count FROM {table_name}")
                if result:
                    stats["tables"][table_name] = result[0]["count"]
                else:
                    stats["tables"][table_name] = 0
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {"status": "error", "error": str(e)}
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()