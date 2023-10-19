from typing import TYPE_CHECKING, List

from sqlalchemy.orm import Mapped, relationship

from acmana.models import SQLBase
from acmana.models.contest import ContestBase

if TYPE_CHECKING:
    from acmana.models.ranking.nowcoder_ranking import NowcoderRanking


class NowcoderContest(ContestBase, SQLBase):
    """存储牛客 所有比赛元信息 的表"""

    __tablename__ = "nowcoder_contest"
    rankings: Mapped[List["NowcoderRanking"]] = relationship(
        back_populates="contest", cascade="all, delete-orphan"
    )
