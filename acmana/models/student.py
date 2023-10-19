from typing import Optional, TYPE_CHECKING

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from acmana.models import SQLBase, sqlsession

if TYPE_CHECKING:
    from acmana.models.contestant import OJAccountBase

class Student(SQLBase):
    """学生信息表"""

    __tablename__ = "student"
    id: Mapped[str] = mapped_column(primary_key=True)  # 学校学号
    real_name: Mapped[Optional[str]] = mapped_column(String())
    major: Mapped[Optional[str]] = mapped_column(String())
    grade: Mapped[Optional[str]] = mapped_column(String())  # 考虑到有可能有研究生，所以用 str
    in_course: Mapped[bool] = mapped_column()  # 是否在选课名单中
    oj_accounts: Mapped[list["OJAccountBase"]] = mapped_column(
        "OJAccountBase", back_populates="student", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"Student(real_name={self.real_name}, id={self.id}, major={self.major}, grade={self.grade}, in_course={self.in_course})"

    @staticmethod
    def query_from_student_id(student_id: str) -> Optional["Student"]:
        """根据学号查询"""
        stmt = sqlsession.query(Student).filter_by(id=student_id)
        return sqlsession.execute(stmt).scalar_one_or_none()
