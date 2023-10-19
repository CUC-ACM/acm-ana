from typing import TYPE_CHECKING, List, Optional

from sqlalchemy.orm import Mapped, relationship

from acmana.models import SQLBase, sqlsession
from acmana.models.account import OJAccountBase

if TYPE_CHECKING:
    from acmana.models.ranking.nowcoder_ranking import NowcoderRanking
    from acmana.models.student import Student


class NowcoderAccount(OJAccountBase, SQLBase):
    """存储 `牛客账号` 信息"""

    __tablename__ = "nowcoder_account"
    rankings: Mapped[List["NowcoderRanking"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    student: Mapped[Optional["Student"]] = relationship(
        back_populates="nowcoder_account"
    )

    def __repr__(self) -> str:
        return f"NowcoderAccount(id={self.id}, nickname={self.nickname}, student={getattr(self, 'student')})"

    @staticmethod
    def query_from_student_id(student_id: str) -> Optional["NowcoderAccount"]:
        """根据学号查询"""
        stmt = sqlsession.query(NowcoderAccount).filter_by(student_id=student_id)
        return sqlsession.execute(stmt).scalar_one_or_none()
