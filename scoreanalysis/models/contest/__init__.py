import datetime
from typing import Optional

from sqlalchemy import DateTime, Select, String, select
from sqlalchemy.orm import Mapped, mapped_column

from scoreanalysis.models import sqlsession


class ContestBase:
    """比赛元信息的基类"""

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String())  # 比赛名称
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False))
    end_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False))
    div: Mapped[Optional[str]] = mapped_column(
        String()
    )  # 比赛组别："div1", "div2", "div1 & div2"

    def commit_to_db(self):
        sqlsession.add(self)
        sqlsession.commit()

    @classmethod
    def _get_query_stmt(
        cls, id: int | None = None, title: str | None = None, div: str | None = None
    ) -> Select:
        stmt = select(cls)
        if id is not None:
            stmt = stmt.where(cls.id == id)
        if title is not None:
            stmt = stmt.where(cls.title == title)
        if div is not None:
            stmt = stmt.where(cls.div == div)
        return stmt
