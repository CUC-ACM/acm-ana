from typing import TYPE_CHECKING, Sequence

from sqlalchemy import ForeignKey, Select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acmana.models import SQLBase, sqlsession
from acmana.models.ranking import RankingBase

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

    @classmethod
    def query(
        cls,
        id: int | None = None,
        contest_id: int | None = None,
        contestant_id: int | None = None,
    ) -> Sequence["VjudgeRanking"]:
        stmt: Select = super()._get_query_stmt(id)
        if contest_id is not None:
            stmt = stmt.where(cls.contest_id == contest_id)
        if contestant_id is not None:
            stmt = stmt.where(cls.contestant_id == contestant_id)
        return sqlsession.execute(stmt).scalars().all()
