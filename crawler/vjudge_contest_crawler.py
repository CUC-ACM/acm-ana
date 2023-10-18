import datetime

import fake_useragent
import requests
from sqlalchemy import select

import config
from config import sqlsession
from contest.vjudge_contest import VjudgeContest
from contestant.vjudge_contestant import VjudgeContestant
from ranking.vjudge_ranking import VjudgeRanking


class VjudgeContestCrawler:
    class Submission:
        def __init__(
            self,
            contestant_id: int,
            problem_id: int,
            accepted: bool,
            time: datetime.timedelta,
            contestant: VjudgeContestant,
        ) -> None:
            self.contestant_id: int = contestant_id  # 注意，这里是 vjudge 自己的 contestant_id
            self.problem_id = problem_id
            self.accepted: bool = accepted
            self.time: datetime.timedelta = time
            self.contestant: VjudgeContestant = contestant

        @classmethod
        def from_api_list(
            cls, l: list, participants_dict: dict[int, VjudgeContestant]
        ) -> "VjudgeContestCrawler.Submission":
            return cls(
                contestant_id=int(l[0]),
                problem_id=int(l[1]),
                accepted=bool(l[2]),
                time=datetime.timedelta(seconds=int(l[3])),
                contestant=participants_dict[int(l[0])],
            )

        def __repr__(self) -> str:
            return f"contestant_id: {self.contestant_id}, contestant: {self.contestant} promble_id: {self.problem_id}, accepted: {self.accepted}, time: {self.time}"

    def __init__(self, d: dict) -> None:
        self.id: int = int(d["id"])
        self.title: str = d["title"]
        self.isReplay: bool = d["isReplay"]
        self.length = datetime.timedelta(seconds=int(d["length"]) / 1000)
        self.begin: datetime.datetime = datetime.datetime.utcfromtimestamp(
            int(d["begin"] / 1000)
        )
        self.end: datetime.datetime = self.begin + self.length
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

        self.submissions = [VjudgeContestCrawler.Submission.from_api_list(submission, self.participants) for submission in d["submissions"]]  # type: ignore
        self.submissions.sort(key=lambda x: x.time)

    def __repr__(self) -> str:
        return f"id: {self.id}, title: {self.title}, begin: {self.begin}, end: {self.end}, participants: {self.participants}, submissions: {self.submissions}"

    @classmethod
    def get_rank_from_http_api(cls, contest_id: int) -> "VjudgeContestCrawler":
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

    cache_path = "tmp/vjudge_rank_587010.json"
    contest_id = 587010
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            vj_contest_crawler = VjudgeContestCrawler(json.load(f))
    else:
        response = requests.get(f"https://vjudge.net/contest/rank/single/{contest_id}")
        with open(cache_path, "w") as f:
            json.dump(response.json(), f)
        vj_contest_crawler = VjudgeContestCrawler(response.json())
    # print(vj_contest_crawler)
    for submission in vj_contest_crawler.submissions:
        print(submission)
    # vj_contest_crawler.commit_to_vjudge_contest_db(div="div1")
