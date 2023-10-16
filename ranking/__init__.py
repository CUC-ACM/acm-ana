from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class RankingBase(DeclarativeBase):
    """排名信息的基类(各场比赛混在一起)"""

    id: Mapped[int] = mapped_column(primary_key=True)
    rank: Mapped[int] = mapped_column(Integer())
    score: Mapped[int] = mapped_column(Integer())
