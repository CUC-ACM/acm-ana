import asyncio
import datetime
import json
import logging
import os
import re

import fake_useragent
import requests

from acmana.crawler.nowcoder.contest.nowcoder_competition_ranking import (
    fetch_contest_ranking,
)
from acmana.crawler.nowcoder.contest.nowcoder_ranking_item import NowcoderRankingItem
from acmana.crawler.nowcoder.contest.nowcoder_submission import (
    NowcoderSubmission,
    fetch_contest_submisions,
)
from acmana.models.contest.nowcoder_contest import NowcoderContest
from acmana.models.ranking.nowcoder_ranking import NowcoderRanking

logger = logging.getLogger(__name__)


class NowcoderContestCrawler:
    def __init__(self, contest_id: int, div: str) -> None:
        self._contest_id = contest_id
        self.db_nowcoder_contest: NowcoderContest = NowcoderContest.query_from_id(contest_id)  # type: ignore
        if self.db_nowcoder_contest is None:
            self.db_nowcoder_contest = NowcoderContest(id=contest_id, div=div)

        self._contest_metadata: dict = self.crawl_contest_metadata_json()
        self.db_nowcoder_contest.title = self._contest_metadata["name"]
        self.db_nowcoder_contest.begin = datetime.datetime.utcfromtimestamp(
            self._contest_metadata["startTime"] / 1000,
        ).replace(tzinfo=datetime.timezone.utc)
        self.db_nowcoder_contest.end = datetime.datetime.utcfromtimestamp(
            self._contest_metadata["endTime"] / 1000
        ).replace(tzinfo=datetime.timezone.utc)
        self.nowcoder_ranking_items_dict: dict[
            int, NowcoderRankingItem
        ] = {}  # User ID -> NowcoderRankingItem

    def crawl_contest_metadata_json(self) -> dict:
        """获取比赛的基础信息"""
        cache_path = f"acmana/tmp/cache/nowcoder_contest_{self._contest_id}.html"
        if os.getenv("DEBUG_CACHE", "False").lower() in (
            "true",
            "1",
            "t",
        ) and os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                html = f.read()
        else:
            headers = {
                "authority": "ac.nowcoder.com",
                "user-agent": fake_useragent.UserAgent().random,
            }

            response = requests.get(
                f"https://ac.nowcoder.com/acm/contest/{self.db_nowcoder_contest.id}",
                headers=headers,
            )
            html = response.text
            with open(cache_path, "w") as f:
                f.write(html)

        re_contest_info = re.compile(r"window.pageInfo = ([\w\W]*);\s+window.gioInfo")

        matchObj = re_contest_info.search(html)

        if matchObj is not None:
            return json.loads(matchObj.group(1).strip())
        else:
            raise RuntimeError(f"比赛 {self.db_nowcoder_contest} 信息获取失败")

    def get_competition_ranking(self):
        """从 API 接口中获取比赛结束为止的排名信息和题目通过信息（不包含补题）
        这里不需管理员权限，因此不需要登录 cookies"""
        api_ranking_list = asyncio.run(
            fetch_contest_ranking(self.db_nowcoder_contest.id)
        )
        for api_ranking in api_ranking_list:
            self.nowcoder_ranking_items_dict[api_ranking["uid"]] = NowcoderRankingItem(
                nowcoder_account_id=api_ranking["uid"],
                nowcoder_account_nickename=api_ranking["userName"],
                nowcoder_contest_crawler=self,
            )

            # db_nowcoder_ranking_item = NowcoderRanking.index_query(
            #     contest_id=self.db_nowcoder_contest.id,
            #     account_id=api_ranking["uid"],
            # )
            # if db_nowcoder_ranking_item is None:  # 数据库中没有这个排名信息——>新建
            #     db_nowcoder_ranking_item = NowcoderRanking(
            #         account_id=api_ranking["uid"],
            #         contest_id=self.db_nowcoder_contest.id,
            #         competition_rank=api_ranking["ranking"],
            #         solved_cnt=api_ranking["acceptedCount"],
            #         upsolved_cnt=0,  # 需要后续根据所有的提交信息来计算
            #         penalty=datetime.timedelta(milliseconds=api_ranking["penaltyTime"]),
            #     )
            # else:  # 数据库中已经有这个排名信息——>更新

            self.nowcoder_ranking_items_dict[
                api_ranking["uid"]
            ].db_nowcoder_ranking.competition_rank = api_ranking["ranking"]
            self.nowcoder_ranking_items_dict[
                api_ranking["uid"]
            ].db_nowcoder_ranking.solved_cnt = api_ranking["acceptedCount"]
            self.nowcoder_ranking_items_dict[
                api_ranking["uid"]
            ].db_nowcoder_ranking.penalty = datetime.timedelta(
                milliseconds=api_ranking["penaltyTime"]
            )

            # self.db_nowcoder_contest.rankings.append(db_nowcoder_ranking_item)

            self.nowcoder_ranking_items_dict[
                api_ranking["uid"]
            ].update_problem_set_status_from_api_scoreList(api_ranking["scoreList"])

    def simulate_contest(self):
        """牛客虽然比赛期间不用模拟，但是需要模拟提交后的补题以避免重复 AC 计数"""
        self.get_competition_ranking()  # 先获取比赛期间的排名信息
        # 模拟比赛结束后的补题
        for api_submission_dict in self.get_upsolve_info():
            nowcoder_submission = NowcoderSubmission.from_api_submission_dict(
                api_submission_dict=api_submission_dict,
                contest_crawler=self,
            )
            self.nowcoder_ranking_items_dict[
                api_submission_dict["userId"]
            ].submit_after_competiton(
                nowcoder_submission
            )  # 模拟补题

    def get_upsolve_info(self) -> list[dict]:
        """获取补题提交的 api 信息并按照 `提交顺序` 排序后返回

        注意：这里需要管理员权限才能爬取所有提交，因此需要具有管理员权限的 cookies"""
        all_submissions = asyncio.run(fetch_contest_submisions(self._contest_id))

        upsovle_submissions: list[dict] = list(
            filter(
                lambda x: x["submitTime"]
                > self.db_nowcoder_contest.end.timestamp() * 1000,
                all_submissions,
            )
        )

        upsovle_submissions.sort(key=lambda x: x["submitTime"])

        logger.info(
            f"fetch {len(upsovle_submissions)} upsolved submissions from nowcoder contest {self.db_nowcoder_contest.title}"
        )
        return upsovle_submissions


if __name__ == "__main__":
    nowcoder_contest_crawler = NowcoderContestCrawler(67345, "div2")
    print(nowcoder_contest_crawler.db_nowcoder_contest)
    nowcoder_contest_crawler.get_competition_ranking()
    nowcoder_contest_crawler.db_nowcoder_contest.commit_to_db()
    nowcoder_contest_crawler.simulate_contest()
