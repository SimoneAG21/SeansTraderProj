import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from helper.database import DatabaseHandler
from helper.Logger import Logging
from helper.config_manager import ConfigManager

@pytest.fixture
def mock_config():
    config = ConfigManager()
    config._data = {
        "database": {
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
    logger = Logging(mock_config, instance_id="test_database")
    yield logger
    logger.close_log()

def test_init_success(mock_config, logger):
    with patch("helper.database.create_engine") as mock_create_engine:
        handler = DatabaseHandler(mock_config, logger)
        assert handler.engine is not None
        mock_create_engine.assert_called_once()
        assert handler.config == mock_config
        assert handler.logger == logger

def test_init_invalid_config(logger):
    with pytest.raises(TypeError):
        DatabaseHandler("not_config", logger)

def test_init_invalid_logger(mock_config):
    with pytest.raises(TypeError):
        DatabaseHandler(mock_config, "not_logger")

def test_init_missing_config_key(mock_config, logger):
    mock_config._data = {"database": {}}
    with pytest.raises(ValueError):
        DatabaseHandler(mock_config, logger)

def test_create_engine(mock_config, logger):
    with patch("helper.database.create_engine") as mock_create_engine:
        handler = DatabaseHandler(mock_config, logger)
        expected_url = (
            "postgresql+psycopg2://test_user:test_pass@localhost:5432/test_db"
        )
        mock_create_engine.assert_called_once_with(expected_url)

def test_test_connection_success(mock_config, logger):
    with patch("helper.database.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        handler = DatabaseHandler(mock_config, logger)
        with patch.object(mock_engine, "connect") as mock_connect:
            handler._test_connection()
            mock_connect.assert_called_once()

def test_test_connection_failure(mock_config, logger):
    with patch("helper.database.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_create_engine.return_value = mock_engine
        handler = DatabaseHandler(mock_config, logger)
        with patch.object(mock_engine, "connect") as mock_connect:
            mock_connect.side_effect = Exception("Connection failed")
            with pytest.raises(Exception, match="Connection failed"):
                handler._test_connection()

def test_get_engine(mock_config, logger):
    with patch("helper.database.create_engine") as mock_create_engine:
        mock_engine = MagicMock()
        mock_connection = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        handler = DatabaseHandler(mock_config, logger)
        assert handler.get_engine() == mock_engine