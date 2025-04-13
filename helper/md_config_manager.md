# ConfigManager Feature List

This document outlines all features of the `ConfigManager` class in `helper/config_manager.py`, providing a contractual specification for the TradingV1 project. Each feature includes a description, usage instructions, and test cases to ensure functionality.

## 1. Singleton Pattern

**Description**: Ensures a single instance of `ConfigManager` to centralize configuration access across the application, preventing redundant parsing and ensuring consistent state.

**Usage**:
- **Python**: Instantiate with `ConfigManager(filename="config/combined_config.xml")`. Subsequent calls return the same instance.
- **XML**: No specific structure required.
- **Example**:
  ```python
  config1 = ConfigManager("config/combined_config.xml")
  config2 = ConfigManager("config/combined_config.xml")
  # config1 is config2
  config1.some_attribute = "value"
  print(config2.some_attribute)  # Outputs: value
  ```

**Test Cases**:
- Verify instances are identical:
  ```python
  config1 = ConfigManager("config/combined_config.xml")
  config2 = ConfigManager("config/combined_config.xml")
  assert config1 is config2, "Singleton instances differ"
  ```
- Check state sharing:
  ```python
  config1.test_attr = "test"
  assert config2.test_attr == "test", "Singleton state not shared"
  ```

## 2. Settings Parsing with Nested Paths

**Description**: Parses XML `<setting>` tags into a nested dictionary, accessible via dot-separated paths, supporting flexible configuration retrieval with defaults.

**Usage**:
- **XML**: Define `<setting name="key" value="val" type="type"/>` in sections like `<logging>`, `<constants>`.
- **Python**: Use `config.get(section, key)` or `config.get_with_default(section, key, default)`.
- **Example**:
  ```xml
  <logging>
      <setting name="log_dir_name" value="logs" type="string"/>
  </logging>
  ```
  ```python
  log_dir = config.get("logging", "log_dir_name")  # Returns "logs"
  missing = config.get_with_default("logging", "missing", "default")  # Returns "default"
  ```

**Test Cases**:
- Retrieve setting:
  ```python
  assert config.get("logging", "log_dir_name") == "logs", "Failed to get log_dir_name"
  ```
- Check default fallback:
  ```python
  assert config.get_with_default("logging", "missing", "default") == "default", "Failed default fallback"
  ```

## 3. Type Conversion

**Description**: Converts XML setting values to native Python types (integer, float, boolean, date, list, string) based on the `type` attribute, ensuring correct data handling.

**Usage**:
- **XML**: Specify `type="integer|float|boolean|date|list|string"` in `<setting>`.
- **Python**: `config.get()` returns the converted value.
- **Example**:
  ```xml
  <constants>
      <setting name="max_retries" value="2" type="integer"/>
      <setting name="is_test_mode" value="true" type="boolean"/>
  </constants>
  ```
  ```python
  retries = config.get("constants", "max_retries")  # Returns 2 (int)
  test_mode = config.get("constants", "is_test_mode")  # Returns True (bool)
  ```

**Test Cases**:
- Verify integer conversion:
  ```python
  assert isinstance(config.get("constants", "max_retries"), int), "max_retries not int"
  assert config.get("constants", "max_retries") == 2, "max_retries value incorrect"
  ```
- Verify boolean conversion:
  ```python
  assert isinstance(config.get("constants", "is_test_mode"), bool), "is_test_mode not bool"
  assert config.get("constants", "is_test_mode") is True, "is_test_mode value incorrect"
  ```

## 4. Hierarchical Attributes

**Description**: Parses `<process>` tag attributes as configuration settings, with `type_<attr>` attributes specifying data types, enabling concise process definitions.

**Usage**:
- **XML**: Define attributes like `interval="60" type_interval="integer"` in `<process>`.
- **Python**: Access via `config.get_processes()[index][key]`.
- **Example**:
  ```xml
  <processes>
      <process id="fetch" interval="60" type_interval="integer" enabled="true" type_enabled="boolean"/>
  </processes>
  ```
  ```python
  fetch = next(p for p in config.get_processes() if p.get('id') == 'fetch')
  # {'id': 'fetch', 'interval': ('60', 'integer'), 'enabled': ('true', 'boolean')}
  ```

**Test Cases**:
- Check attribute parsing:
  ```python
  fetch = next(p for p in config.get_processes() if p.get('id') == 'fetch')
  assert fetch['interval'] == ('60', 'integer'), "fetch interval incorrect"
  assert fetch['enabled'] == ('true', 'boolean'), "fetch enabled incorrect"
  ```

## 5. Template-Based Configurations

