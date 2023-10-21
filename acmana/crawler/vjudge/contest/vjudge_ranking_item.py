import datetime
import logging
from typing import TYPE_CHECKING

import acmana
from acmana.crawler.vjudge.contest.vjudge_submission import VjudgeSubmission
from acmana.models.account.vjudge_account import VjudgeAccount
from acmana.models.ranking.vjudge_ranking import VjudgeRanking

if TYPE_CHECKING:
    from acmana.crawler.vjudge.contest import VjudgeContestCrawler

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
        account: VjudgeAccount,
        vjudge_contest_crawler: "VjudgeContestCrawler",
    ) -> None:
        self.db_account: VjudgeAccount = account
        self.vjudge_contest_crawler: "VjudgeContestCrawler" = vjudge_contest_crawler
        self.db_vjudge_ranking: VjudgeRanking = VjudgeRanking.index_query(  # type: ignore
            contest_id=self.vjudge_contest_crawler.db_vjudge_contest.id,
            account_id=self.db_account.id,
        )

        if self.db_vjudge_ranking is None:  # 如果还没有创建过 “这个人这场比赛” 对应的 VjudgeRanking
            self.db_vjudge_ranking = VjudgeRanking(
                account_id=self.db_account.id,
                contest_id=self.vjudge_contest_crawler.db_vjudge_contest.id,
                competition_rank=None,
                solved_cnt=0,
                upsolved_cnt=0,
                penalty=datetime.timedelta(),
            )
        else:  # 如果已经创建过了——>清空数据
            self.db_vjudge_ranking.competition_rank = None
            self.db_vjudge_ranking.solved_cnt = 0
            self.db_vjudge_ranking.upsolved_cnt = 0
            self.db_vjudge_ranking.penalty = datetime.timedelta()

        # self.db_vjudge_ranking.competition_rank: int | None = None  # 比赛排名。如果没有参加比赛而补了题，为 None
        # # self.score: float = 0
        # self.db_vjudge_ranking.solved_cnt: int = 0
        # self.db_vjudge_ranking.upsolved_cnt: int = 0
        # self.db_vjudge_ranking.penalty: datetime.timedelta = datetime.timedelta()
        self.first_submit_time: datetime.timedelta
        self.problem_set: ProblemSet = ProblemSet()

    # @property
    # def total_solved_cnt(self) -> int:
    #     """总过题数"""
    #     return self.db_vjudge_ranking.solved_cnt + self.db_vjudge_ranking.upsolved_cnt

    def __repr__(self) -> str:
        return f"account: {self.db_account}, contest_id: {self.vjudge_contest_crawler.db_vjudge_contest.id}, db_vjudge_ranking: {self.db_vjudge_ranking}, first_submit_time: {self.first_submit_time}"

    def __lt__(self, other: "VjudgeRankingItem") -> bool:
        if (
            self.first_submit_time > self.vjudge_contest_crawler.db_vjudge_contest.length  # type: ignore
        ):  # 只参加了补题
            raise ValueError("只参加了补题，不应该参与比赛期间排名")
        # 否则下面是参加了比赛的情况
        elif (
            self.db_vjudge_ranking.solved_cnt == other.db_vjudge_ranking.solved_cnt
        ):  # 如果通过题目数相同
            if (
                self.db_vjudge_ranking.penalty != other.db_vjudge_ranking.penalty
            ):  # 如果罚时不同
                return (
                    self.db_vjudge_ranking.penalty < other.db_vjudge_ranking.penalty
                )  # 罚时少的排名靠前
            else:  # 如果罚时相同
                return self.db_account.id < other.db_account.id  # 按照 ID 排序
        else:  # 如果通过题目数不同
            return (
                self.db_vjudge_ranking.solved_cnt > other.db_vjudge_ranking.solved_cnt
            )  # 通过题目数多的排名靠前

    # def commit_to_db(self):
    #     assert self.db_account.id is not None
    #     db_vjudge_ranking: VjudgeRanking | None = VjudgeRanking.index_query(
    #         contest_id=self.vjudge_contest_crawler.db_vjudge_contest.id,
    #         account_id=self.db_account.id,
    #     )

    #     if db_vjudge_ranking:
    #         db_vjudge_ranking.competition_rank = self.db_vjudge_ranking.competition_rank
    #         db_vjudge_ranking.solved_cnt = self.db_vjudge_ranking.solved_cnt
    #         db_vjudge_ranking.upsolved_cnt = self.db_vjudge_ranking.upsolved_cnt
    #         db_vjudge_ranking.penalty = self.db_vjudge_ranking.penalty
    #     else:  # 如果还没有创建过 “这个人这场比赛” 对应的 VjudgeRanking
    #         db_vjudge_ranking = VjudgeRanking(
    #             account_id=self.db_account.id,
    #             contest_id=self.vjudge_contest_crawler.db_vjudge_contest.id,
    #             competition_rank=self.db_vjudge_ranking.competition_rank,
    #             solved_cnt=self.db_vjudge_ranking.solved_cnt,
    #             upsolved_cnt=self.db_vjudge_ranking.upsolved_cnt,
    #             penalty=int(self.db_vjudge_ranking.penalty.total_seconds()),
    #         )
    #     db_vjudge_ranking.commit_to_db()

    def submit(self, submission: VjudgeSubmission):
        """提交题目。注意！需要按照提交时间排序顺序提交！"""

        if getattr(self, "first_submit_time", None) is None:  # 第一次提交
            self.first_submit_time = submission.time

        if (
            submission.time < self.vjudge_contest_crawler.db_vjudge_contest.length
        ):  # 在比赛时间内提交
            if not self.problem_set[submission.problem_id].accepted:  # 如果之前还没有通过这道题
                if submission.accepted:  # 如果通过这道题——>通过题目数+1，总罚时 += 此题的罚时
                    self.db_vjudge_ranking.solved_cnt += 1
                    self.db_vjudge_ranking.penalty += (
                        submission.time
                        + self.problem_set[submission.problem_id].penalty
                    )
                    self.problem_set[submission.problem_id].accepted = True
                else:  # 如果没有通过这道题——>此题的罚时+20min（只有过题后才会纳入罚时计算）
                    self.problem_set[
                        submission.problem_id
                    ].penalty += datetime.timedelta(minutes=20)
            else:  # 对于已经通过的题目，不再进行处理
                if submission.accepted:
                    logger.debug(f"比赛时重复提交已经通过的题目并通过，跳过: {submission}")
                else:
                    logger.debug(f"比赛时重复提交已经通过的题目但没有通过，跳过: {submission}")
        elif (
            submission.time
            <= self.vjudge_contest_crawler.db_vjudge_contest.length
            + datetime.timedelta(days=acmana.config["upsolve"]["expiration"])
        ):  # 7 天内补题
            if submission.accepted:
                if self.problem_set[submission.problem_id].accepted:  # 过题后重复提交
                    logger.debug(f"补题重复提交已经通过的题目并通过，跳过: {submission}")
                else:
                    self.db_vjudge_ranking.upsolved_cnt += 1
                    self.problem_set[submission.problem_id].accepted = True
            else:  # 补题没有通过不计算罚时
                pass
        else:
            logger.debug(
                f"补题超过 {acmana.config['upsolve']['expiration']} 天，跳过: {submission}"
            )

    # @staticmethod
    # def simulate_contest(
    #     vjudge_contest_crawler: "VjudgeContestCrawler",
    # ):
    #     """模拟整场比赛"""
    #     vjudge_ranking_items_dict: dict[int, VjudgeRankingItem] = {}

    #     for submission in vjudge_contest_crawler.submissions:
    #         if (
    #             submission.account.id not in vjudge_ranking_items_dict
    #         ):  # 如果还未创建过这个人的 VjudgeRankingItem
    #             crt_item = VjudgeRankingItem(
    #                 account=submission.account,
    #                 vjudge_contest_crawler=vjudge_contest_crawler,
    #             )
    #             vjudge_ranking_items_dict[submission.account.id] = crt_item

    #         vjudge_ranking_items_dict[submission.account.id].submit(
    #             submission=submission
    #         )

    #     vjudge_competition_ranking_items_list = list(
    #         filter(
    #             lambda item: item.first_submit_time is not None
    #             and item.first_submit_time
    #             <= vjudge_contest_crawler.db_vjudge_contest.length,
    #             list(vjudge_ranking_items_dict.values()),
    #         )
    #     )
    #     vjudge_competition_ranking_items_list.sort()
    #     for ranking_num, item in enumerate(vjudge_competition_ranking_items_list, 1):
    #         item.db_vjudge_ranking.competition_rank = ranking_num

    #     # append to db_vjudge_contest
    #     for item in vjudge_competition_ranking_items_list:
    #         vjudge_contest_crawler.db_vjudge_contest.rankings.append(
    #             item.db_vjudge_ranking
    #         )


