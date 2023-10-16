import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from contest import ContestBase
from ranking.vjudge_ranking import VjudgeRanking


class VjudgeContest(ContestBase):
    """存储 vjudge 所有比赛元信息 的表"""

    __tablename__ = "vjudge_contest"
    rankings: Mapped[List["VjudgeRanking"]] = relationship(
        back_populates="contest", cascade="all, delete-orphan"
    )
