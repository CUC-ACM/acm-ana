import datetime
from typing import Optional

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from scoreanalysis.models import sqlsession


class ContestBase:
    """比赛元信息的基类"""

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String())  # 比赛名称
    start_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False))
    end_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False))
    url: Mapped[Optional[str]] = mapped_column(String())
    div: Mapped[Optional[str]] = mapped_column(
        String()
    )  # 比赛组别："div1", "div2", "div1 & div2"

    def commit_to_db(self):
        sqlsession.add(self)
        sqlsession.commit()