**Description**: Applies reusable `<template>` settings to `<process>` elements, reducing duplication by merging default settings with process-specific overrides.

**Usage**:
- **XML**: Define `<template id="name">` with `<setting>` tags; reference via `template="name"` in `<process>`.
- **Python**: Template settings appear in `config.get_processes()`.
- **Example**:
  ```xml
  <templates>
      <template id="default_process">
          <setting name="interval" value="60" type="integer"/>
          <setting name="enabled" value="true" type="boolean"/>
      </template>
  </templates>
  <processes>
      <process template="default_process">
          <setting name="priority" value="high" type="string"/>
      </process>
  </processes>
  ```
  ```python
  proc = config.get_processes()[1]
  # {'interval': ('60', 'integer'), 'enabled': ('true', 'boolean'), 'priority': ('high', 'string')}
  ```

**Test Cases**:
- Verify template application:
  ```python
  proc = config.get_processes()[1]
  assert proc['interval'] == ('60', 'integer'), "Template interval not applied"
  assert proc['priority'] == ('high', 'string'), "Template override incorrect"
  ```

## 6. Conditional Configurations

**Description**: Selects process settings based on environment (`test` or `prod`) using `<condition>` tags, controlled by the `is_test_mode` constant, for environment-specific configurations.

**Usage**:
- **XML**: Use `<condition env="test|prod">` with `<setting>` tags inside `<process>`.
- **Python**: Only active environment settings appear in `config.get_processes()`.
- **Example**:
  ```xml
  <processes>
      <process>
          <condition env="test">
              <setting name="interval" value="30" type="integer"/>
              <setting name="mode" value="debug" type="string"/>
          </condition>
          <condition env="prod">
              <setting name="interval" value="300" type="integer"/>
              <setting name="mode" value="optimized" type="string"/>
          </condition>
      </process>
  </processes>
  ```
  ```python
  proc = config.get_processes()[2]  # {'interval': ('30', 'integer'), 'mode': ('debug', 'string')}
  ```

**Test Cases**:
- Check condition filtering:
  ```python
  proc = config.get_processes()[2]
  assert proc['interval'] == ('30', 'integer'), "Test condition interval incorrect"
  assert proc['mode'] == ('debug', 'string'), "Test condition mode incorrect"
  assert 'condition' not in proc, "Inactive condition included"
  ```

## 7. Embedded SQL/Scripts

**Description**: Embeds SQL queries or script snippets within `<sql>` or `<script>` tags in processes, enabling direct storage of executable configurations.

**Usage**:
- **XML**: Use `<sql name="name">` or `<script name="name">` with CDATA for content inside `<process>`.
- **Python**: Access via `config.get_processes()[index]['sql'][name]`.
- **Example**:
  ```xml
  <processes>
      <process>
          <sql name="fetch_messages"><![CDATA[SELECT * FROM telegram_messages WHERE timestamp > NOW() - INTERVAL '1 hour';]]></sql>
      </process>
  </processes>
  ```
  ```python
  sql = config.get_processes()[3]['sql']['fetch_messages']  # SQL query string
  ```

**Test Cases**:
- Verify SQL parsing:
  ```python
  proc = config.get_processes()[3]
  assert 'sql' in proc, "SQL not parsed"
  assert proc['sql']['fetch_messages'].startswith("SELECT *"), "SQL query incorrect"
  ```

## 8. External File Includes

**Description**: Loads additional XML configuration files via `<include>` tags, supporting modular configuration files for scalability.

**Usage**:
- **XML**: Use `<include file="path"/>` to reference files like `config/processes.xml`.
- **Python**: Included settings merge into `config.get_processes()` or other structures.
- **Example**:
  ```xml
  <configuration>
      <include file="config/processes.xml"/>
  </configuration>
  <!-- config/processes.xml -->
  <processes>
      <process id="sync" interval="300" type_interval="integer" timeout="600" type_timeout="integer"/>
  </processes>
  ```
  ```python
  sync = next(p for p in config.get_processes() if p.get('id') == 'sync')
  # {'id': 'sync', 'interval': ('300', 'integer'), 'timeout': ('600', 'integer')}
  ```

**Test Cases**:
- Check include parsing:
  ```python
  sync = next((p for p in config.get_processes() if p.get('id') == 'sync'), None)
  assert sync is not None, "Sync process not included"
  assert sync['interval'] == ('300', 'integer'), "Sync interval incorrect"
  ```

## 9. Menu Structure Parsing

**Description**: Parses hierarchical `<menu>` and `<item>` tags, filtering for `Trading`, `Settings`, and `Exit` under a `Main` menu, suitable for navigation systems.

