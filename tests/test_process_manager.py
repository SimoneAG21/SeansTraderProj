# tests/test_process_manager.py
import pytest
from helper.process_manager import ProcessManager
from helper.config_manager import ConfigManager
import time

@pytest.fixture
def process_manager():
    pm = ProcessManager(log_file="logs/test.log")  # log_file for set_log_file
    yield pm
    pm.stop_scheduler()

def test_start_continuous_process(process_manager):
    def dummy_script():
        time.sleep(1)
    process_manager.start_process("dummy_script", dummy_script)
    assert "dummy_script" in process_manager.get_status()
    assert process_manager.get_status()["dummy_script"] == "running"
    time.sleep(2)

def test_start_scheduled_process(process_manager):
    def dummy_script():
        pass
    process_manager.start_process("scheduled_script", dummy_script, schedule_minutes=5)
    assert "scheduled_script" in process_manager.get_status()
    assert process_manager.get_status()["scheduled_script"] == "scheduled"

def test_duplicate_process_warning(process_manager):
    def dummy_script():
        time.sleep(1)
    process_manager.start_process("duplicate_script", dummy_script)
    process_manager.start_process("duplicate_script", dummy_script)
    assert len(process_manager.processes) == 1
    time.sleep(2)