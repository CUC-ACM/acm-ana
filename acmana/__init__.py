import logging.config

import config

logging.config.dictConfig(config.config["Logging"])
