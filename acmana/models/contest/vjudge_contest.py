import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy.orm import Mapped, relationship

from acmana.models import SQLBase, sqlsession
from acmana.models.contest import ContestBase

if TYPE_CHECKING:
    from ranking.vjudge_ranking import VjudgeRanking


class VjudgeContest(ContestBase, SQLBase):
    """存储 vjudge 所有比赛元信息 的表"""

    __tablename__ = "vjudge_contest"
    rankings: Mapped[List["VjudgeRanking"]] = relationship(
        back_populates="contest", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"VjudgeContest({self.title}, id: {self.id}, div: {self.div}, {self.begin} ~ {self.end})"

    def get_competition_participants_num(self, only_attendance) -> int:
        """在比赛结束前参与的人数（当场比赛排名最大的数值）"""
        if not only_attendance:  # 所有在比赛期间参加比赛的人数
            return len(
                list(filter(lambda x: x.competition_rank is not None, self.rankings))
            )
        else:
            return len(
                list(
                    filter(
                        lambda x: x.competition_rank is not None  # 有排名(参加了比赛)
                        and x.account.student  # 在 student 数据库中
                        and x.account.student.in_course,  # 参加了课程
                        self.rankings,
                    )
                )
            )

    @staticmethod
    def query_from_id(id: int) -> Optional["VjudgeContest"]:
        return (
            sqlsession.query(VjudgeContest).filter(VjudgeContest.id == id).one_or_none()
        )

    @staticmethod
    def query_all() -> List["VjudgeContest"]:
        return sqlsession.query(VjudgeContest).all()

    @staticmethod
    def query_finished_contests() -> List["VjudgeContest"]:
        return (
            sqlsession.query(VjudgeContest)
            .filter(VjudgeContest.end <= datetime.datetime.utcnow())
            .all()
        )
