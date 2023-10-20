import logging.config

import coloredlogs
import yaml

with open("config.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# logging.config.dictConfig(config["Logging"])


coloredlogs.install(
    level=config["coloredlogs"]["level"],
    fmt=config["coloredlogs"]["fmt"],
)
