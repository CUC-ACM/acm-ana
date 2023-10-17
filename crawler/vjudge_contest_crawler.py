import datetime

import fake_useragent
import requests
from sqlalchemy import select

import config
from config import sqlsession
from contest.vjudge_contest import VjudgeContest
from contestant.vjudge_contestant import VjudgeContestant
from ranking.vjudge_ranking import VjudgeRanking


class VjudgeRankCrawler:
    class Submission:
        def __init__(
            self, l: list, participants_dict: dict[int, VjudgeContestant]
        ) -> None:
            self.contestant_id: int = int(l[0])
            self.promble_id = int(l[1])
            self.accepted: bool = bool(l[2])
            self.time: datetime.timedelta = datetime.timedelta(seconds=int(l[3]))
            self.contestant: VjudgeContestant = participants_dict[self.contestant_id]

        def __repr__(self) -> str:
            return f"contestant_id: {self.contestant_id}, contestant: {self.contestant} promble_id: {self.promble_id}, accepted: {self.accepted}, time: {self.time}"

    def __init__(self, d: dict) -> None:
        self.id = d["id"]
        self.title = d["title"]
        self.isReplay = d["isReplay"]
        self.length = int(d["length"])
        self.begin: datetime.datetime = datetime.datetime.utcfromtimestamp(
            int(d["begin"] / 1000)
        )
        self.end: datetime.datetime = datetime.datetime.utcfromtimestamp(
            int((d["begin"] + d["length"]) / 1000)
        )
        self.participants: dict[int, VjudgeContestant | None] = {}

        for contestant_id, val in d["participants"].items():
            contestant_id = int(contestant_id)
            username = val[0]
            nickname = val[1]
            stmt = select(VjudgeContestant).where(VjudgeContestant.username == username)

            self.participants[contestant_id] = sqlsession.execute(
                stmt
            ).scalar_one_or_none()  # type: ignore
            if self.participants[contestant_id] is None:
                self.participants[contestant_id] = VjudgeContestant(
                    username=username, nickname=nickname
                )

        self.submissions = [VjudgeRankCrawler.Submission(submission, self.participants) for submission in d["submissions"]]  # type: ignore

    def __repr__(self) -> str:
        return f"id: {self.id}, title: {self.title}, begin: {self.begin}, end: {self.end}, participants: {self.participants}, submissions: {self.submissions}"

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
    # print(vj_rank_crawler)
    for submission in vj_rank_crawler.submissions:
        print(submission)
    # vj_rank_crawler.commit_to_vjudge_contest_db(div="div1")
