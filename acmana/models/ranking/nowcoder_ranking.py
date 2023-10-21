from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Index, Select, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acmana.models import SQLBase, sqlsession
from acmana.models.ranking import RankingBase

if TYPE_CHECKING:
    from acmana.models.account.nowcoder_account import NowcoderAccount
    from acmana.models.contest.nowcoder_contest import NowcoderContest


class NowcoderRanking(RankingBase, SQLBase):
    """存储牛客 所有比赛排名 的表(各场比赛混在一起)"""

    __tablename__ = "nowcoder_ranking"
    account_id: Mapped[int] = mapped_column(ForeignKey("nowcoder_account.id"))
    account: Mapped["NowcoderAccount"] = relationship(back_populates="rankings")
    contest_id: Mapped[int] = mapped_column(ForeignKey("nowcoder_contest.id"))
    contest: Mapped["NowcoderContest"] = relationship(back_populates="rankings")

    @staticmethod
    def index_query(
        contest_id: int,
        account_id: int,
    ) -> Optional["NowcoderRanking"]:
        stmt: Select = (
            select(NowcoderRanking)
            .with_hint(NowcoderRanking, "unique_nowcoder_account_contest")
            .where(NowcoderRanking.contest_id == contest_id)
            .where(NowcoderRanking.account_id == account_id)
        )
        return sqlsession.execute(stmt).scalar_one_or_none()


# 为了防止重复提交，这里设置了唯一索引，确保同一个账号只能在同一个比赛中出现在 nowcoder_ranking 中一次
Index(
    "unique_nowcoder_account_contest",
    NowcoderRanking.account_id,
    NowcoderRanking.contest_id,
    unique=True,
)
