import datetime

import fake_useragent
import requests

from acmana.crawler.vjudge.contest.vj_submission import VjSubmission
from acmana.models.account.vjudge_account import VjudgeAccount
from acmana.models.contest.vjudge_contest import VjudgeContest


class VjContest:
    def __init__(self, d: dict) -> None:
        self.id: int = int(d["id"])
        self.title: str = d["title"]
        self.isReplay: bool = d["isReplay"]
        self.length = datetime.timedelta(seconds=int(d["length"]) / 1000)
        self.begin: datetime.datetime = datetime.datetime.utcfromtimestamp(
            int(d["begin"] / 1000)
        )
        self.end: datetime.datetime = self.begin + self.length
        self.participants: dict[int, VjudgeAccount | None] = {}

        for vaccount_id, val in d["participants"].items():
            vaccount_id = int(vaccount_id)
            username = val[0]
            nickname = val[1]

            self.participants[vaccount_id] = VjudgeAccount.query_from_username(
                username=username
            )
            if self.participants[vaccount_id] is None:  # TODO: commit to db
                self.participants[vaccount_id] = VjudgeAccount(
                    username=username, nickname=nickname
                )

        self.submissions = [VjSubmission.from_api_list(submission, self.participants, self) for submission in d["submissions"]]  # type: ignore
        self.submissions.sort(key=lambda x: x.time)

    def __repr__(self) -> str:
        return f"id: {self.id}, title: {self.title}, begin: {self.begin}, end: {self.end}, participants: {self.participants}, submissions: {self.submissions}"

    @classmethod
    def get_rank_from_http_api(cls, contest_id: int) -> "VjContest":
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
            vj_contest_crawler = VjContest(json.load(f))
    else:
        response = requests.get(f"https://vjudge.net/contest/rank/single/{contest_id}")
        with open(cache_path, "w") as f:
            json.dump(response.json(), f, ensure_ascii=False)
        vj_contest_crawler = VjContest(response.json())
    # print(vj_contest_crawler)
    for submission in vj_contest_crawler.submissions:
        print(submission)
    # vj_contest_crawler.commit_to_vjudge_contest_db(div="div1")
