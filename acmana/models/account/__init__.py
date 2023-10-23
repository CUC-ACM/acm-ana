import logging
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from acmana.models import sqlsession

if TYPE_CHECKING:
    from acmana.models.student import Student

logger = logging.getLogger(__name__)


class OJAccountBase:
    """各大 OJ 平台账号信息的基类"""

    id: Mapped[int] = mapped_column(primary_key=True)  # 该平台 api 接口的的账号 id
    nickname: Mapped[Optional[str]] = mapped_column(String())
    student_id: Mapped[Optional[str]] = mapped_column(ForeignKey("student.id"))

    def commit_to_db(self, sqlsession: Session = sqlsession):
        logger.debug(f"commiting {self} to db......")
        sqlsession.add(self)
        sqlsession.commit()

    @classmethod
    def query_from_account_id(cls, id: int) -> Optional["OJAccountBase"]:
        stmt = sqlsession.query(cls).filter_by(id=id)
        return sqlsession.execute(stmt).scalar_one_or_none()
