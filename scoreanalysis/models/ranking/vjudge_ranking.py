from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from scoreanalysis.models import SQLBase
from scoreanalysis.models.ranking import RankingBase

if TYPE_CHECKING:
    from contest.vjudge_contest import VjudgeContest
    from contestant.vjudge_contestant import VjudgeContestant


class VjudgeRanking(SQLBase, RankingBase):
    """存储 vjudge 所有比赛排名 的表(各场比赛混在一起)"""

    __tablename__ = "vjudge_ranking"
    contestant_id: Mapped[int] = mapped_column(ForeignKey("vjudge_contestant.id"))
    contestant: Mapped["VjudgeContestant"] = relationship(back_populates="rankings")
    contest_id: Mapped[int] = mapped_column(ForeignKey("vjudge_contest.id"))
    contest: Mapped["VjudgeContest"] = relationship(back_populates="rankings")