if __name__ == "__main__":
    """下面的代码尽量不要运行——>会对数据库进行操作，使用 unittest 进行测试"""
    # from acmana.crawler.vjudge.contest import VjudgeContestCrawler
    # from acmana.models import engine

    # logger.warning(f"Droping table {VjudgeRanking.__tablename__}")
    # VjudgeRanking.metadata.drop_all(engine)
    # logger.info(f"Creating table {VjudgeRanking.__tablename__}")
    # VjudgeRanking.metadata.create_all(engine)

    # vjudge_contest_crawler = VjudgeContestCrawler(contest_id=587010, div="div1")

    # def main():
    #     VjudgeRankingItem.simulate_contest(
    #         vjudge_contest_crawler=vjudge_contest_crawler,
    #     )

    #     for item in vjudge_total_ranking_items_list:
    #         print(item)
    #         item.commit_to_db()

    #     # 测试 youngwind (22物联网黄屹)
    #     accurate_penalty = datetime.timedelta(hours=5, minutes=44, seconds=27)
    #     assert (
    #         vjudge_competition_ranking_items_list[0].total_penalty == accurate_penalty
    #     )

    #     # 测试 fzhan (22电信车宜峰)
    #     accurate_penalty = datetime.timedelta(hours=10, minutes=6, seconds=43)
    #     assert (
    #         vjudge_competition_ranking_items_list[1].total_penalty == accurate_penalty
    #     )

    #     # 测试 sjkw (黄采薇) 「带有重复提交已经通过的题」
    #     accurate_penalty = datetime.timedelta(hours=5, minutes=20, seconds=37)
    #     assert (
    #         vjudge_competition_ranking_items_list[2].total_penalty == accurate_penalty
    #     )

    #     # 测试补题

    # main()
    pass
