import logging.config
import os
import coloredlogs
import yaml

with open("config.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# logging.config.dictConfig(config["Logging"])

os.makedirs("acmana/tmp/cache", exist_ok=True)

coloredlogs.install(
    level=config["coloredlogs"]["level"],
    fmt=config["coloredlogs"]["fmt"],
)
