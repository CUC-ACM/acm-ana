from typing import TYPE_CHECKING, List

from contest import ContestBase
from sqlalchemy.orm import Mapped, relationship

from scoreanalysis.models import SQLBase

if TYPE_CHECKING:
    from ranking.nowcoder_ranking import NowcoderRanking


class NowcoderContest(SQLBase, ContestBase):
    """存储牛客 所有比赛元信息 的表"""

    __tablename__ = "nowcoder_contest"
    rankings: Mapped[List["NowcoderRanking"]] = relationship(
        back_populates="contest", cascade="all, delete-orphan"
    )