**Usage**:
- **XML**: Define `<menu name="Main">` with nested `<menu>` or `<item>` tags, including `<param>` for item parameters.
- **Python**: Access via `config.get_menu_structure()`.
- **Example**:
  ```xml
  <menu name="Main">
      <menu name="Trading">
          <item name="Start">
              <param name="amount" default="50.0" type="float"/>
          </item>
      </menu>
      <menu name="Settings"/>
      <menu name="Exit"/>
  </menu>
  ```
  ```python
  menu = config.get_menu_structure()
  # {'Main': {'Trading': {...}, 'Settings': {...}, 'Exit': {...}}}
  ```

**Test Cases**:
- Verify menu structure:
  ```python
  menu = config.get_menu_structure()
  assert 'Main' in menu, "Main menu missing"
  assert set(menu['Main'].keys()) == {'Trading', 'Settings', 'Exit'}, "Menu items incorrect"
  assert 'Start' in menu['Main']['Trading'], "Trading Start item missing"
  ```

## Usage in TradingV1

- **Instantiation**: Create a single `ConfigManager` instance at application start:
  ```python
  from helper.config_manager import ConfigManager
  config = ConfigManager("config/combined_config.xml")
  ```
- **Access Configurations**:
  - Settings: `config.get("section", "key")` for logging, constants, etc.
  - Processes: `config.get_processes()` for trading tasks (`telegram_fetch.py`).
  - Menu: `config.get_menu_structure()` for UI navigation.
- **Integration**:
  - Use in `app.py` for Flask routes.
  - Apply process intervals in `telegram_fetch.py`.
  - Execute SQL queries against Heroku Postgres (`seanstrader` db).

## Test Framework

The features are verified by `test_config_manager.py`, a `unittest`-based suite located in the project root. Run it to ensure all functionality:
```bash
python test_config_manager.py
```

This suite covers all test cases listed above, ensuring `ConfigManager` meets its contractual obligations.

## Embedding Documentation

To include this feature list in `config_manager.py`, add the following docstring at the class level:

```python
class ConfigManager:
    """
    ConfigManager provides centralized configuration management for the TradingV1 project,
    parsing XML files with advanced features for flexibility and scalability.

    Features:
    1. **Singleton Pattern**: Ensures a single instance for consistent state.
       - Usage: Instantiate with `ConfigManager(filename)`.
       - Example: `config1 = ConfigManager("config.xml"); config2 = ConfigManager("config.xml")` (same instance).
    2. **Settings Parsing with Nested Paths**: Parses `<setting>` tags into a nested dictionary.
       - Usage: `<setting name="key" value="val" type="type"/>`, access via `config.get(section, key)`.
       - Example: `<setting name="log_dir_name" value="logs"/>`, `config.get("logging", "log_dir_name")`.
    3. **Type Conversion**: Converts values to int, float, bool, date, list, string.
       - Usage: Specify `type="integer"` in `<setting>`, get native type from `config.get()`.
       - Example: `<setting name="max_retries" value="2" type="integer"/>`, returns 2 (int).
    4. **Hierarchical Attributes**: Parses `<process>` attributes as settings.
       - Usage: `<process id="name" interval="60" type_interval="integer"/>`, access via `get_processes()`.
       - Example: Returns `{'id': 'name', 'interval': ('60', 'integer')}`.
    5. **Template-Based Configurations**: Applies reusable `<template>` settings to processes.
       - Usage: `<template id="name">`, `<process template="name"/>`.
       - Example: Merges template settings with process overrides.
    6. **Conditional Configurations**: Selects settings based on `env="test|prod"`.
       - Usage: `<condition env="test">` in `<process>`, controlled by `is_test_mode`.
       - Example: Returns test settings when `is_test_mode=true`.
    7. **Embedded SQL/Scripts**: Stores queries or scripts in `<sql>`/`<script>` tags.
       - Usage: `<sql name="query">...</sql>`, access via `get_processes()[i]['sql']`.
       - Example: `<sql name="fetch_messages">SELECT ...</sql>`.
    8. **External File Includes**: Loads XML files via `<include>`.
       - Usage: `<include file="path"/>`, merges into appropriate structures.
       - Example: `<include file="config/processes.xml"/>`.
    9. **Menu Structure Parsing**: Parses `<menu>` and `<item>` tags, filtering for `Main`.
       - Usage: `<menu name="Main">`, access via `get_menu_structure()`.
       - Example: Returns `{'Main': {'Trading': {...}, ...}}`.

    See `md_config_manager.md` for detailed usage and test cases.
    """
```