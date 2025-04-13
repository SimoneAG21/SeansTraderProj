import datetime
import json
import xml.etree.ElementTree as ET
import logging
import os

class ConfigManager:
    _instance = None
    _defaults = {
        "logging": {
            "log_dir_name": "logs",
            "logger_name": "MyLogger",
            "log_gen_level": "DEBUG",
            "log_file_name": "application.log",
            "log_file_max_bytes": 10485760,
            "log_file_backup_count": 5,
            "log_file_level": "DEBUG",
            "log_stream_level": "INFO",
            "logfile_file_format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "logstream_format": "%(name)s - %(levelname)s - %(message)s"
        },
        "constants": {
            "max_retries": 3,
            "default_leverage": 2.5,
            "app_name": "SeanTrade",
            "is_test_mode": True,
            "supported_timeframes": ["1m", "5m", "1h"],
            "exchange_fees": {"maker": 0.001, "taker": 0.002}
        }
    }
    CONVERT_FUNC = {
        'integer': int,
        'float': float,
        'boolean': lambda x: x.lower() in ('true', '1'),
        'date': lambda x: datetime.datetime.strptime(x, '%Y-%m-%d').date(),
        'list': json.loads,
        'string': str
    }

    def __new__(cls, filename="config/combined_config.xml", logger=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.filename = filename
            cls._instance.settings = {}
            cls._instance.menu_structure = {}
            cls._instance.processes = []
            cls._instance.templates = {}
            cls._instance.logger = logger or logging.getLogger("ConfigManager")
            cls._instance.load()
            cls._instance._set_attributes()
        return cls._instance

    def load(self):
        try:
            tree = ET.parse(self.filename)
            root = tree.getroot()
            self.settings.clear()
            self.menu_structure.clear()
            self.processes.clear()
            self.templates.clear()
            for section in root:
                if section.tag == "include":
                    include_file = section.get('file')
                    include_tree = ET.parse(include_file)
                    include_root = include_tree.getroot()
                    if include_root.tag == "processes":
                        self.processes.extend(self._parse_processes(include_root))
                    elif include_root.tag == "menu":
                        self.menu_structure.update(self._parse_menu_items(include_root))
                    elif include_root.tag == "templates":
                        self.templates.update(self._parse_templates(include_root))
                    else:
                        self.settings[include_root.tag] = {}
                        self._parse_section(include_root, self.settings[include_root.tag])
                elif section.tag == "menu":
                    self.menu_structure = self._parse_menu_items(section)
                elif section.tag == "processes":
                    self.processes.extend(self._parse_processes(section))
                elif section.tag == "templates":
                    self.templates = self._parse_templates(section)
                else:
                    self.settings[section.tag] = {}
                    self._parse_section(section, self.settings[section.tag])
            self.logger.info("Configuration loaded successfully")
            self.logger.debug(f"Loaded configuration: {self.settings}, Processes: {self.processes}, Templates: {self.templates}")
        except FileNotFoundError as e:
            self.logger.error(f"Could not find configuration file '{self.filename}'. Details: {e}")
            raise FileNotFoundError(f"Configuration file '{self.filename}' not found.")
        except ET.ParseError as e:
            self.logger.error(f"Invalid XML in configuration file '{self.filename}'. Details: {e}")
            raise ET.ParseError(f"Failed to parse '{self.filename}'.")
        except Exception as e:
            self.logger.error(f"Unexpected error loading configuration: {e}")
            raise

    def _parse_section(self, element, current_dict):
        tag_counts = {}
        for child in element:
            tag = child.tag
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
            if tag == "setting":
                name = child.get('name')
                value = child.get('value')
                value_type = child.get('type')
                current_dict[name] = (value, value_type)
            elif tag in ("sql", "script"):
                current_dict[tag] = {child.get('name'): child.text.strip() if child.text else ""}
            else:
                if tag_counts[tag] > 1 and tag not in current_dict:
                    current_dict[tag] = []
                elif tag_counts[tag] == 1 and tag not in current_dict:
                    current_dict[tag] = {}
                
                if isinstance(current_dict[tag], list):
                    sub_dict = {}
                    self._parse_section(child, sub_dict)
                    current_dict[tag].append(sub_dict)
                else:
                    self._parse_section(child, current_dict[tag])

    def _parse_templates(self, root):
        templates = {}
        for template in root.findall('template'):
            template_id = template.get('id')
            template_dict = {}
            self._parse_section(template, template_dict)
            templates[template_id] = template_dict
        return templates

    def _parse_processes(self, root):
        processes = []
        env = 'test' if self.get_with_default('constants', 'is_test_mode', True) else 'prod'
        for process in root.findall('process'):
            process_dict = {}
            for attr, value in process.attrib.items():
                if attr != 'id' and attr != 'template' and not attr.startswith('type_'):
                    type_key = f'type_{attr}'
                    value_type = process.get(type_key, 'string')
                    process_dict[attr] = (value, value_type)
            if process.get('id'):
                process_dict['id'] = process.get('id')
            template_id = process.get('template')
            if template_id and template_id in self.templates:
                for key, value in self.templates[template_id].items():
                    if key not in process_dict:
                        process_dict[key] = value
            for child in process:
                if child.tag == "condition" and child.get('env') == env:
                    self._parse_section(child, process_dict)
                elif child.tag == "setting":
                    name = child.get('name')
                    value = child.get('value')
                    value_type = child.get('type')
                    process_dict[name] = (value, value_type)
                elif child.tag in ("sql", "script"):
                    process_dict[child.tag] = {child.get('name'): child.text.strip() if child.text else ""}
            processes.append(process_dict)
        return processes

    def _parse_menu_items(self, root):
        menu_structure = {}
        if root.tag == 'menu':
            for item in root:
                if item.tag == 'menu' and item.get('name'):
                    name = item.get('name')
                    help_text = item.find('help').text if item.find('help') is not None else ''
                    menu_structure[name] = {'help': help_text, 'type': 'menu'}
                    for child in item:
                        if child.tag in ['menu', 'item']:
                            child_name = child.get('name')
                            if not child_name:
                                continue
                            child_help = child.find('help').text if child.find('help') is not None else ''
                            submenu = child.find('submenu')
                            if child.tag == 'menu' and len(list(child)) > 0:
                                submenu_items = self._parse_menu_items(child)
                                menu_structure[name][child_name] = {
                                    'help': child_help, 'submenu': submenu_items, 'type': child.tag
                                }
                            elif submenu is not None:
                                submenu_items = self._parse_menu_items(submenu)
                                menu_structure[name][child_name] = {
                                    'help': child_help, 'submenu': submenu_items, 'type': child.tag
                                }
                            else:
                                params = {}
                                for param in child.findall('param'):
                                    param_name = param.get('name')
                                    default = param.get('default')
                                    param_type = param.get('type')
                                    params[param_name] = {'default': default, 'type': param_type}
                                menu_structure[name][child_name] = {
                                    'help': child_help, 'params': params, 'type': child.tag
                                }
                elif item.tag == 'item':
                    name = item.get('name')
                    if not name:
                        continue
                    help_text = item.find('help').text if item.find('help') is not None else ''
                    params = {}
                    for param in child.findall('param'):
                        param_name = param.get('name')
                        default = param.get('default')
                        param_type = param.get('type')
                        params[param_name] = {'default': default, 'type': param_type}
                    menu_structure[name] = {'help': help_text, 'params': params, 'type': item.tag}
        return menu_structure

    def get_menu_structure(self):
        if 'Main' in self.menu_structure:
            return {'Main': {k: v for k, v in self.menu_structure['Main'].items() if k in ['Trading', 'Settings', 'Exit']}}
        return {'Main': self.menu_structure}

    def get_processes(self):
        return self.processes

    def get(self, *path):
        current = self.settings
        for key in path:
            current = current[key]
            if isinstance(current, tuple):
                value, value_type = current
                return self.CONVERT_FUNC.get(value_type, str)(value)
        raise KeyError(f"Setting not found at path: {path}")

    def get_with_default(self, *path, default=None):
        try:
            return self.get(*path)
        except KeyError:
            if path and path[0] in self._defaults:
                current = self._defaults[path[0]]
                for key in path[1:]:
                    current = current.get(key, default) if isinstance(current, dict) else default
                return current
            return default

    def _set_attributes(self):
        for section in ["logging", "constants"]:
            section_defaults = self._defaults.get(section, {})
            for key in section_defaults:
                setattr(self, key, self.get_with_default(section, key, default=section_defaults[key]))

    def reload(self):
        self.load()
        self._set_attributes()