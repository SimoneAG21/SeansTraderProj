# helper/process_manager.py
from helper.config_manager import ConfigManager
from helper.Logger import Logging
from apscheduler.schedulers.background import BackgroundScheduler
import threading

class ProcessManager:
    def __init__(self, config_path="config/demo_config.yaml", log_file="logs/app.log"):
        self.processes = {}
        self.config_manager = ConfigManager(config_file=config_path)
        self.config = self.config_manager._data  # Full config
        self.logger = Logging(config=ConfigManager(config_file=config_path), instance_id="process_manager")
        self.logger.set_log_file("app")
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

    def start_process(self, script_name, script_func, schedule_minutes=None):
        if schedule_minutes:
            self.logger.info(f"Scheduling process: {script_name} every {schedule_minutes} minutes")
            self.scheduler.add_job(script_func, "interval", minutes=schedule_minutes, id=script_name)
        else:
            if script_name not in self.processes:
                self.logger.info(f"Starting continuous process: {script_name}")
                thread = threading.Thread(target=script_func, daemon=True)
                thread.start()
                self.processes[script_name] = thread
            else:
                self.logger.warning(f"Process {script_name} already running")

    def get_status(self):
        running_threads = {name: "running" if thread.is_alive() else "stopped"
                          for name, thread in self.processes.items()}
        scheduled_jobs = {job.id: "scheduled" for job in self.scheduler.get_jobs()}
        return {**running_threads, **scheduled_jobs}

    def stop_scheduler(self):
        self.scheduler.shutdown()