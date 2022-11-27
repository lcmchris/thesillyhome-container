import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from traceback import format_exception

# Local application imports
from thesillyhome.model_creator.home import homedb


def add_logger():
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logname = "/thesillyhome_src/log/thesillyhome.log"

    # setup logging to file
    filelog = TimedRotatingFileHandler(
        logname, when="midnight", interval=1, backupCount=3
    )
    fileformatter = logging.Formatter(FORMAT)
    filelog.setLevel(logging.DEBUG)
    filelog.setFormatter(fileformatter)
    logger.addHandler(filelog)

    # setup logging to console
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    formatter = logging.Formatter(FORMAT)
    console.setFormatter(formatter)
    logger.addHandler(console)

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback)
        )

    sys.excepthook = handle_exception
