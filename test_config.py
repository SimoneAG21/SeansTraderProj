# test_config.py
from helper.xml_config_manager import ConfigManager

config = ConfigManager("config/combined_config.xml")
print("Log dir:", config.log_dir_name)  # logs
print("Processes:", config.get_processes())  # List of process dicts
print("Menu:", config.get_menu_structure())  # Filtered menu
print("Templates:", config.templates)  # Templates dict