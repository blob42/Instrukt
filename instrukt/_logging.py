import logging
import sys
from logging import Handler, LogRecord

from textual._context import active_app
# from textual.logging import TextualHandler

from .console_capture import (
    ConsoleFilter,
    ErrorF,
    LangchainF,
    IndexCreationF,
)

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
        except LookupError:
            if self._stderr:
                print(message, file=sys.stderr)
            elif self._stdout:
                print(message, file=sys.stdout)
        else:
            if record.levelno >= self.level:
                app._print(message)
            else:
                app.log.logging(message)

def setup_logging():

    log_capture_handler.setFormatter(ConsoleFilter.formatter)
    log_capture_handler.setLevel(logging.INFO)

    filter = IndexCreationF() | LangchainF() | ErrorF()
    log_capture_handler.addFilter(filter)

    # add Textual dev console handler
    logging.basicConfig(
        level=logging.DEBUG,
        # handlers=[TextualHandler()],
        handlers=[log_capture_handler],
    )


    # silence markdown-it
    mdlogger = logging.getLogger("markdown_it")
    mdlogger.setLevel("CRITICAL")

    # silence chromadb
    chromadb = logging.getLogger("chromadb")
    chromadb.setLevel("INFO")

    openai = logging.getLogger("openai")
    openai.setLevel("INFO")

    pdfminer = logging.getLogger("pdfminer")
    pdfminer.setLevel("INFO")


ANSI_ESCAPE_RE = r"\x1b\[[AB]"
log_capture_handler = LogCaptureHandler()
