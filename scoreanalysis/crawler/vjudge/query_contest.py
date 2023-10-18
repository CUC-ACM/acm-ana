import datetime
import json
import logging
import time

import fake_useragent
import requests

from scoreanalysis import config
from scoreanalysis.models.contest.vjudge_contest import VjudgeContest

logger = logging.getLogger(__name__)


class VjudgeContestRetriever:
    class Contest:
        def __init__(
            self,
            vcontest_id: int,
            name: str,
            begin: datetime.datetime,
            end: datetime.datetime,
        ) -> None:
            self.vcontest_id: int = vcontest_id
            self.name: str = name
            self.begin: datetime.datetime = begin
            self.end: datetime.datetime = end

        def __repr__(self) -> str:
            return f"(vcontest_id: {self.vcontest_id}, name: {self.name}, time({self.begin}, {self.end}))"

        def commit_to_db(self):
            pass

    def __init__(
        self,
        title: str,
        start: int,
        length: int,
        draw: int = 1,
        sortDir: str = "desc",
        sortCol: int = 4,  # 时间
        category: str = "all",
        running: int = 0,
        owner: str = "",
        unix_timestamp: int = int(time.time() * 1000),
    ) -> None:
        self.draw: int = draw  # 1
        self.start: int = start
        self.length: int = length
        self.sortDir: str = sortDir  # asc or desc
        self.sortCol: int = sortCol  # sort by which column
        self.category: str = category  # all
        self.running: int = running  # 0
        self.title: str = title
        self.owner: str = owner
        self.unix_timestamp: int = unix_timestamp
        self.params = {
            "draw": self.draw,
            "start": self.start,
            "length": self.length,
            "sortDir": self.sortDir,
            "sortCol": self.sortCol,
            "category": self.category,
            "running": self.running,
            "title": self.title,
            "owner": self.owner,
            "_": self.unix_timestamp,
        }
        self.retrieved_contests: list["VjudgeContestRetriever.Contest"] = []

    def _to_contest(self, l: list) -> "VjudgeContestRetriever.Contest":
        return VjudgeContestRetriever.Contest(
            name=l[1],
            vcontest_id=int(l[0]),
            begin=datetime.datetime.utcfromtimestamp(int(l[3]) / 1000),
            end=datetime.datetime.utcfromtimestamp(int(l[4]) / 1000),
        )

    def get_contests(self):
        headers = {
            "User-Agent": fake_useragent.UserAgent().random,
        }
        if config.config["debug_cache"]:
            logger.info("debug_cache is True, use cache")
            with open("scoreanalysis/tmp/vjudge_retrive_contests.json", "r") as f:
                data: list[list] = json.load(f)["data"]
        else:
            logger.info(
                f"Getting contests from vjudge.net with title '{self.title}'......"
            )
            response = requests.get(
                f"https://vjudge.net/contest/data",
                headers=headers,
                params=self.params,
            )
            data: list[list] = response.json()["data"]

        self.retrieved_contests = list(map(self._to_contest, data))

        return self.retrieved_contests


if __name__ == "__main__":
    vjudge_contest_retriever = VjudgeContestRetriever(
        title=config.config["vjudge"][0]["title_prefix"],
        start=0,
        length=20,
    )

    vjudge_contest_retriever.get_contests()

    for contest in vjudge_contest_retriever.retrieved_contests:
        print(contest)
