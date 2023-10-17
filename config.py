import logging.config

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from contest.nowcoder_contest import NowcoderContest
from contest.vjudge_contest import VjudgeContest
from contestant.nowcoder_contestant import NowcoderContestant
from contestant.vjudge_contestant import VjudgeContestant
from ranking.nowcoder_ranking import NowcoderRanking
from ranking.vjudge_ranking import VjudgeRanking

engine = create_engine("sqlite:///data/sqlite_data.db", echo=False)
SessionMaker = sessionmaker(bind=engine)
sqlsession = SessionMaker()

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
