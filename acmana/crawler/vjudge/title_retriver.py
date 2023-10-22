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
    def __init__(
        self,
        title_prefix: str,
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
        self.title_prefix: str = title_prefix
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
            "title": self.title_prefix,
            "owner": self.owner,
            "_": self.unix_timestamp,
        }
        self.retrieved_contests: list["VjudgeContest"] = []

    def _to_db_contest(self, l: list) -> "VjudgeContest":
        vjudge_contest: VjudgeContest = VjudgeContest.query_from_id(int(l[0]))  # type: ignore
        if vjudge_contest is None:  # 如果数据库中没有这个比赛——>新建
            vjudge_contest = VjudgeContest(
                title=l[1],
                id=int(l[0]),
                div=self.div,
                begin=datetime.datetime.utcfromtimestamp(int(l[3]) / 1000),
                end=datetime.datetime.utcfromtimestamp(int(l[4]) / 1000),
            )
        else:  # 如果数据库中有这个比赛——>更新
            vjudge_contest.title = l[1]
            vjudge_contest.div = self.div
            vjudge_contest.begin = datetime.datetime.utcfromtimestamp(int(l[3]) / 1000)
            vjudge_contest.end = datetime.datetime.utcfromtimestamp(int(l[4]) / 1000)

        return vjudge_contest

    def get_contests_and_commit_to_db(self):
        headers = {
            "User-Agent": fake_useragent.UserAgent().random,
        }
        cache_path = (
            f"acmana/tmp/cache/vjudge_retrive_contests_{self.title_prefix}.json"
        )
        if os.getenv("DEBUG_CACHE", "False").lower() in (
            "true",
            "1",
            "t",
        ) and os.path.exists(cache_path):
            logger.info(f"DEBUG_CACHE is True, use cache {cache_path}")
            with open(cache_path, "r") as f:
                data: list[list] = json.load(f)["data"]
        else:
            logger.info(
                f"Getting contests from vjudge.net with title '{self.title_prefix}'......"
            )
            response = requests.get(
                f"https://vjudge.net/contest/data",
                headers=headers,
                params=self.params,
            )
            with open(cache_path, "w") as f:
                json.dump(response.json(), f, ensure_ascii=False)
            data: list[list] = response.json()["data"]

        self.retrieved_contests = list(map(self._to_db_contest, data))

        for contest in self.retrieved_contests:
            contest.commit_to_db()

        return self.retrieved_contests


if __name__ == "__main__":
    vjudge_contest_retriever = VjudgeContestRetriever(
        title_prefix=acmana.config["vjudge"]["instances"][0]["title_prefix"],
        div=acmana.config["vjudge"]["instances"][0]["div"],
    )
    vjudge_contest_retriever.get_contests_and_commit_to_db()
