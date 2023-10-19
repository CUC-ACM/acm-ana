import datetime
import logging
from typing import Optional

from sqlalchemy import DateTime, Select, String, select
from sqlalchemy.orm import Mapped, mapped_column

from acmana.models import sqlsession

logger = logging.getLogger(__name__)


class ContestBase:
    """比赛元信息的基类"""

    id: Mapped[int] = mapped_column(primary_key=True)  # 该平台 api 接口的的比赛 id
    title: Mapped[str] = mapped_column(String())  # 比赛名称
    begin: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False))
    end: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=False))
    div: Mapped[Optional[str]] = mapped_column(
        String()
    )  # 比赛组别："div1", "div2", "div1 & div2"

    def commit_to_db(self):
        logger.info(f"Committing contest {self} to database......")
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

    @classmethod
    def query_from_id(cls, id: int) -> Optional["ContestBase"]:
        return sqlsession.execute(cls._get_query_stmt(id)).scalar_one_or_none()
