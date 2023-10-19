import datetime

import fake_useragent
import requests

from acmana.models.contest.vjudge_contest import VjudgeContest
from acmana.models.contestant.vjudge_contestant import VjudgeContestant


class VjudgeContestCrawler:
    class Submission:
        def __init__(
            self,
            vcontestant_id: int,
            problem_id: int,
            accepted: bool,
            time: datetime.timedelta,
            contestant: VjudgeContestant,
            contest: "VjudgeContestCrawler",
        ) -> None:
            self.vcontestant_id: int = (
                vcontestant_id  # 注意，这里是 vjudge 自己的 vcontestant_id
            )
            self.problem_id = problem_id
            self.accepted: bool = accepted
            self.time: datetime.timedelta = time
            self.contestant: VjudgeContestant = contestant
            self.contest: VjudgeContestCrawler = contest

        @classmethod
        def from_api_list(
            cls,
            l: list,
            participants_dict: dict[int, VjudgeContestant],
            contest: "VjudgeContestCrawler",
        ) -> "VjudgeContestCrawler.Submission":
            return cls(
                vcontestant_id=int(l[0]),
                problem_id=int(l[1]),
                accepted=bool(l[2]),
                time=datetime.timedelta(seconds=int(l[3])),
                contestant=participants_dict[int(l[0])],
                contest=contest,
            )

        def __repr__(self) -> str:
            return f"vcontestant_id: {self.vcontestant_id}, contestant: {self.contestant} promble_id: {self.problem_id}, accepted: {self.accepted}, time: {self.time}"

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

        for vcontestant_id, val in d["participants"].items():
            vcontestant_id = int(vcontestant_id)
            username = val[0]
            nickname = val[1]

            self.participants[vcontestant_id] = VjudgeContestant.query_from_username(
                username=username
            )
            if self.participants[vcontestant_id] is None:
                self.participants[vcontestant_id] = VjudgeContestant(
                    username=username, nickname=nickname
                )

        self.submissions = [VjudgeContestCrawler.Submission.from_api_list(submission, self.participants, self) for submission in d["submissions"]]  # type: ignore
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
            begin=self.begin,
            end=self.end,
            url=f"https://vjudge.net/contest/{self.id}",
            div=div,
        )
        vjudge_contest.commit_to_db()


if __name__ == "__main__":
    import json
    import os

    cache_path = "acmana/tmp/vjudge_rank_587010.json"
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
