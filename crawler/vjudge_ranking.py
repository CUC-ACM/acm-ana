import asyncio
import datetime
import json

import aiofiles
import aiohttp
import fake_useragent
import requests

import config
from contestant.vjudge_contestant import VjudgeContestant
from crawler.vjudge_contest_crawler import VjudgeContestCrawler
from ranking.vjudge_ranking import VjudgeRanking


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
        self.penalty: datetime.timedelta = datetime.timedelta()

    def __repr__(self) -> str:
        return f"contestant_id: {self.contestant_id}, contestant: {self.contestant}, contest_id: {self.contest_id}, rank: {self.rank}, score: {self.score}, solved_cnt: {self.solved_cnt}, upsolved_cnt: {self.upsolved_cnt}, penalty: {self.penalty}"

    def __lt__(self, other: "VjudgeRankingItem") -> bool:
        if self.solved_cnt == other.solved_cnt:
            return self.penalty < other.penalty
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
                penalty=self.penalty,
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

        penalty_dict: dict[
            int, dict[int, datetime.timedelta]
        ] = {}  # id. problem_id -> penalty

        for submission in vjudge_contest_crawler.submissions:
            if submission.contestant_id not in penalty_dict.keys():
                penalty_dict[submission.contestant_id] = {}
            if (
                submission.promble_id
                not in penalty_dict[submission.contestant_id].keys()
            ):
                penalty_dict[submission.contestant_id][
                    submission.promble_id
                ] = datetime.timedelta()

            if (
                submission.contestant_id not in vjudge_ranking_items_dict.keys()
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
                if submission.accepted:
                    crt_item.solved_cnt += 1
                    crt_item.penalty += (
                        submission.time
                        + penalty_dict[submission.contestant_id][submission.promble_id]
                    )
                else:  # 如果这个人没有通过这道题——>罚时+20min
                    penalty_dict[submission.contestant_id][
                        submission.promble_id
                    ] += datetime.timedelta(minutes=20)
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

    asyncio.run(main())
