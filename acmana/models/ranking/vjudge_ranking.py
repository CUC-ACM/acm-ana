from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Index, Select, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acmana.models import SQLBase, sqlsession
from acmana.models.ranking import RankingBase

if TYPE_CHECKING:
    from acmana.models.account.vjudge_account import VjudgeAccount
    from acmana.models.contest.vjudge_contest import VjudgeContest


class VjudgeRanking(RankingBase, SQLBase):
    """存储 vjudge 所有比赛排名 的表(各场比赛混在一起)"""

    __tablename__ = "vjudge_ranking"

    account_id: Mapped[int] = mapped_column(ForeignKey("vjudge_account.id"))
    account: Mapped["VjudgeAccount"] = relationship(back_populates="rankings")
    contest_id: Mapped[int] = mapped_column(ForeignKey("vjudge_contest.id"))
    contest: Mapped["VjudgeContest"] = relationship(back_populates="rankings")

    @staticmethod
    def index_query(
        contest_id: int,
        account_id: int,
    ) -> Optional["VjudgeRanking"]:
        stmt: Select = (
            select(VjudgeRanking)
            .where(VjudgeRanking.contest_id == contest_id)
            .where(VjudgeRanking.account_id == account_id)
        )
        return sqlsession.execute(stmt).scalar_one_or_none()


# 为了防止重复提交，这里设置了唯一索引，确保同一个账号只能在同一个比赛中出现在 vjudge_ranking 中一次
Index(
    "unique_vj_account_contest",
    VjudgeRanking.account_id,
    VjudgeRanking.contest_id,
    unique=True,
)
