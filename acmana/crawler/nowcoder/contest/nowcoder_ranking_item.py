import datetime
import logging
from typing import TYPE_CHECKING, Any

import acmana
from acmana.models.account.nowcoder_account import NowcoderAccount
from acmana.models.ranking.nowcoder_ranking import NowcoderRanking

if TYPE_CHECKING:
    from acmana.crawler.nowcoder.contest import NowcoderContestCrawler
    from acmana.crawler.nowcoder.contest.nowcoder_submission import NowcoderSubmission
logger = logging.getLogger(__name__)


class NowcoderProblemSet:
    """这里仅仅在牛客补题时的题目状态时使用。并不将其用于模拟整场比赛"""

    class Problem:
        def __init__(self) -> None:
            self.accepted: bool | None = None  # 是否已经通过
            # self.penalty: datetime.timedelta = datetime.timedelta()  # 补题时不需要计算罚时

    def __init__(self) -> None:
        self.problem_dict: dict[int, NowcoderProblemSet.Problem] = {}
        pass

    def __getitem__(self, problem_id: int):
        """获取题目状态，如果没有这道题，创建一个

        :param problem_id: 牛客 api 的唯一题目 ID"""
        if problem_id not in self.problem_dict:
            self.problem_dict[problem_id] = NowcoderProblemSet.Problem()  # 如果没有这道题，创建一个
            return self.problem_dict[problem_id]
        else:
            return self.problem_dict[problem_id]


class NowcoderRankingItem:
    def __init__(
        self,
        nowcoder_account_id: int,
        nowcoder_account_nickename: str,
        nowcoder_contest_crawler: "NowcoderContestCrawler",
    ) -> None:
        """新建一个 NowcoderRankingItem，将之前数据库中的 NowcoderRankingItem 初始化"""
        self.db_account: NowcoderAccount = NowcoderAccount.query_from_account_id(  # type: ignore
            nowcoder_account_id
        )
        self.nowcoder_contest_crawler: "NowcoderContestCrawler" = (
            nowcoder_contest_crawler
        )
        if self.db_account is None:  # 数据库中还没有这个账号——>新建
            logger.warning(
                f"nowcoder account ({nowcoder_account_id}: {nowcoder_account_nickename}) not found, create a new one and commit to db......"
            )
            self.db_account = NowcoderAccount(
                id=nowcoder_account_id,
                nickname=nowcoder_account_nickename,
            )
            self.db_account.commit_to_db()

        self.db_nowcoder_ranking: NowcoderRanking = NowcoderRanking.index_query(  # type: ignore
            contest_id=self.nowcoder_contest_crawler.db_nowcoder_contest.id,
            account_id=self.db_account.id,
        )
        if self.db_nowcoder_ranking is None:
            self.db_nowcoder_ranking = NowcoderRanking(
                account_id=self.db_account.id,
                contest_id=self.nowcoder_contest_crawler.db_nowcoder_contest.id,
                competition_rank=None,
                solved_cnt=0,
                upsolved_cnt=0,
                penalty=0,
            )

        # 清空之前的数据库
        self.db_nowcoder_ranking.competition_rank = None
        self.db_nowcoder_ranking.solved_cnt = 0
        self.db_nowcoder_ranking.upsolved_cnt = 0
        self.db_nowcoder_ranking.penalty = datetime.timedelta()

        self.nowcoder_contest_crawler.db_nowcoder_contest.rankings.append(  # commit to database with `db_nowcoder_contest`
            self.db_nowcoder_ranking
        )

        self.problem_set: NowcoderProblemSet = NowcoderProblemSet()

    def __repr__(self) -> str:
        return f"NowcoderRankingItem(db_account={self.db_account}, db_nowcoder_ranking={self.db_nowcoder_ranking})"

    def update_problem_set_status_from_api_scoreList(
        self, api_problem_score_list: list[dict]
    ) -> None:
        for problem in api_problem_score_list:
            self.problem_set[problem["problemId"]].accepted = problem["accepted"]

    def submit_after_competiton(self, submission: "NowcoderSubmission") -> None:
        """在比赛结束后提交补题。

        由于没有模拟正常比赛，只是计算补题的数据
        所以注意需要在这一步之前将在牛客终榜中的数据 db_nowcoder_ranking 导入数据库中"""
        if (
            submission.time_from_begin
            < self.nowcoder_contest_crawler.db_nowcoder_contest.length
        ):  # 在比赛时间内提交
            logger.warning(
                f"不能通过 submit_after_competiton 提交比赛期间的 submission！{submission}"
            )
            return
            raise ValueError(f"已经爬取过比赛期间的排名数据了，不能重复计算！ {submission}")
            if not self.problem_set[submission.problem_id].accepted:  # 如果之前还没有通过这道题
                if submission.accepted:  # 如果通过这道题——>通过题目数+1，总罚时 += 此题的罚时
                    self.db_nowcoder_ranking.solved_cnt += 1
                    self.db_nowcoder_ranking.penalty += (
                        submission.time_from_begin
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
            submission.time_from_begin
            <= self.nowcoder_contest_crawler.db_nowcoder_contest.length
            + datetime.timedelta(days=acmana.config["common"]["upsolve"]["expiration"])
        ):  # 7 天内补题
            if submission.accepted:
                if self.problem_set[submission.problem_id].accepted:  # 过题后重复提交
                    logger.debug(f"补题重复提交已经通过的题目并通过，跳过: {submission}")
                else:
                    self.db_nowcoder_ranking.upsolved_cnt += 1
                    self.problem_set[submission.problem_id].accepted = True
            else:  # 补题没有通过不计算罚时
                pass
        else:
            logger.debug(
                f"补题超过 {acmana.config['common']['upsolve']['expiration']} 天，跳过: {submission}"
            )
