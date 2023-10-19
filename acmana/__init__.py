import logging.config

from acmana import config

logging.config.dictConfig(config.config["Logging"])
