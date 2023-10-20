import datetime
import json
import logging
import os
import time

import fake_useragent
import requests

import acmana
from acmana.models.contest.vjudge_contest import VjudgeContest

logger = logging.getLogger(__name__)


class VjudgeContestRetriever:
    class Contest:
        def __init__(
            self,
            vcontest_id: int,
            title: str,
            div: str,
            begin: datetime.datetime,
            end: datetime.datetime,
        ) -> None:
            self.vcontest_id: int = vcontest_id
            self.title: str = title
            self.div: str = div
            self.begin: datetime.datetime = begin
            self.end: datetime.datetime = end

        def __repr__(self) -> str:
            return f"(vcontest_id: {self.vcontest_id}, name: {self.title}, time({self.begin}, {self.end}))"

        def commit_to_db(self):
            logger.info(f"Committing contest {self} to database......")
            vjudge_contest: VjudgeContest | None = VjudgeContest.query_from_id(
                id=self.vcontest_id
            )  # type: ignore

            if vjudge_contest is None:  # 数据库中不存在
                logger.info(f"Contest {self} not found in database, creating......")
                VjudgeContest(
                    id=self.vcontest_id,
                    title=self.title,
                    div=self.div,
                    begin=self.begin,
                    end=self.end,
                ).commit_to_db()
            else:  # 更新此比赛
                logger.info(f"Contest {self} found in database, updating......")
                vjudge_contest.title = self.title
                vjudge_contest.div = self.div
                vjudge_contest.begin = self.begin
                vjudge_contest.end = self.end
                vjudge_contest.commit_to_db()

    def __init__(
        self,
        title: str,
        div: str,  # div: "", "div1", "div2"
        start: int = 0,
        length: int = 20,
        draw: int = 1,
        sortDir: str = "desc",
        sortCol: int = 4,  # 时间
        category: str = "all",
        running: int = 0,
        owner: str = "",
        unix_timestamp: int = int(time.time() * 1000),
    ) -> None:
        self.div: str = div
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
            title=l[1],
            vcontest_id=int(l[0]),
            div=self.div,
            begin=datetime.datetime.utcfromtimestamp(int(l[3]) / 1000),
            end=datetime.datetime.utcfromtimestamp(int(l[4]) / 1000),
        )

    def get_contests(self):
        headers = {
            "User-Agent": fake_useragent.UserAgent().random,
        }
        if os.getenv("DEBUG_CACHE", "True").lower() in ("true", "1", "t"):
            cache_path = "acmana/tmp/vjudge_retrive_contests.json"
            logger.info(f"DEBUG_CACHE is True, use cache {cache_path}")
            with open(cache_path, "r") as f:
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
        title=acmana.config["vjudge"]["instances"][0]["title_prefix"],
        div=acmana.config["vjudge"]["instances"][0]["div"],
    )

    vjudge_contest_retriever.get_contests()

    for contest in vjudge_contest_retriever.retrieved_contests:
        logger.info(contest)
        contest.commit_to_db()
