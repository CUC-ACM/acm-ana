import asyncio
import datetime
import json
import logging

import aiofiles
import aiohttp
import fake_useragent

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
        contest_length: datetime.timedelta,
    ) -> None:
        self.contestant_id: int = contestant_id
        self.contestant: VjudgeContestant = contestant
        self.contest_id: int = contest_id
        self.contest_length: datetime.timedelta = contest_length
        self.competition_rank: int | None = None  # 比赛排名。如果没有参加比赛而补了题，为 None
        self.score: float = 0
        self.solved_cnt: int = 0
        self.upsolved_cnt: int = 0
        self.total_penalty: datetime.timedelta = datetime.timedelta()
        self.first_submit_time: datetime.timedelta | None = None
        self.problem_set: ProblemSet = ProblemSet()

    def __repr__(self) -> str:
        return f"contestant_id: {self.contestant_id}, contestant: {self.contestant}, contest_id: {self.contest_id}, competition_rank: {self.competition_rank}, score: {self.score}, solved_cnt: {self.solved_cnt}, upsolved_cnt: {self.upsolved_cnt}, penalty: {self.total_penalty}, first_submit_time: {self.first_submit_time}"

    def __lt__(self, other: "VjudgeRankingItem") -> bool:
        if (
            self.solved_cnt == 0 and self.first_submit_time > self.contest_length  # type: ignore
        ):  # 只参加了补题
            if self.upsolved_cnt != other.upsolved_cnt:  # 如果补题数不同
                return self.upsolved_cnt > other.upsolved_cnt  # 补题数多的排名靠前
            else:
                return self.contestant_id < other.contestant_id  # 否则按照 ID 排序
        # 否则下面是参加了比赛的情况
        elif self.solved_cnt == other.solved_cnt:  # 如果通过题目数相同
            if self.total_penalty != other.total_penalty:  # 如果罚时不同
                return self.total_penalty < other.total_penalty  # 罚时少的排名靠前
            else:  # 如果罚时相同
                return self.contestant_id < other.contestant_id  # 按照 ID 排序
        else:  # 如果通过题目数不同
            return self.solved_cnt > other.solved_cnt  # 通过题目数多的排名靠前

    def commit_to_db(self):
        config.sqlsession.add(
            VjudgeRanking(
                contestant_id=self.contestant_id,
                contestant=self.contestant,
                contest_id=self.contest_id,
                competition_rank=self.competition_rank,
                score=self.score,
                solved_cnt=self.solved_cnt,
                upsolved_cnt=self.upsolved_cnt,
                penalty=self.total_penalty,
            )
        )

    def cal_score(self, contestant_num: int):
        """计算得分。注意 contestant_num 是在比赛期间参加比赛的人数！

        :param contestant_num: `在比赛期间参加比赛` 的人数"""
        # 1. 比赛期间得分
        if (
            self.first_submit_time <= self.contest_length  # type: ignore
            and self.competition_rank is not None
        ):  # 参加了比赛——>比赛期间得分
            percentage = self.competition_rank / contestant_num
            if percentage <= 0.2:
                self.score += 100
            elif percentage <= 0.4:
                self.score += 90
            elif percentage <= 0.6:
                self.score += 80
            elif percentage <= 0.8:
                self.score += 70
            else:
                self.score += 60

        # 2. 比赛后补题分
        self.score += self.upsolved_cnt * 6

        self.score = min(100, self.score)

    def submit(self, submission: VjudgeContestCrawler.Submission):
        """提交题目。注意！需要按照提交时间排序顺序提交！"""

        if self.first_submit_time is None:  # 第一次提交
            self.first_submit_time = submission.time
        if submission.time < self.contest_length:  # 在比赛时间内提交
            if not self.problem_set[submission.problem_id].accepted:  # 如果之前还没有通过这道题
                if submission.accepted:
                    self.solved_cnt += 1
                    self.total_penalty += (
                        submission.time
                        + self.problem_set[submission.problem_id].penalty
                    )
                    self.problem_set[submission.problem_id].accepted = True
                else:  # 如果没有通过这道题——>罚时+20min
                    self.problem_set[
                        submission.problem_id
                    ].penalty += datetime.timedelta(minutes=20)
            else:  # 对于已经通过的题目，不再进行处理
                if submission.accepted:
                    logger.debug(f"比赛时重复提交已经通过的题目并通过，跳过: {submission}")
        else:  # 补题
            if submission.accepted:
                if self.problem_set[submission.problem_id].accepted:  # 过题后重复提交
                    logger.debug(f"补题重复提交已经通过的题目并通过，跳过: {submission}")
                else:
                    self.upsolved_cnt += 1
                    self.problem_set[submission.problem_id].accepted = True
            else:  # 补题没有通过不计算罚时
                pass

    @staticmethod
    async def get_vjudge_ranking_items(
        contest_id: int,
        aiosession: aiohttp.ClientSession,
        only_attendance: bool = False,
    ) -> tuple[list["VjudgeRankingItem"], list["VjudgeRankingItem"]]:
        """获取编号为 contest_id 的 vjudge_ranking_items

        :param contest_id: 比赛编号
        :param aiosession: aiohttp.ClientSession
        :param only_attendance: 是否只将参加了课程的人进行排名

        :return: 返回 tuple[总榜, 比赛榜]"""
        vjudge_ranking_items_dict: dict[int, VjudgeRankingItem] = {}
        headers = {
            "User-Agent": fake_useragent.UserAgent().random,
        }
        if config.config["debug_cache"]:
            async with aiofiles.open("tmp/vjudge_rank_587010.json", mode="r") as f:
                vjudge_contest_crawler = VjudgeContestCrawler(
                    json.loads(await f.read())
                )
        else:
            async with aiosession.get(
                f"https://vjudge.net/contest/rank/single/{contest_id}",
                headers=headers,
            ) as response:
                vjudge_contest_crawler = VjudgeContestCrawler(await response.json())

        if only_attendance:  # 只对参加了课程的人进行排名
            vjudge_contest_crawler.submissions = list(
                filter(
                    lambda x: x.contestant.is_in_course,
                    vjudge_contest_crawler.submissions,
                )
            )

        for submission in vjudge_contest_crawler.submissions:
            if (
                submission.contestant_id not in vjudge_ranking_items_dict
            ):  # 如果还未创建过这个人的 VjudgeRankingItem
                crt_item = VjudgeRankingItem(
                    contestant_id=submission.contestant_id,
                    contestant=submission.contestant,
                    contest_id=contest_id,
                    contest_length=vjudge_contest_crawler.length,
                )
                vjudge_ranking_items_dict[submission.contestant_id] = crt_item

            vjudge_ranking_items_dict[submission.contestant_id].submit(
                submission=submission
            )

        vjudge_total_ranking_items_list = list(vjudge_ranking_items_dict.values())
        vjudge_competition_ranking_items_list = list(
            filter(
                lambda item: item.first_submit_time is not None
                and item.first_submit_time <= vjudge_contest_crawler.length,
                vjudge_total_ranking_items_list,
            )
        )
        vjudge_competition_ranking_items_list.sort()
        for i, item in enumerate(vjudge_competition_ranking_items_list):
            item.competition_rank = i + 1

        contestant_num: int = len(vjudge_competition_ranking_items_list)

        # 计算得分
        for vjudge_total_ranking_item in vjudge_total_ranking_items_list:
            vjudge_total_ranking_item.cal_score(contestant_num)

        return sorted(vjudge_total_ranking_items_list), sorted(
            vjudge_competition_ranking_items_list
        )


if __name__ == "__main__":

    async def main():
        async with aiohttp.ClientSession() as aiosession:
            (
                _,
                vjudge_competition_ranking_items_list,
            ) = await VjudgeRankingItem.get_vjudge_ranking_items(
                contest_id=587010, aiosession=aiosession
            )

        for item in vjudge_competition_ranking_items_list:
            print(item)

        # 测试 youngwind (22物联网黄屹)
        accurate_penalty = datetime.timedelta(hours=5, minutes=44, seconds=27)
        assert (
            vjudge_competition_ranking_items_list[0].total_penalty == accurate_penalty
        )

        # 测试 fzhan (22电信车宜峰)
        accurate_penalty = datetime.timedelta(hours=10, minutes=6, seconds=43)
        assert (
            vjudge_competition_ranking_items_list[1].total_penalty == accurate_penalty
        )

        # 测试 sjkw (黄采薇) 「带有重复提交已经通过的题」
        accurate_penalty = datetime.timedelta(hours=5, minutes=20, seconds=37)
        assert (
            vjudge_competition_ranking_items_list[2].total_penalty == accurate_penalty
        )

        # 测试补题

    asyncio.run(main())
