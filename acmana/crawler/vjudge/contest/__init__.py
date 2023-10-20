import datetime
import json
import logging
import os

import fake_useragent
import requests

from acmana.crawler.vjudge.contest.vjudge_ranking_item import VjudgeRankingItem
from acmana.crawler.vjudge.contest.vjudge_submission import VjudgeSubmission
from acmana.models.account.vjudge_account import VjudgeAccount
from acmana.models.contest.vjudge_contest import VjudgeContest

logger = logging.getLogger(__name__)


class VjudgeContestCrawler:
    def __init__(self, contest_id: int) -> None:
        self.contest_id: int = contest_id
        self._contest_api_metadata: dict = self.crawl_ranking_metadata_json()
        self.id: int = int(self._contest_api_metadata["id"])
        self.title: str = self._contest_api_metadata["title"]
        self.isReplay: bool = self._contest_api_metadata["isReplay"]
        self.length = datetime.timedelta(
            seconds=int(self._contest_api_metadata["length"]) / 1000
        )
        self.begin: datetime.datetime = datetime.datetime.utcfromtimestamp(
            int(self._contest_api_metadata["begin"] / 1000)
        )
        self.end: datetime.datetime = self.begin + self.length
        self.participants: dict[int, VjudgeAccount] = {}

        for vaccount_id, val in self._contest_api_metadata["participants"].items():
            vaccount_id = int(vaccount_id)
            username, nickname = val[0], val[1]

            self.participants[vaccount_id] = VjudgeAccount.query_from_username(  # type: ignore
                username=username
            )
            if self.participants[vaccount_id] is None:  # 在解析的时候就直接将没有见过的用户存入数据库
                logger.warning(
                    f"vjudge account {username}, {nickname} not found, create a new one and commit to db......"
                )
                self.participants[vaccount_id] = VjudgeAccount(
                    username=username, nickname=nickname, id=vaccount_id
                )
                self.participants[vaccount_id].commit_to_db()  # type: ignore

        self.submissions = [VjudgeSubmission.from_api_list(submission, self.participants, self) for submission in self._contest_api_metadata["submissions"]]  # type: ignore
        self.submissions.sort(key=lambda x: x.time)
        (
            self.total_until_now_ranking_items,
            self.total_competion_ranking_items,
        ) = VjudgeRankingItem.get_vjudge_ranking_items(
            only_attendance=False, vjudge_contest_crawler=self
        )
        (
            self.attendance_until_now_ranking_items,
            self.attendance_competition_ranking_items,
        ) = VjudgeRankingItem.get_vjudge_ranking_items(
            only_attendance=True, vjudge_contest_crawler=self
        )

    def __repr__(self) -> str:
        return f"id: {self.id}, title: {self.title}, begin: {self.begin}, end: {self.end}, participants: {self.participants}, submissions: {self.submissions}"

    def crawl_ranking_metadata_json(self) -> dict:
        cache_path = f"acmana/tmp/vjudge_rank_{self.contest_id}.json"
        if os.getenv("DEBUG_CACHE", "False").lower() in (
            "true",
            "1",
            "t",
        ) and os.path.exists(cache_path):
            with open(cache_path) as f:
                _contest_api_metadata = json.load(f)
            return _contest_api_metadata

        headers = {
            "User-Agent": fake_useragent.UserAgent().random,
        }
        response = requests.get(
            f"https://vjudge.net/contest/rank/single/{self.contest_id}",
            headers=headers,
        )
        with open(cache_path, "w") as f:  # 保存 cache 到本地
            json.dump(response.json(), f, ensure_ascii=False)
        return response.json()

    def commit_to_vjudge_contest_db(self, div: str | None = None):
        """将当前的比赛的 `元信息` 及其所有的 VjudgeRankingItem 提交到数据库中"""

        vjudge_contest = VjudgeContest(
            id=self.id,
            title=self.title,
            begin=self.begin,
            end=self.end,
            div=div,
        )

        map(VjudgeRankingItem.commit_to_db, self.total_until_now_ranking_items)

        vjudge_contest.commit_to_db()


if __name__ == "__main__":
    import json
    import os

    contest_id = 587010

    vj_contest_crawler = VjudgeContestCrawler(contest_id)
    # print(vj_contest_crawler)
    for submission in vj_contest_crawler.submissions:
        print(submission)
    # vj_contest_crawler.commit_to_vjudge_contest_db(div="div1")
