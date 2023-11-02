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
        else:  # 如果已经创建过了——>清空数据以在之后重新计算
            self.db_vjudge_ranking.competition_rank = None
            self.db_vjudge_ranking.solved_cnt = 0
            self.db_vjudge_ranking.upsolved_cnt = 0
            self.db_vjudge_ranking.penalty = datetime.timedelta()

        self.first_submit_time: datetime.timedelta
        self.problem_set: ProblemSet = ProblemSet()

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
            + datetime.timedelta(days=acmana.config["common"]["upsolve"]["expiration"])
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
            logger.warning(
                f"Vjudge Submission: {submission} 补题时间超过 {acmana.config['common']['upsolve']['expiration']} 天，跳过: {submission}"
            )


if __name__ == "__main__":
    pass
