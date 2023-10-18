from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scoreanalysis.models import SQLBase
from scoreanalysis.models.ranking import RankingBase

if TYPE_CHECKING:
    from contest.nowcoder_contest import NowcoderContest
    from contestant.nowcoder_contestant import NowcoderContestant


class NowcoderRanking(SQLBase, RankingBase):
    """存储牛客 所有比赛排名 的表(各场比赛混在一起)"""

    __tablename__ = "nowcoder_ranking"
    contestant_id: Mapped[int] = mapped_column(ForeignKey("nowcoder_contestant.id"))
    contestant: Mapped["NowcoderContestant"] = relationship(back_populates="rankings")
    contest_id: Mapped[int] = mapped_column(ForeignKey("nowcoder_contest.id"))
    contest: Mapped["NowcoderContest"] = relationship(back_populates="rankings")