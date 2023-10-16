import logging.config

import yaml
from sqlalchemy import create_engine

engine = create_engine("sqlite:///data/sqlite_data.db", echo=False)

with open("config.yaml", "r") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

# ANSI colors
COLORS = (
    "\033[0m",  # End of color
    "\033[36m",  # Cyan
    "\033[91m",  # Red
    "\033[35m",  # Magenta
)

logging.config.dictConfig(config["Logging"])
