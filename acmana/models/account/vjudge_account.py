from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Mapped, relationship

from acmana.models import SQLBase, sqlsession
from acmana.models.account import OJAccountBase

if TYPE_CHECKING:
    from ranking.vjudge_ranking import VjudgeRanking


class VjudgeContestant(SQLBase, OJAccountBase):
    """存储 vjudge 所有参赛者信息 的表

    注意：同时参加 `牛客` 和 `Vjudge` 的同一人不被视作一个 Contestant"""

    __tablename__ = "vjudge_contestant"
    rankings: Mapped[List["VjudgeRanking"]] = relationship(
        back_populates="contestant", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"VjudgeContestant(real_name={self.student.real_name}, id={self.id}, username={self.username}, nickname={self.nickname}, student_id={self.student_id}, is_in_course={self.student.in_course})"

    @staticmethod
    def query_from_username(username: str) -> Optional["VjudgeContestant"]:
        stmt = select(VjudgeContestant).where(VjudgeContestant.username == username)

        return sqlsession.execute(stmt).scalar_one_or_none()

    @staticmethod
    def query_from_student_id(student_id: int) -> Optional["VjudgeContestant"]:
        """根据学号查询"""
        stmt = sqlsession.query(VjudgeContestant).filter_by(student_id=student_id)
        return sqlsession.execute(stmt).scalar_one_or_none()
