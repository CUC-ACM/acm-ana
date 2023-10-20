import logging

from sqlalchemy import Float, Integer, Select, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from acmana.models import sqlsession

logger = logging.getLogger(__name__)


class RankingBase:
    """排名信息的基类(各场比赛混在一起)"""

    id: Mapped[int] = mapped_column(primary_key=True)
    competition_rank: Mapped[int | None] = mapped_column(Integer())
    score: Mapped[float] = mapped_column(Float())
    solved_cnt: Mapped[int] = mapped_column(Integer())
    upsolved_cnt: Mapped[int] = mapped_column(Integer())  # 补题数
    penalty: Mapped[int] = mapped_column(Integer())  # 罚时

    def commit_to_db(self, sqlsession: Session = sqlsession):
        logger.info(f"commiting {self} to db......")
        sqlsession.add(self)
        sqlsession.commit()

    @classmethod
    def _get_query_stmt(cls, id: int | None = None) -> Select:
        stmt = select(cls)
        if id is not None:
            stmt = stmt.where(cls.id == id)
        return stmt
