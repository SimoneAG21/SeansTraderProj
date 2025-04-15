"""
Test suite for the abstract database system in TradingV1, verifying PostgreSQL and SQLite
handler functionality using the Abstract Factory pattern.

This file tests helper/abstract_database.py, ensuring handlers and factories work with
tests/combined_config_test.yaml. Compatible with existing app.py, telegram_fetch.py.

How to Run Tests:
- All Tests: `pytest tests/test_abstract_database.py -v`
- Single Test: `pytest tests/test_abstract_database.py::test_sqlite_handler -v`
- Coverage: `pytest tests/test_abstract_database.py --cov=helper --cov-report=html`
"""

import pytest
from unittest.mock import MagicMock, patch
from helper.abstract_database import (
    AbstractDatabaseHandler,
    PostgresHandler,
    SQLiteHandler,
    get_database_factory
)
from helper.config_manager import ConfigManager
from helper.Logger import Logging

@pytest.fixture
def mock_config():
    """Fixture for a ConfigManager with SQLite config."""
    config = ConfigManager()
    config._data = {
        "database": {
            "type": "sqlite",
            "path": ":memory:"
        }
    }
    return config

@pytest.fixture
def mock_postgres_config():
    """Fixture for a ConfigManager with PostgreSQL config."""
    config = ConfigManager()
    config._data = {
        "database": {
            "type": "postgresql",
            "user": "test_user",
            "password": "test_pass",
            "host": "localhost",
            "port": "5432",
            "database": "test_db"
        }
    }
    return config

@pytest.fixture
def logger(mock_config):
    """Fixture for a Logging instance."""
    logger = Logging(mock_config, instance_id="test_abstract_database")
    yield logger
    logger.close_log()

def test_sqlite_handler(mock_config, logger):
    """Test SQLiteHandler creates engine and tests connection."""
    with patch("helper.abstract_database.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        handler = SQLiteHandler(mock_config, logger)
        handler.create_engine()
        assert handler.engine is not None
        mock_create_engine.assert_called_once_with("sqlite:///:memory:")
        with patch.object(mock_engine, "connect") as mock_connect:
            mock_connect.return_value.__enter__.return_value = MagicMock()
            handler.test_connection()
            mock_connect.assert_called_once()

def test_postgres_handler(mock_postgres_config, logger):
    """Test PostgresHandler creates engine and tests connection."""
    with patch("helper.abstract_database.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        handler = PostgresHandler(mock_postgres_config, logger)
        handler.create_engine()
        assert handler.engine is not None
        expected_url = (
            "postgresql+psycopg2://test_user:test_pass@localhost:5432/test_db"
        )
        mock_create_engine.assert_called_once_with(expected_url)
        with patch.object(mock_engine, "connect") as mock_connect:
            mock_connect.return_value.__enter__.return_value = MagicMock()
            handler.test_connection()
            mock_connect.assert_called_once()

def test_factory_selection_sqlite(mock_config, logger):
    """Test factory creates SQLiteHandler for sqlite config."""
    factory = get_database_factory(mock_config, logger)
    handler = factory.create_handler(mock_config, logger)
    assert isinstance(handler, SQLiteHandler)
    assert handler.config == mock_config
    assert handler.logger == logger

def test_factory_selection_postgres(mock_postgres_config, logger):
    """Test factory creates PostgresHandler for postgresql config."""
    factory = get_database_factory(mock_postgres_config, logger)
    handler = factory.create_handler(mock_postgres_config, logger)
    assert isinstance(handler, PostgresHandler)
    assert handler.config == mock_postgres_config
    assert handler.logger == logger

def test_invalid_config_type(mock_config, logger):
    """Test invalid config type raises TypeError."""
    with pytest.raises(TypeError):
        PostgresHandler("not_config", logger)

def test_invalid_logger_type(mock_config):
    """Test invalid logger type raises TypeError."""
    with pytest.raises(TypeError):
        SQLiteHandler(mock_config, "not_logger")

def test_missing_config_key(mock_postgres_config, logger):
    """Test missing PostgreSQL config keys raises ValueError."""
    mock_postgres_config._data = {"database": {"type": "postgresql"}}
    with pytest.raises(ValueError):
        handler = PostgresHandler(mock_postgres_config, logger)
        handler.create_engine()

def test_unsupported_db_type(mock_config, logger):
    """Test unsupported database type raises ValueError."""
    mock_config._data = {"database": {"type": "mysql"}}
    with pytest.raises(ValueError, match="Unsupported database type: mysql"):
        get_database_factory(mock_config, logger)