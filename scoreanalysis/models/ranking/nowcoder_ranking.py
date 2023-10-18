from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from ranking import RankingBase
from scoreanalysis.models import SQLBase

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
