from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from contestant import ContestantBase
from scoreanalysis.models.sql_base import SQLBase

if TYPE_CHECKING:
    from ranking.nowcoder_ranking import NowcoderRanking


class NowcoderContestant(SQLBase, ContestantBase):
    """存储 牛客 所有参赛者信息 的表

    注意：同时参加 `牛客` 和 `Vjudge` 的同一人不被视作一个 Contestant"""

    __tablename__ = "nowcoder_contestant"
    rankings: Mapped[List["NowcoderRanking"]] = relationship(
        back_populates="contestant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"NowcoderContestant(real_name={self.real_name}, id={self.id}, username={self.username}, nickname={self.nickname}, student_id={self.student_id}, is_in_course={self.is_in_course})"
