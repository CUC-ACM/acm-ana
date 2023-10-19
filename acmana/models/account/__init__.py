from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from acmana.models import sqlsession

if TYPE_CHECKING:
    from acmana.models.student import Student


class OJAccountBase:
    """各大 OJ 平台账号信息的基类"""

    id: Mapped[int] = mapped_column(primary_key=True)  # 该平台 api 接口的的账号 id
    nickname: Mapped[Optional[str]] = mapped_column(String())
    username: Mapped[str] = mapped_column(String(), unique=True)
    student_id: Mapped[Optional[str]] = mapped_column(ForeignKey("student.id"))

    def commit_to_db(self):
        sqlsession.add(self)
        sqlsession.commit()
