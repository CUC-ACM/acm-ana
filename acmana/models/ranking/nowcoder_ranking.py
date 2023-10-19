from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acmana.models import SQLBase
from acmana.models.ranking import RankingBase

if TYPE_CHECKING:
    from acmana.models.contest.nowcoder_contest import NowcoderContest
    from acmana.models.account.nowcoder_account import NowcoderAccount


class NowcoderRanking(RankingBase, SQLBase):
    """存储牛客 所有比赛排名 的表(各场比赛混在一起)"""

    __tablename__ = "nowcoder_ranking"
    account_id: Mapped[int] = mapped_column(ForeignKey("nowcoder_account.id"))
    account: Mapped["NowcoderAccount"] = relationship(back_populates="rankings")
    contest_id: Mapped[int] = mapped_column(ForeignKey("nowcoder_contest.id"))
    contest: Mapped["NowcoderContest"] = relationship(back_populates="rankings")