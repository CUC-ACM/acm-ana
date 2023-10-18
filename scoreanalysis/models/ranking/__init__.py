from sqlalchemy import Float, Integer
from sqlalchemy.orm import Mapped, mapped_column

from scoreanalysis.models import sqlsession


class RankingBase:
    """排名信息的基类(各场比赛混在一起)"""

    id: Mapped[int] = mapped_column(primary_key=True)
    competition_rank: Mapped[int] = mapped_column(Integer())
    score: Mapped[float] = mapped_column(Float())
    solved_cnt: Mapped[int] = mapped_column(Integer())
    upsolved_cnt: Mapped[int] = mapped_column(Integer())  # 补题数
    penalty: Mapped[int] = mapped_column(Integer())  # 罚时

    def commit_to_db(self):
        sqlsession.add(self)
        sqlsession.commit()
