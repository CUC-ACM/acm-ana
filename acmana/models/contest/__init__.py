import datetime
import logging
from typing import Optional

import pytz
import sqlalchemy
from sqlalchemy import DateTime, Select, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from acmana.models import sqlsession


logger = logging.getLogger(__name__)


class BeijingDatetime(sqlalchemy.types.TypeDecorator):
    """参见 https://mike.depalatis.net/blog/sqlalchemy-timestamps.html

    用于将 datetime.datetime 转换为 UTC 时间并存储在数据库中
    """

    cache_ok = False
    impl = sqlalchemy.types.DateTime

    LOCAL_TIMEZONE = pytz.timezone("Asia/Shanghai")

    def process_bind_param(self, value: datetime.datetime, dialect):
        if value.tzinfo is None:
            # value = value.astimezone(self.BJ_TIMEZONE)
            raise ValueError(
                "datetime object must be timezone-aware!需要将 datetime 对象转换为时区感知对象！"
            )

        return value.astimezone(datetime.timezone.utc)  # 转换为 UTC 时间存储

    def process_result_value(self, value: datetime.datetime, dialect):
        if value.tzinfo is None:
            # 数据库中存储的是 UTC 时间，所以需要将其转换为 aware 的 UTC 时间
            return pytz.utc.localize(value, is_dst=None).astimezone(self.LOCAL_TIMEZONE)
        else:
            raise ValueError("SQLite 中的 datetime 对象必须是 unware 的！")


class ContestBase:
    """比赛元信息的基类"""

    id: Mapped[int] = mapped_column(primary_key=True)  # 该平台 api 接口的的比赛 id
    title: Mapped[str] = mapped_column(String())  # 比赛名称
    begin: Mapped[datetime.datetime] = mapped_column(BeijingDatetime())
    end: Mapped[datetime.datetime] = mapped_column(BeijingDatetime())
    div: Mapped[Optional[str]] = mapped_column(
        String()
    )  # 比赛组别："div1", "div2", "div1 & div2"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.title}, id: {self.id}, div: {self.div}, {self.begin} ~ {self.end})"

    @property
    def length(self) -> datetime.timedelta:
        return self.end - self.begin

    def commit_to_db(self, sqlsession: Session = sqlsession):
        logger.info(f"Committing contest {self} to database......")
        sqlsession.add(self)
        sqlsession.commit()

    @classmethod
    def _get_query_stmt(
        cls, id: int | None = None, title: str | None = None, div: str | None = None
    ) -> Select:
        stmt = select(cls)
        if id is not None:
            stmt = stmt.where(cls.id == id)
        if title is not None:
            stmt = stmt.where(cls.title == title)
        if div is not None:
            stmt = stmt.where(cls.div == div)
        return stmt

    @classmethod
    def query_from_id(cls, id: int) -> Optional["ContestBase"]:
        return sqlsession.execute(cls._get_query_stmt(id)).scalar_one_or_none()
