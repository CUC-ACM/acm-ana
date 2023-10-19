from typing import TYPE_CHECKING, Sequence

from sqlalchemy import ForeignKey, Select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acmana.models import SQLBase, sqlsession
from acmana.models.ranking import RankingBase

if TYPE_CHECKING:
    from acmana.models.contest.vjudge_contest import VjudgeContest
    from acmana.models.account.vjudge_account import VjudgeAccount


class VjudgeRanking(RankingBase, SQLBase):
    """存储 vjudge 所有比赛排名 的表(各场比赛混在一起)"""

    __tablename__ = "vjudge_ranking"
    account_id: Mapped[int] = mapped_column(ForeignKey("vjudge_account.id"))
    account: Mapped["VjudgeAccount"] = relationship(back_populates="rankings")
    contest_id: Mapped[int] = mapped_column(ForeignKey("vjudge_contest.id"))
    contest: Mapped["VjudgeContest"] = relationship(back_populates="rankings")

    @classmethod
    def query(
        cls,
        id: int | None = None,
        contest_id: int | None = None,
        account_id: int | None = None,
    ) -> Sequence["VjudgeRanking"]:
        stmt: Select = super()._get_query_stmt(id)
        if contest_id is not None:
            stmt = stmt.where(cls.contest_id == contest_id)
        if account_id is not None:
            stmt = stmt.where(cls.account_id == account_id)
        return sqlsession.execute(stmt).scalars().all()