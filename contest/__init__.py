import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class ContestBase(DeclarativeBase):
    """比赛元信息的基类"""

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String())  # 比赛名称
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False))
    end_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False))
    url: Mapped[Optional[str]] = mapped_column(String())
