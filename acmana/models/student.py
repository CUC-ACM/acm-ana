import logging
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acmana.models import SQLBase, sqlsession

if TYPE_CHECKING:
    from acmana.models.account.nowcoder_account import NowcoderAccount
    from acmana.models.account.vjudge_account import VjudgeAccount

logger = logging.getLogger(__name__)


class Student(SQLBase):
    """学生信息表"""

    __tablename__ = "student"

    id: Mapped[str] = mapped_column(primary_key=True)  # 学校学号
    real_name: Mapped[Optional[str]] = mapped_column(String())
    major: Mapped[Optional[str]] = mapped_column(String())
    grade: Mapped[Optional[str]] = mapped_column(String())  # 考虑到有可能有研究生，所以用 str
    in_course: Mapped[Optional[bool]] = mapped_column()  # 是否在选课名单中
    nowcoder_account: Mapped[Optional["NowcoderAccount"]] = relationship(
        "NowcoderAccount", back_populates="student"
    )
    vjudge_account: Mapped[Optional["VjudgeAccount"]] = relationship(
        "VjudgeAccount", back_populates="student"
    )

    def __repr__(self) -> str:
        return f"Student(real_name={self.real_name}, id={self.id}, major={self.major}, grade={self.grade}, in_course={self.in_course})"

    def commit_to_db(self):
        logger.info(f"commiting {self} to db......")
        sqlsession.add(self)
        sqlsession.commit()

    @staticmethod
    def query_from_student_id(student_id: str) -> Optional["Student"]:
        """根据学号查询"""
        stmt = sqlsession.query(Student).filter_by(id=student_id)
        return sqlsession.execute(stmt).scalar_one_or_none()
