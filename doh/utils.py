import logging
import os

from rich.logging import RichHandler


def setup_logging():
    lvl = logging.DEBUG if "DEBUG" in os.environ else logging.INFO

    FORMAT = "%(message)s"
    logging.basicConfig(
        level=lvl, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
    )
