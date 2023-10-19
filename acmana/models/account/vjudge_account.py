from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Mapped, relationship

from acmana.models import SQLBase, sqlsession
from acmana.models.account import OJAccountBase

if TYPE_CHECKING:
    from ranking.vjudge_ranking import VjudgeRanking


class VjudgeAccount(SQLBase, OJAccountBase):
    """存储 `Vjudge 账号` 信息"""

    __tablename__ = "vjudge_account"
    rankings: Mapped[List["VjudgeRanking"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"VjudgeAccount(real_name={self.student.real_name}, id={self.id}, username={self.username}, nickname={self.nickname}, student_id={self.student_id}, in_course={self.student.in_course})"

    @staticmethod
    def query_from_username(username: str) -> Optional["VjudgeAccount"]:
        stmt = select(VjudgeAccount).where(VjudgeAccount.username == username)

        return sqlsession.execute(stmt).scalar_one_or_none()

    @staticmethod
    def query_from_student_id(student_id: int) -> Optional["VjudgeAccount"]:
        """根据学号查询"""
        stmt = sqlsession.query(VjudgeAccount).filter_by(student_id=student_id)
        return sqlsession.execute(stmt).scalar_one_or_none()
