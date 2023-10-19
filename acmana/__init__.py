import logging.config

import yaml

with open("config.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

logging.config.dictConfig(config["Logging"])
