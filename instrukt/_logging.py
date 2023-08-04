import typing as t
import logging
import sys

from textual._context import active_app
from textual.logging import TextualHandler
from logging import Handler, LogRecord, Filter
from .console_capture import ( SentenceTransformersFilter )


# def sentence_transformers_filter(record: LogRecord) -> bool:
#     return record.name.startswith("sentence_transformers")

class LogCaptureHandler(Handler):
    """A Logging handler for Textual apps."""

    def __init__(self, stderr: bool = True, stdout: bool = False) -> None:
        """Capture log and redirects it back to Textual for print capture."""
        super().__init__()
        self._stderr = stderr
        self._stdout = stdout

    def emit(self, record: LogRecord) -> None:
        """Invoked by logging."""
        message = self.format(record)
        try:
            app = active_app.get()
            app._print(message)
        except LookupError:
            if self._stderr:
                print(message, file=sys.stderr)
            elif self._stdout:
                print(message, file=sys.stdout)



def setup_logging():
    log_ch = LogCaptureHandler()
    st_filter = SentenceTransformersFilter()

    log_ch.setFormatter(st_filter.formatter)
    log_ch.addFilter(st_filter)
    # add Textual dev console handler
    logging.basicConfig(
        level="DEBUG",
        # handlers=[TextualHandler(), log_capture_handler],
        handlers=[log_ch, TextualHandler()],
    )

    # silence markdown-it
    mdlogger = logging.getLogger("markdown_it")
    mdlogger.setLevel("CRITICAL")

    # silence chromadb
    chromadb = logging.getLogger("chromadb")
    chromadb.setLevel("INFO")
