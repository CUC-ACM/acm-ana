from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class RankingBase:
    """排名信息的基类(各场比赛混在一起)"""

    id: Mapped[int] = mapped_column(primary_key=True)
    competition_rank: Mapped[int] = mapped_column(Integer())
    score: Mapped[float] = mapped_column(Float())
    solved_cnt: Mapped[int] = mapped_column(Integer())
    upsolved_cnt: Mapped[int] = mapped_column(Integer())  # 补题数
    penalty: Mapped[int] = mapped_column(Integer())  # 罚时
