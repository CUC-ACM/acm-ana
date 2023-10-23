import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy.orm import Mapped, relationship

from acmana.models import SQLBase, sqlsession
from acmana.models.account.vjudge_account import VjudgeAccount
from acmana.models.contest import ContestBase
from acmana.models.student import Student
from acmana.models.ranking.vjudge_ranking import VjudgeRanking

if TYPE_CHECKING:
    from acmana.models.ranking.vjudge_ranking import VjudgeRanking


class VjudgeContest(ContestBase, SQLBase):
    """存储 vjudge 所有比赛元信息 的表"""

    __tablename__ = "vjudge_contest"
    rankings: Mapped[List["VjudgeRanking"]] = relationship(
        back_populates="contest", cascade="all, delete-orphan"
    )

    def get_competition_participants_num(self, only_attendance) -> int:
        """在比赛结束前参与的人数（当场比赛排名最大的数值）"""
        if not only_attendance:  # 所有在比赛期间参加比赛的人数
            cnt1 = len(
                list(filter(lambda x: x.competition_rank is not None, self.rankings))
            )
            cnt = (
                sqlsession.query(VjudgeRanking)
                .where(VjudgeRanking.contest_id == self.id)
                .where(VjudgeRanking.competition_rank != None)
                .count()
            )
            assert cnt1 == cnt
            return cnt
        else:
            # cnt1 = len(
            #     list(
            #         filter(
            #             lambda x: x.competition_rank is not None  # 有排名(参加了比赛)
            #             and x.account.student  # 在 student 数据库中
            #             and x.account.student.in_course,  # 参加了课程
            #             self.rankings,
            #         )
            #     )
            # )
            cnt = (
                sqlsession.query(VjudgeRanking)
                .join(VjudgeAccount)
                .join(Student)
                .where(VjudgeRanking.contest_id == self.id)
                .where(Student.in_course == True)
                .where(VjudgeRanking.competition_rank != None)
                .count()
            )

            return cnt

    def get_only_attendance_rankings(self) -> List["VjudgeRanking"]:
        """获取所有参加了比赛的 VjudgeRanking"""
        return (
            sqlsession.query(VjudgeRanking)
            .join(VjudgeAccount)
            .join(Student)
            .where(VjudgeRanking.contest_id == self.id)
            .where(Student.in_course == True)
            .order_by(Student.id)
            # .where(VjudgeRanking.competition_rank != None)
            .all()
        )

    def get_rankings_append_unregistered(self) -> List["VjudgeRanking"]:
        """获取所有参加了比赛的 VjudgeRanking。将没有登记纳入 student & vjudge_account 数据库的同学 append 到最后"""
        registered = (
            sqlsession.query(VjudgeRanking)
            .join(VjudgeAccount)
            .join(Student)
            .where(VjudgeRanking.contest_id == self.id)
            .order_by(Student.id)
            # .where(VjudgeRanking.competition_rank != None)
            .all()
        )
        unregistered = (
            sqlsession.query(VjudgeRanking)
            .join(VjudgeAccount)
            .where(VjudgeRanking.contest_id == self.id)
            .where(VjudgeAccount.student_id == None)
            .all()
        )
        return registered + unregistered

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
            .filter(VjudgeContest.end <= datetime.datetime.now(datetime.timezone.utc))
            .all()
        )
