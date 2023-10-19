from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import String, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acmana.models import SQLBase, sqlsession
from acmana.models.account import OJAccountBase

if TYPE_CHECKING:
    from acmana.models.ranking.vjudge_ranking import VjudgeRanking
    from acmana.models.student import Student


class VjudgeAccount(OJAccountBase, SQLBase):
    """存储 `Vjudge 账号` 信息"""

    __tablename__ = "vjudge_account"
    username: Mapped[str] = mapped_column(String(), nullable=False)
    rankings: Mapped[List["VjudgeRanking"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    student: Mapped[Optional["Student"]] = relationship(back_populates="vjudge_account")

    def __repr__(self) -> str:
        return f"VjudgeAccount(id={self.id}, username={self.username}, nickname={self.nickname}, student={getattr(self, 'student'), None})"

    @staticmethod
    def query_from_username(username: str) -> Optional["VjudgeAccount"]:
        stmt = select(VjudgeAccount).where(VjudgeAccount.username == username)

        return sqlsession.execute(stmt).scalar_one_or_none()

    @staticmethod
    def query_from_student_id(student_id: str) -> Optional["VjudgeAccount"]:
        """根据学号查询"""
        stmt = sqlsession.query(VjudgeAccount).filter_by(student_id=student_id)
        return sqlsession.execute(stmt).scalar_one_or_none()
