"""Devtools and utils for debugging"""

import logging
import os
import timeit
from typing import TYPE_CHECKING

from xdg import BaseDirectory

from ..config import APP_SETTINGS

if TYPE_CHECKING:
    pass

dap_conn = None
DAP_PORT = 5678

if APP_SETTINGS.debug:
    def notify(msg: str) -> None:
        pass
        #DEBUG:
        # call a system command `dunstify` to send`
        # subprocess.call(['dunstify', '-u', 'critical', msg])
else:
    def notify(msg: str) -> None:
        pass

class ExecutionTimer:
    """A context manager to time code execution."""
    def __init__(self, name: str) -> None:
        self.name = name
        self.start = None
        self.end = None

    def __enter__(self) -> None:
        if APP_SETTINGS.debug:
            self.start = timeit.default_timer()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if APP_SETTINGS.debug:
            self.end = timeit.default_timer()
            execution_time = self.end - self.start
            print(f"Total execution time for {self.name}: {execution_time} seconds.")

def get_dbg_path() -> str:
    """Returns the debug path"""
    return BaseDirectory.save_cache_path("instrukt")

def dap_listen() -> bool:
    import debugpy
    global dap_conn
    if dap_conn is None:
        dap_conn = debugpy.listen(DAP_PORT)
        return True
    return False

def log_llm_output(msg: str) -> None:
    """Logs the msg to the file"""
    debug_path = BaseDirectory.save_cache_path("instrukt")
    debug_file = os.path.join(debug_path, "debug_llm_output.log")
    with open(debug_file, "a") as f:
        f.write(msg + "\n")


def dbg_file_logger() -> None:
    """Returns a file based logger"""
    debug_path = BaseDirectory.save_cache_path("instrukt")
    debug_file = os.path.join(debug_path, "debug.log")
    logger = logging.getLogger("instrukt_dbg_file")
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(debug_file)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
