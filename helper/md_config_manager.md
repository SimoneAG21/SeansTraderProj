ConfigManager Feature List
This document outlines all features of the ConfigManager class in helper/config_manager.py, providing a contractual specification for the TradingV1 project. Each feature includes a description, usage instructions with YAML examples, and test cases to ensure functionality. The configuration is loaded from YAML files, such as tests/combined_config_test.yaml and included files like tests/processes.yaml.
1. Singleton-Like Pattern
Description: Ensures consistent configuration access by maintaining state for a given YAML file, reusable across threads. New instances can be created for different files (e.g., test vs. prod configs).
Usage:

Python: Instantiate with ConfigManager(filename="tests/combined_config_test.yaml"). The instance retains state for that file.
YAML: No specific structure required.
Example:config1 = ConfigManager("tests/combined_config_test.yaml")
config2 = ConfigManager("tests/combined_config_test.yaml")
config1.some_attribute = "value"
print(config2.some_attribute)  # Outputs: value



Test Cases:

Verify initialization:assert config.get("logging", "log_dir_name") == "logs", "Singleton not initialized"


Check state sharing:config.test_attr = "test"
assert config.test_attr == "test", "State not preserved"



2. Settings Parsing with Nested Paths
Description: Parses YAML key-value pairs into a nested dictionary, accessible via section and key, supporting flexible retrieval with defaults.
Usage:

YAML: Define keys under sections (e.g., logging, constants) with value and type.logging:
  log_dir_name:
    value: logs
    type: string


Python: Use config.get(section, key) or config.get_with_default(section, key, default).
Example:log_dir = config.get("logging", "log_dir_name")  # Returns "logs"
missing = config.get_with_default("logging", "missing", "default")  # Returns "default"



Test Cases:

Retrieve setting:assert config.get("logging", "log_dir_name") == "logs", "Failed to get log_dir_name"


Check default fallback:assert config.get_with_default("logging", "missing", "default") == "default", "Failed default fallback"



3. Type Conversion
Description: Converts YAML setting values to native Python types (integer, boolean, float, string) based on the type field, ensuring correct data handling.
Usage:

YAML: Specify type for settings under sections.constants:
  max_retries:
    value: 2
    type: integer
  is_test_mode:
    value: true
    type: boolean


Python: config.get() returns the converted value.
Example:retries = config.get("constants", "max_retries")  # Returns 2 (int)
test_mode = config.get("constants", "is_test_mode")  # Returns True (bool)



Test Cases:

Verify integer conversion:assert isinstance(config.get("constants", "max_retries"), int), "max_retries not int"
assert config.get("constants", "max_retries") == 2, "max_retries value incorrect"


Verify boolean conversion:assert isinstance(config.get("constants", "is_test_mode"), bool), "is_test_mode not bool"
assert config.get("constants", "is_test_mode") is True, "is_test_mode value incorrect"



4. Hierarchical Attributes
Description: Parses process attributes (e.g., interval, enabled) as dictionaries with value and type, enabling structured task configurations.
Usage:

YAML: Define processes with attributes under processes.processes:
  - id: fetch
    interval:
      value: 60
      type: integer
    enabled:
      value: true
      type: boolean


Python: Access via config.get_processes() or config.get_section("processes").
Example:fetch = next(p for p in config.get_processes() if p.get("id") == "fetch")
# Returns {"id": "fetch", "interval": {"value": 60, "type": "integer"}, ...}



Test Cases:

Check attribute parsing:fetch = next(p for p in config.get_processes() if p.get("id") == "fetch")
assert fetch["interval"]["value"] == 60, "fetch interval incorrect"
assert fetch["enabled"]["value"] is True, "fetch enabled incorrect"



5. Template-Based Configurations
Description: Applies reusable template settings to processes, merging with process-specific overrides to reduce duplication.
Usage:

YAML: Define templates with settings; reference via template key in processes.templates:
  default_process:
    interval:
      value: 60
      type: integer
    enabled:
      value: true
      type: boolean
processes:
  - template: default_process
    priority:
      value: high
      type: string


Python: Template settings appear in config.get_processes().
Example:proc = next(p for p in config.get_processes() if p.get("priority"))
# Returns {"interval": {"value": 60, ...}, "enabled": {"value": true, ...}, "priority": ...}



Test Cases:

