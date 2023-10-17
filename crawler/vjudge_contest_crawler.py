import datetime

import fake_useragent
import requests
from sqlalchemy.orm import Session

import config
from contest.vjudge_contest import VjudgeContest
from contestant.vjudge_contestant import VjudgeContestant
from ranking.vjudge_ranking import VjudgeRanking


class VjudgeRankCrawler:
    def __init__(self, d: dict) -> None:
        self.begin: datetime.datetime = datetime.datetime.utcfromtimestamp(
            int(d["begin"] / 1000)
        )
        self.id = d["id"]
        self.isReplay = d["isReplay"]
        self.length = int(d["length"])
        self.end: datetime.datetime = datetime.datetime.utcfromtimestamp(
            int((d["begin"] + d["length"]) / 1000)
        )
        self.participants = d["participants"]
        self.submissions = d["submissions"]
        self.title = d["title"]

    @classmethod
    def get_rank_from_http_api(cls, contest_id: int) -> "VjudgeRankCrawler":
        headers = {
            "User-Agent": fake_useragent.UserAgent().random,
        }
        response = requests.get(
            f"https://vjudge.net/contest/rank/single/{contest_id}",
            headers=headers,
        )
        return cls(response.json())

    def commit_to_vjudge_contest_db(self, div: str | None = None):
        """将当前的比赛信息提交到数据库 vjudge_contest 中"""
        with Session(config.engine, autoflush=False) as sqlsession:
            vjudge_contest = VjudgeContest(
                id=self.id,
                title=self.title,
                start_time=self.begin,
                end_time=self.end,
                url=f"https://vjudge.net/contest/{self.id}",
                div=div,
            )
            sqlsession.add(vjudge_contest)
            sqlsession.commit()


if __name__ == "__main__":
    import json
    import os

    cache_path = "tmp/vjudge_rank.json"
    contest_id = 587010
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            vj_rank_crawler = VjudgeRankCrawler(json.load(f))
    else:
        response = requests.get(f"https://vjudge.net/contest/rank/single/{contest_id}")
        with open(cache_path, "w") as f:
            json.dump(response.json(), f)
        vj_rank_crawler = VjudgeRankCrawler(response.json())

    vj_rank_crawler.commit_to_vjudge_contest_db(div="div1")
