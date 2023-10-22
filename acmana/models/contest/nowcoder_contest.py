from typing import TYPE_CHECKING, List, Optional

from sqlalchemy.orm import Mapped, relationship

from acmana.models import SQLBase, sqlsession
from acmana.models.contest import ContestBase

if TYPE_CHECKING:
    from acmana.models.ranking.nowcoder_ranking import NowcoderRanking


class NowcoderContest(ContestBase, SQLBase):
    """存储牛客 所有比赛元信息 的表"""

    __tablename__ = "nowcoder_contest"
    rankings: Mapped[List["NowcoderRanking"]] = relationship(
        back_populates="contest", cascade="all, delete-orphan"
    )

    @staticmethod
    def query_from_id(id: int) -> Optional["NowcoderContest"]:
        return (
            sqlsession.query(NowcoderContest)
            .where(NowcoderContest.id == id)
            .one_or_none()
        )