Verify template application:proc = next(p for p in config.get_processes() if p.get("priority"))
assert proc["interval"]["value"] == 60, "Template interval not applied"
assert proc["priority"]["value"] == "high", "Template override incorrect"



6. Conditional Configurations
Description: Selects process settings based on is_test_mode (true for test, false for prod), enabling environment-specific configurations.
Usage:

YAML: Use conditions with test/prod keys in processes.processes:
  - conditions:
      test:
        interval:
          value: 30
          type: integer
        mode:
          value: debug
          type: string
      prod:
        interval:
          value: 300
          type: integer
        mode:
          value: optimized
          type: string


Python: Settings for active environment appear in config.get_processes().
Example:proc = next(p for p in config.get_processes() if p.get("mode"))
# Returns {"interval": {"value": 30, ...}, "mode": {"value": "debug", ...}} if is_test_mode=true



Test Cases:

Check condition merging:proc = next(p for p in config.get_processes() if p.get("mode"))
assert proc["interval"]["value"] == 30, "Test condition interval incorrect"
assert proc["mode"]["value"] == "debug", "Test condition mode incorrect"



7. Embedded SQL/Scripts
Description: Stores SQL queries within processes under sql keys, supporting database operations.
Usage:

YAML: Define sql with named queries in processes.processes:
  - interval:
      value: 120
      type: integer
    sql:
      fetch_messages: |
        SELECT * FROM telegram_messages WHERE timestamp > NOW() - INTERVAL '1 hour';


Python: Access via config.get_processes()[index]["sql"][name].
Example:proc = next(p for p in config.get_processes() if p.get("sql"))
sql = proc["sql"]["fetch_messages"]  # Returns SQL query string



Test Cases:

Verify SQL parsing:proc = next(p for p in config.get_processes() if p.get("sql"))
assert "sql" in proc, "SQL not parsed"
assert proc["sql"]["fetch_messages"].startswith("SELECT *"), "SQL query incorrect"



8. External File Includes
Description: Merges processes from external YAML files listed in includes, supporting modular configurations.
Usage:

YAML: Specify includes with file paths.includes:
  - tests/processes.yaml

# tests/processes.yaml
processes:
  - id: sync
    interval:
      value: 300
      type: integer
    timeout:
      value: 600
      type: integer


Python: Included processes appear in config.get_processes().
Example:sync = next(p for p in config.get_processes() if p.get("id") == "sync")
# Returns {"id": "sync", "interval": {"value": 300, ...}, ...}



Test Cases:

Check include merging:sync = next(p for p in config.get_processes() if p.get("id") == "sync")
assert sync["interval"]["value"] == 300, "Sync interval incorrect"
assert sync["timeout"]["value"] == 600, "Sync timeout incorrect"



9. Menu Structure Parsing
Description: Parses hierarchical menu settings for UI navigation, focusing on Main with Trading, Settings, and Exit.
Usage:

YAML: Define menu with nested structure.menu:
  Main:
    Trading:
      help: Test trading menu
      Start:
        help: Start test trade
        params:
          amount:
            default: 50.0
            type: float
    Settings:
      help: Test settings
    Exit:
      help: Exit test


Python: Access via config.get_section("menu").
Example:menu = config.get_section("menu")
# Returns {"Main": {"Trading": {"Start": {"params": {"amount": ...}}, ...}, ...}}



Test Cases:

Verify menu structure:menu = config.get_section("menu")
assert "Main" in menu, "Main menu missing"
assert menu["Main"]["Trading"]["Start"]["params"]["amount"]["default"] == 50.0, "Trading Start amount incorrect"



Usage in TradingV1

Instantiation: Create a ConfigManager instance at app start:from helper.config_manager import ConfigManager
config = ConfigManager("tests/combined_config_test.yaml")


Access Configurations:
Settings: config.get("logging", "log_dir_name") for logs, constants.
Processes: config.get_processes() for tasks (e.g., telegram_fetch.py).
Menu: config.get_section("menu") for UI navigation.


Integration:
Flask routes in app.py use get_section("menu").
Task intervals in telegram_fetch.py from get_processes().
Heroku (seanstrader) loads configs for deployment.



Test Framework
Run tests/test_config_manager.py to verify all features:
pytest tests/test_config_manager.py -v

This suite covers all test cases above, ensuring ConfigManager meets its contractual obligations.
Embedding Documentation
To include this feature list in config_manager.py, use its existing docstring, which summarizes these features. Refer to this file for detailed usage and examples.
