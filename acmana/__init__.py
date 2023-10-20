import logging.config
import os
import coloredlogs
import yaml

with open("config.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# logging.config.dictConfig(config["Logging"])

os.mkdir("acmana/tmp") if not os.path.exists("acmana/tmp") else None

coloredlogs.install(
    level=config["coloredlogs"]["level"],
    fmt=config["coloredlogs"]["fmt"],
)
