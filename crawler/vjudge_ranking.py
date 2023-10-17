import asyncio
import datetime
import json
import logging

import aiofiles
import aiohttp
import fake_useragent
import requests

import config
from contestant.vjudge_contestant import VjudgeContestant
from crawler.vjudge_contest_crawler import VjudgeContestCrawler
from ranking.vjudge_ranking import VjudgeRanking

logger = logging.getLogger(__name__)


class ProblemSet:
    class Problem:
        def __init__(self) -> None:
            self.accepted: bool | None = None  # 是否已经通过
            self.penalty: datetime.timedelta = datetime.timedelta()  # 罚时

    def __init__(self) -> None:
        self.problem_dict: dict[int, ProblemSet.Problem] = {}
        pass

    def __getitem__(self, index):  # 获取第 i 题
        if index not in self.problem_dict:
            self.problem_dict[index] = ProblemSet.Problem()  # 如果没有这道题，创建一个
            return self.problem_dict[index]
        else:
            return self.problem_dict[index]


class VjudgeRankingItem:
    def __init__(
        self,
        contestant_id: int,
        contestant: VjudgeContestant,
        contest_id: int,
    ) -> None:
        self.contestant_id: int = contestant_id
        self.contestant: VjudgeContestant = contestant
        self.contest_id: int = contest_id
        self.rank: int
        self.score: float = 0
        self.solved_cnt: int = 0
        self.upsolved_cnt: int = 0
        self.total_penalty: datetime.timedelta = datetime.timedelta()
        self.first_submit_time: datetime.datetime | None = None
        self.problem_set: ProblemSet = ProblemSet()

    def __repr__(self) -> str:
        return f"contestant_id: {self.contestant_id}, contestant: {self.contestant}, contest_id: {self.contest_id}, rank: {self.rank}, score: {self.score}, solved_cnt: {self.solved_cnt}, upsolved_cnt: {self.upsolved_cnt}, penalty: {self.total_penalty}"

    def __lt__(self, other: "VjudgeRankingItem") -> bool:
        if self.solved_cnt == other.solved_cnt:
            return self.total_penalty < other.total_penalty
        else:
            return self.solved_cnt > other.solved_cnt

    def commit_to_db(self):
        config.sqlsession.add(
            VjudgeRanking(
                contestant_id=self.contestant_id,
                contestant=self.contestant,
                contest_id=self.contest_id,
                rank=self.rank,
                score=self.score,
                solved_cnt=self.solved_cnt,
                upsolved_cnt=self.upsolved_cnt,
                penalty=self.total_penalty,
            )
        )

    @staticmethod
    async def get_vjudge_ranking_items(
        contest_id: int, aiosession: aiohttp.ClientSession
    ) -> list["VjudgeRankingItem"]:
        vjudge_ranking_items_dict: dict[int, VjudgeRankingItem] = {}
        headers = {
            "User-Agent": fake_useragent.UserAgent().random,
        }
        if config.config["debug"]:
            async with aiofiles.open("tmp/vjudge_rank.json", mode="r") as f:
                vjudge_contest_crawler = VjudgeContestCrawler(
                    json.loads(await f.read())
                )
        else:
            async with aiosession.get(
                f"https://vjudge.net/contest/rank/single/{contest_id}", headers=headers
            ) as response:
                vjudge_contest_crawler = VjudgeContestCrawler(await response.json())

        for submission in vjudge_contest_crawler.submissions:
            if (
                submission.contestant_id not in vjudge_ranking_items_dict
            ):  # 如果还未创建过这个人的 VjudgeRankingItem
                crt_item = VjudgeRankingItem(
                    contestant_id=submission.contestant_id,
                    contestant=submission.contestant,
                    contest_id=contest_id,
                )
                vjudge_ranking_items_dict[submission.contestant_id] = crt_item

            crt_item: VjudgeRankingItem = vjudge_ranking_items_dict[
                submission.contestant_id
            ]

            if submission.time < vjudge_contest_crawler.length:  # 在比赛时间内提交
                if not crt_item.problem_set[
                    submission.problem_id
                ].accepted:  # 多次提交中第一次 ac
                    if submission.accepted:
                        crt_item.solved_cnt += 1
                        crt_item.total_penalty += (
                            submission.time
                            + crt_item.problem_set[submission.problem_id].penalty
                        )
                        crt_item.problem_set[submission.problem_id].accepted = True
                    else:  # 如果这个人没有通过这道题——>罚时+20min
                        crt_item.problem_set[
                            submission.problem_id
                        ].penalty += datetime.timedelta(minutes=20)
                else:  # 对于已经通过的题目，不再进行处理
                    if submission.accepted:
                        logger.debug(f"提交已经通过的题目，跳过: {submission}")

            else:  # 补题
                crt_item.upsolved_cnt += 1

        vjudge_ranking_items_list = list(vjudge_ranking_items_dict.values())
        vjudge_ranking_items_list.sort()
        for i, item in enumerate(vjudge_ranking_items_list):
            item.rank = i + 1

        return vjudge_ranking_items_list


if __name__ == "__main__":

    async def main():
        async with aiohttp.ClientSession() as aiosession:
            vjudge_ranking_items = await VjudgeRankingItem.get_vjudge_ranking_items(
                contest_id=587010, aiosession=aiosession
            )

        for item in vjudge_ranking_items:
            print(item)

        # 测试 youngwind (22物联网黄屹)
        accurate_penalty = datetime.timedelta(hours=5, minutes=44, seconds=27)
        assert vjudge_ranking_items[0].total_penalty == accurate_penalty

        # 测试 fzhan (22电信车宜峰)
        accurate_penalty = datetime.timedelta(hours=10, minutes=6, seconds=43)
        assert vjudge_ranking_items[1].total_penalty == accurate_penalty

        # 测试 sjkw (黄采薇) 「带有重复提交已经通过的题」
        accurate_penalty = datetime.timedelta(hours=5, minutes=20, seconds=37)
        assert vjudge_ranking_items[2].total_penalty == accurate_penalty

    asyncio.run(main())
