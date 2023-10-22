import datetime
import logging
from typing import TYPE_CHECKING

from acmana.models.account.nowcoder_account import NowcoderAccount
from acmana.models.ranking.nowcoder_ranking import NowcoderRanking

if TYPE_CHECKING:
    from acmana.crawler.nowcoder.contest import NowcoderContestCrawler

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

    def __getitem__(self, index):  # 获取第 i 题
        if index not in self.problem_dict:
            self.problem_dict[index] = NowcoderProblemSet.Problem()  # 如果没有这道题，创建一个
            return self.problem_dict[index]
        else:
            return self.problem_dict[index]


class NowcoderRankingItem:
    def __init__(
        self,
        db_account: NowcoderAccount,
        nowcoder_contest_crawler: "NowcoderContestCrawler",
    ) -> None:
        self.db_account: NowcoderAccount = db_account
        self.nowcoder_contest_crawler: "NowcoderContestCrawler" = (
            nowcoder_contest_crawler
        )
        self.db_nowcoder_ranking: NowcoderRanking = NowcoderRanking.index_query(  # type: ignore
            contest_id=self.nowcoder_contest_crawler.db_nowcoder_contest.id,
            account_id=self.db_account.id,
        )
        if self.db_nowcoder_ranking is None:
            self.db_nowcoder_ranking = NowcoderRanking(
                account_id=self.db_account.id,
                contest_id=self.nowcoder_contest_crawler.db_nowcoder_contest.id,
                competition_rank=None,
                solved_cnt=None,  # 直接由 nowcoder api 接口获取
                upsolved_cnt=0,
                penalty=None,  # 直接由 nowcoder api 接口获取
            )
