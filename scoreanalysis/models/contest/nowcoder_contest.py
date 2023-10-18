import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from contest import ContestBase
from scoreanalysis.models import SQLBase

if TYPE_CHECKING:
    from ranking.nowcoder_ranking import NowcoderRanking


class NowcoderContest(SQLBase, ContestBase):
    """存储牛客 所有比赛元信息 的表"""

    __tablename__ = "nowcoder_contest"
    rankings: Mapped[List["NowcoderRanking"]] = relationship(
        back_populates="contest", cascade="all, delete-orphan"
    )
