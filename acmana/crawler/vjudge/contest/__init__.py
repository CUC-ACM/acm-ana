import bisect
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
    def __init__(self, contest_id: int, div: str | None) -> None:
        self._contest_id = contest_id
        self._contest_api_metadata: dict = self.crawl_ranking_metadata_json()
        _id: int = int(self._contest_api_metadata["id"])
        assert _id == contest_id
        _title: str = self._contest_api_metadata["title"]
        _isReplay: bool = self._contest_api_metadata["isReplay"]
        _length = datetime.timedelta(
            seconds=int(self._contest_api_metadata["length"]) / 1000
        )
        _begin: datetime.datetime = datetime.datetime.utcfromtimestamp(
            int(self._contest_api_metadata["begin"] / 1000)
        )
        _end: datetime.datetime = _begin + _length
        self.db_vjudge_contest: VjudgeContest = VjudgeContest.query_from_id(contest_id)  # type: ignore
        if self.db_vjudge_contest is None:
            self.db_vjudge_contest = VjudgeContest(
                id=contest_id, title=_title, begin=_begin, end=_end, div=div
            )

        self.participants_vjudge_account: dict[int, VjudgeAccount] = {}

        for vaccount_id, val in self._contest_api_metadata["participants"].items():
            vaccount_id = int(vaccount_id)
            username, nickname = val[0], val[1]

            self.participants_vjudge_account[vaccount_id] = VjudgeAccount.query_from_username(  # type: ignore
                username=username
            )
            if (
                self.participants_vjudge_account[vaccount_id] is None
            ):  # 在解析的时候就直接将没有见过的用户存入数据库
                logger.warning(
                    f"vjudge account {username}, {nickname} not found, create a new one and commit to db......"
                )
                self.participants_vjudge_account[vaccount_id] = VjudgeAccount(
                    username=username, nickname=nickname, id=vaccount_id
                )
                self.participants_vjudge_account[vaccount_id].commit_to_db()  # type: ignore

        self.submissions = [VjudgeSubmission.from_api_list(submission, self.participants_vjudge_account, self) for submission in self._contest_api_metadata["submissions"]]  # type: ignore

        self.submissions.sort(key=lambda x: x.time)  # 按照时间顺序模拟提交
        self.simulate_contest()

    def simulate_contest(self):
        """模拟整场比赛"""
        self.submissions.sort(key=lambda x: x.time)  # 按照时间顺序模拟提交
        vjudge_ranking_items_dict: dict[int, VjudgeRankingItem] = {}

        truncation = bisect.bisect_right(  # 找到第一个比赛结束的提交分割点
            self.submissions, self.db_vjudge_contest.length, key=lambda x: x.time
        )

        # 比赛中的提交
        for submission in self.submissions[:truncation]:  # 按照时间顺序模拟提交
            if (
                submission.account.id not in vjudge_ranking_items_dict
            ):  # 如果还未创建过这个人的 VjudgeRankingItem
                vjudge_ranking_items_dict[submission.account.id] = VjudgeRankingItem(
                    account=submission.account,
                    vjudge_contest_crawler=self,
                )

            vjudge_ranking_items_dict[submission.account.id].submit(
                submission=submission
            )

        # 计算排名
        for i, ranking_item in enumerate(
            sorted(list(vjudge_ranking_items_dict.values())), start=1
        ):
            ranking_item.db_vjudge_ranking.competition_rank = i

        # 比赛结束后的提交
        for submission in self.submissions[truncation:]:
            if submission.account.id not in vjudge_ranking_items_dict:
                vjudge_ranking_items_dict[submission.account.id] = VjudgeRankingItem(
                    account=submission.account,
                    vjudge_contest_crawler=self,
                )

            vjudge_ranking_items_dict[submission.account.id].submit(
                submission=submission
            )
            # print(vjudge_ranking_items_dict[submission.account.id].db_vjudge_ranking.penalty)

        # vjudge_competition_ranking_items_list = list(
        #     filter(
        #         lambda item: item.first_submit_time is not None
        #         and item.first_submit_time <= self.db_vjudge_contest.length,
        #         list(vjudge_ranking_items_dict.values()),
        #     )
        # )
        # vjudge_competition_ranking_items_list.sort()
        # for ranking_num, item in enumerate(vjudge_competition_ranking_items_list, 1):
        #     item.db_vjudge_ranking.competition_rank = ranking_num

        # 将`所有的` db_vjudge_ranking 添加到 db_vjudge_contest
        for item in vjudge_ranking_items_dict.values():
            self.db_vjudge_contest.rankings.append(item.db_vjudge_ranking)

    def __repr__(self) -> str:
        return f"VjudgeContestCrawler(vjudge_contest={self.db_vjudge_contest}, submissions={self.submissions}, participants={self.participants_vjudge_account})"

    def crawl_ranking_metadata_json(self) -> dict:
        cache_path = f"acmana/tmp/vjudge_rank_{self._contest_id}.json"
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
            f"https://vjudge.net/contest/rank/single/{self._contest_id}",
            headers=headers,
        )
        with open(cache_path, "w") as f:  # 保存 cache 到本地
            json.dump(response.json(), f, ensure_ascii=False)
        return response.json()


if __name__ == "__main__":
    import json
    import os

    contest_id = 587010

    vj_contest_crawler = VjudgeContestCrawler(contest_id, "div1")
    # print(vj_contest_crawler)
    for submission in vj_contest_crawler.submissions:
        print(submission)
