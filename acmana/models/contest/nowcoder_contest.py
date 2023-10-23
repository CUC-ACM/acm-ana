import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy.orm import Mapped, relationship

from acmana.models import SQLBase, sqlsession
from acmana.models.account.nowcoder_account import NowcoderAccount
from acmana.models.contest import ContestBase
from acmana.models.ranking.nowcoder_ranking import NowcoderRanking
from acmana.models.student import Student

if TYPE_CHECKING:
    from acmana.models.ranking.nowcoder_ranking import NowcoderRanking


class NowcoderContest(ContestBase, SQLBase):
    """存储牛客 所有比赛元信息 的表"""

    __tablename__ = "nowcoder_contest"
    rankings: Mapped[List["NowcoderRanking"]] = relationship(
        back_populates="contest", cascade="all, delete-orphan"
    )

    @staticmethod
    def query_from_id(id: int) -> Optional["NowcoderContest"]:
        return (
            sqlsession.query(NowcoderContest)
            .where(NowcoderContest.id == id)
            .one_or_none()
        )

    def get_competition_participants_num(self, only_attendance) -> int:
        """在比赛结束前参与的人数（当场比赛排名最大的数值）"""
        if not only_attendance:  # 所有在比赛期间参加比赛的人数
            cnt1 = len(
                list(filter(lambda x: x.competition_rank is not None, self.rankings))
            )
            cnt = (
                sqlsession.query(NowcoderRanking)
                .where(NowcoderRanking.contest_id == self.id)
                .where(NowcoderRanking.competition_rank != None)
                .count()
            )
            assert cnt1 == cnt
            return cnt
        else:
            cnt = (
                sqlsession.query(NowcoderRanking)
                .join(NowcoderAccount)
                .join(Student)
                .where(NowcoderRanking.contest_id == self.id)
                .where(Student.in_course == True)
                .where(NowcoderRanking.competition_rank != None)
                .count()
            )

            return cnt

    def get_only_attendance_rankings(self) -> List["NowcoderRanking"]:
        """获取所有参加了比赛的 NowcoderRanking"""
        return (
            sqlsession.query(NowcoderRanking)
            .join(NowcoderAccount)
            .join(Student)
            .where(NowcoderRanking.contest_id == self.id)
            .where(Student.in_course == True)
            .order_by(Student.id)
            # .where(NowcoderRanking.competition_rank != None)
            .all()
        )

    @staticmethod
    def query_finished_contests() -> List["NowcoderContest"]:
        return (
            sqlsession.query(NowcoderContest)
            .filter(NowcoderContest.end <= datetime.datetime.now(datetime.timezone.utc))
            .all()
        )

    def get_rankings_append_unregistered(self) -> List["NowcoderRanking"]:
        """获取所有参加了比赛的 NowcoderRanking。将没有登记纳入 student & nowcoder_account 数据库的同学 append 到最后"""
        registered = (
            sqlsession.query(NowcoderRanking)
            .join(NowcoderAccount)
            .join(Student)
            .where(NowcoderRanking.contest_id == self.id)
            .order_by(Student.id)
            # .where(NowcoderRanking.competition_rank != None)
            .all()
        )
        unregistered = (
            sqlsession.query(NowcoderRanking)
            .join(NowcoderAccount)
            .where(NowcoderRanking.contest_id == self.id)
            .where(NowcoderAccount.student_id == None)
            .all()
        )
        return registered + unregistered
