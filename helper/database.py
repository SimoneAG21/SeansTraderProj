# helper/database.py
"""
Overview:
This module provides a DatabaseHandler class for the #SeanProjectTrading project, managing
PostgreSQL database connections using SQLAlchemy for Heroku deployment.

Purpose:
- Encapsulates database connection setup and testing.
- Reusable across scripts (e.g., telegram_fetch.py, app.py).

Usage:
- Instantiate: `db_handler = DatabaseHandler(config, logger)`
- Get engine: `engine = db_handler.get_engine()`

Dependencies:
- sqlalchemy: For database connections.
- psycopg2-binary: PostgreSQL driver for SQLAlchemy.
- helper.config_manager.ConfigManager: For database settings.
- helper.Logger.Logging: For logging database events.
"""
"""
Overview:
This module provides a DatabaseHandler class for the #SeanProjectTrading project, managing
PostgreSQL database connections using SQLAlchemy for Heroku deployment.

Purpose:
- Encapsulates database connection setup and testing.
- Reusable across scripts (e.g., telegram_fetch.py, app.py).

Usage:
- Instantiate: `db_handler = DatabaseHandler(config, logger)`
- Get engine: `engine = db_handler.get_engine()`

Dependencies:
- sqlalchemy: For database connections.
- psycopg2-binary: PostgreSQL driver for SQLAlchemy.
- helper.config_manager.ConfigManager: For database settings.
- helper.Logger.Logging: For logging database events.
"""
from sqlalchemy import create_engine
try:
    from helper.config_manager import ConfigManager
    from helper.Logger import Logging
except ImportError as e:
    raise ImportError(f"Failed to import dependencies: {e}")

class DatabaseHandler:
    def __init__(self, config: ConfigManager, logger: Logging):
        if not isinstance(config, ConfigManager):
            raise TypeError("config must be a ConfigManager instance")
        if not isinstance(logger, Logging):
            raise TypeError("logger must be a Logging instance")
        self.config = config
        self.logger = logger
        self.engine = None
        self._create_engine()
        self._test_connection()

    def _create_engine(self):
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

    def _test_connection(self):
        try:
            with self.engine.connect() as conn:
                pass  # Connection successful, no need to log
        except Exception as e:
            self.logger.error(f"Error connecting to PostgreSQL: {e}")
            raise

    def get_engine(self):
        return self.engine