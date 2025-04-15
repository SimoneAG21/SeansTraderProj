#P:\DynaPOD\proj\trader\test\test_config_manager.py
#(venv) PS P:\DynaPOD\proj\trader> clear; pytest tests/test_config_manager.py -v

import pytest
from helper.xml_config_manager import ConfigManager

@pytest.fixture
def config():
    ConfigManager._instance = None
    return ConfigManager('tests/combined_config_test.xml')

def test_singleton_pattern(config):
    config1 = ConfigManager('tests/combined_config_test.xml')
    config2 = ConfigManager('tests/combined_config_test.xml')
    assert config1 is config2, 'Singleton instances differ'
    config1.test_attr = 'test'
    assert config2.test_attr == 'test', 'Singleton state not shared'

def test_get_with_default_isolated():
    config = ConfigManager('tests/combined_config_test.xml')
    result = config.get_with_default("logging", "missing", default="default")
    print(f"Isolated get_with_default: {result}")
    assert result == "default", "Isolated default fallback failed"

def test_settings_parsing(config):
    print(f"Initial self._defaults in test: {config._defaults}")
    assert config.get("logging", "log_dir_name") == "logs", "Failed to get log_dir_name"
    returned_value = config.get_with_default("logging", "missing", default="default")
    print(f"Returned value from get_with_default: {returned_value}")
    assert returned_value == "default", "Failed default fallback"
    
def test_type_conversion(config):
    assert isinstance(config.get("constants", "max_retries"), int), "max_retries not int"
    assert config.get("constants", "max_retries") == 2, "max_retries value incorrect"
    assert isinstance(config.get("constants", "is_test_mode"), bool), "is_test_mode not bool"
    assert config.get("constants", "is_test_mode") is True, "is_test_mode value incorrect"
    
def test_hierarchical_attributes(config):
    fetch = next(p for p in config.get_processes() if p.get('id') == 'fetch')
    assert fetch['interval'] == ('60', 'integer'), "fetch interval incorrect"
    assert fetch['enabled'] == ('true', 'boolean'), "fetch enabled incorrect"
    
def test_hierarchical_attributes_generic(config):
    processes = config.get_section("processes")
    fetch = next(p for p in processes if p.get('id') == 'fetch')
    assert fetch['interval'] == ('60', 'integer'), "fetch interval incorrect"
    assert fetch['enabled'] == ('true', 'boolean'), "fetch enabled incorrect"