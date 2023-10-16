from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class ContestantBase(DeclarativeBase):
    """参赛者信息的基类"""

    id: Mapped[int] = mapped_column(primary_key=True)
    real_name: Mapped[Optional[str]] = mapped_column(String())
    student_id: Mapped[Optional[str]] = mapped_column(String(), unique=True)
    nickname: Mapped[Optional[str]] = mapped_column(String())
    username: Mapped[str] = mapped_column(String())
    is_in_coures: Mapped[bool] = mapped_column()  # 是否在选课名单中
