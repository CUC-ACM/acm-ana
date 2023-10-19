from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from acmana.models import SQLBase, sqlsession
from acmana.models.account.nowcoder_account import NowcoderAccount
from acmana.models.account.vjudge_account import VjudgeAccount


class Student(SQLBase):
    """学生信息表"""

    __tablename__ = "student"
    __table_args__ = {"extend_existing": True}  # Add this line to redefine options and columns on an existing table object
    id: Mapped[int] = mapped_column(primary_key=True)  # 学校学号
    real_name: Mapped[Optional[str]] = mapped_column(String())
    major: Mapped[Optional[str]] = mapped_column(String())
    grade: Mapped[Optional[str]] = mapped_column(String())  # 考虑到有可能有研究生，所以用 str
    in_course: Mapped[bool] = mapped_column()  # 是否在选课名单中
    nowcoder_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("nowcoder_account.id")
    )
    # nowcoder_account: Mapped["NowcoderAccount"] = mapped_column(
    #     back_populates="student"
    # )
    vjudge_account_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("vjudge_account.id")
    )
    # vjudge_account: Mapped["VjudgeAccount"] = mapped_column(back_populates="student")

    def __repr__(self) -> str:
        return f"Student(real_name={self.real_name}, id={self.id}, major={self.major}, grade={self.grade}, in_course={self.in_course})"

    @staticmethod
    def query_from_student_id(student_id: str) -> Optional["Student"]:
        """根据学号查询"""
        stmt = sqlsession.query(Student).filter_by(id=student_id)
        return sqlsession.execute(stmt).scalar_one_or_none()
