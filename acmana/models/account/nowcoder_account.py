from typing import TYPE_CHECKING, List, Optional

from sqlalchemy.orm import Mapped, relationship

from acmana.models import SQLBase, sqlsession
from acmana.models.account import OJAccountBase
from acmana.models.student import Student

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
        return f"NowcoderAccount(id={self.id}, nickname={self.nickname}, student={self.student})"

    @staticmethod
    def query_from_student_id(student_id: str) -> Optional["NowcoderAccount"]:
        """根据学号查询"""
        stmt = sqlsession.query(NowcoderAccount).filter_by(student_id=student_id)
        return sqlsession.execute(stmt).scalar_one_or_none()

    @staticmethod
    def query_all_attendance() -> List["NowcoderAccount"]:
        """查询参加了 nowcoder 比赛的账号"""
        return (
            sqlsession.query(NowcoderAccount)
            .join(Student)
            .where(Student.in_course == True)
            .order_by(Student.id)
            .all()
        )

    @staticmethod
    def query_all_append_unregistered() -> List["NowcoderAccount"]:
        """查询所有 vjudge 账号，包括未注册的"""
        registered = (
            sqlsession.query(NowcoderAccount)
            .where(NowcoderAccount.student_id != None)
            .order_by(NowcoderAccount.student_id)
            .all()
        )
        unregistered = (
            sqlsession.query(NowcoderAccount)
            .where(NowcoderAccount.student_id == None)
            .all()
        )
        return registered + unregistered
