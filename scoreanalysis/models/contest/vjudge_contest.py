from typing import TYPE_CHECKING, List

from contest import ContestBase
from sqlalchemy.orm import Mapped, relationship

from scoreanalysis.models import SQLBase

if TYPE_CHECKING:
    from ranking.vjudge_ranking import VjudgeRanking


class VjudgeContest(SQLBase, ContestBase):
    """存储 vjudge 所有比赛元信息 的表"""

    __tablename__ = "vjudge_contest"
    rankings: Mapped[List["VjudgeRanking"]] = relationship(
        back_populates="contest", cascade="all, delete-orphan"
    )
