import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from contest import ContestBase
from ranking.nowcoder_ranking import NowcoderRanking


class NowcoderContest(ContestBase):
    """存储牛客 所有比赛元信息 的表"""

    __tablename__ = "nowcoder_contest"
    rankings: Mapped[List["NowcoderRanking"]] = relationship(
        back_populates="contest", cascade="all, delete-orphan"
    )
