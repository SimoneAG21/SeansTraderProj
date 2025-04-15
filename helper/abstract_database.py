"""
Overview:
This module provides an abstract database interface for the #SeanProjectTrading project,
supporting multiple databases (PostgreSQL, SQLite, etc.) using Abstract Factory and Adapter
patterns. It enables switching databases via configuration without changing application code.

Purpose:
- Abstracts database-specific logic (engine creation, connection testing).
- Reusable across scripts (e.g., telegram_fetch.py, app.py) while preserving compatibility
  with the existing DatabaseHandler.

Usage:
- Instantiate: `factory = get_database_factory(config, logger); handler = factory.create_handler()`
- Get engine: `engine = handler.get_engine()`

Dependencies:
- sqlalchemy: For database engines.
- psycopg2-binary: PostgreSQL driver (optional, based on config).
- helper.config_manager.ConfigManager: For database settings.
- helper.Logger.Logging: For logging database events.
"""
from abc import ABC, abstractmethod
from sqlalchemy import create_engine
try:
    from helper.config_manager import ConfigManager
    from helper.Logger import Logging
except ImportError as e:
    raise ImportError(f"Failed to import dependencies: {e}")

class AbstractDatabaseHandler(ABC):
    """Abstract base class for database handlers."""
    def __init__(self, config: ConfigManager, logger: Logging):
        if not isinstance(config, ConfigManager):
            raise TypeError("config must be a ConfigManager instance")
        if not isinstance(logger, Logging):
            raise TypeError("logger must be a Logging instance")
        self.config = config
        self.logger = logger
        self.engine = None

    @abstractmethod
    def create_engine(self):
        """Create and set the database engine."""
        pass

    @abstractmethod
    def test_connection(self):
        """Test the database connection."""
        pass

    def get_engine(self):
        """Return the database engine."""
        return self.engine

class PostgresHandler(AbstractDatabaseHandler):
    """Concrete handler for PostgreSQL."""
    def create_engine(self):
        try:
            required_keys = ["user", "password", "host", "database", "port"]
            for key in required_keys:
                value = self.config.get_with_default("database", key, default=None)
                if not value:
                    db_config = self.config.get_with_default("database", None, default={})
                    self.logger.error(f"Missing database config key: {key}. Config: {db_config}")
                    raise ValueError(f"Missing database config key: {key}")
            connection_string = (
                f"postgresql+psycopg2://"
                f"{self.config.get('database', 'user')}:"
                f"{self.config.get('database', 'password')}@"
                f"{self.config.get('database', 'host')}:"
                f"{self.config.get('database', 'port')}/"
                f"{self.config.get('database', 'database')}"
            )
            self.engine = create_engine(connection_string)
        except Exception as e:
            self.logger.error(f"Error creating PostgreSQL engine: {e}")
            raise

    def test_connection(self):
        try:
            with self.engine.connect() as conn:
                pass
        except Exception as e:
            self.logger.error(f"Error connecting to PostgreSQL: {e}")
            raise

class SQLiteHandler(AbstractDatabaseHandler):
    """Concrete handler for SQLite."""
    def create_engine(self):
        try:
            db_path = self.config.get_with_default("database", "path", default=":memory:")
            if not db_path:
                self.logger.error("Missing database path for SQLite")
                raise ValueError("Missing database path")
            connection_string = f"sqlite:///{db_path}"
            self.engine = create_engine(connection_string)
        except Exception as e:
            self.logger.error(f"Error creating SQLite engine: {e}")
            raise

    def test_connection(self):
        try:
            with self.engine.connect() as conn:
                conn.execute("SELECT 1")  # Simple query to test connection
        except Exception as e:
            self.logger.error(f"Error connecting to SQLite: {e}")
            raise

class AbstractDatabaseFactory(ABC):
    """Abstract factory for creating database handlers."""
    @abstractmethod
    def create_handler(self, config: ConfigManager, logger: Logging) -> AbstractDatabaseHandler:
        """Create a database handler instance."""
        pass

class PostgresFactory(AbstractDatabaseFactory):
    """Concrete factory for PostgreSQL."""
    def create_handler(self, config: ConfigManager, logger: Logging) -> AbstractDatabaseHandler:
        return PostgresHandler(config, logger)

class SQLiteFactory(AbstractDatabaseFactory):
    """Concrete factory for SQLite."""
    def create_handler(self, config: ConfigManager, logger: Logging) -> AbstractDatabaseHandler:
        return SQLiteHandler(config, logger)

def get_database_factory(config: ConfigManager, logger: Logging) -> AbstractDatabaseFactory:
    """Return the appropriate factory based on config."""
    db_type = config.get_with_default("database", "type", default="postgresql")
    if db_type == "postgresql":
        return PostgresFactory()
    elif db_type == "sqlite":
        return SQLiteFactory()
    else:
        logger.error(f"Unsupported database type: {db_type}")
        raise ValueError(f"Unsupported database type: {db_type}")