from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from contest.vjudge_contest import VjudgeContest
from contestant.vjudge_contestant import VjudgeContestant
from ranking import RankingBase


class VjudgeRanking(RankingBase):
    """存储 vjudge 所有比赛排名 的表(各场比赛混在一起)"""

    __tablename__ = "vjudge_ranking"
    contestant_id: Mapped[int] = mapped_column(ForeignKey("vjudge_contestant.id"))
    contestant: Mapped["VjudgeContestant"] = relationship(back_populates="rankings")
    contest_id: Mapped[int] = mapped_column(ForeignKey("vjudge_contest.id"))
    contest: Mapped["VjudgeContest"] = relationship(back_populates="rankings")
