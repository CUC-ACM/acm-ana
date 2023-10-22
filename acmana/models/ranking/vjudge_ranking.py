from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Index, Select, select
from sqlalchemy.orm import Mapped, mapped_column, relationship

from acmana.models import SQLBase, sqlsession
from acmana.models.account.vjudge_account import VjudgeAccount
from acmana.models.ranking import RankingBase
from acmana.models.student import Student

if TYPE_CHECKING:
    from acmana.models.account.vjudge_account import VjudgeAccount
    from acmana.models.contest.vjudge_contest import VjudgeContest


class VjudgeRanking(RankingBase, SQLBase):
    """存储 vjudge 所有比赛排名 的表(各场比赛混在一起)"""

    __tablename__ = "vjudge_ranking"

    account_id: Mapped[int] = mapped_column(ForeignKey("vjudge_account.id"))
    account: Mapped["VjudgeAccount"] = relationship(back_populates="rankings")
    contest_id: Mapped[int] = mapped_column(ForeignKey("vjudge_contest.id"))
    contest: Mapped["VjudgeContest"] = relationship(back_populates="rankings")

    @staticmethod
    def query_all() -> list["VjudgeRanking"]:
        return sqlsession.query(VjudgeRanking).all()

    @staticmethod
    def index_query(
        contest_id: int,
        account_id: int,
    ) -> Optional["VjudgeRanking"]:
        stmt: Select = (
            select(VjudgeRanking)
            .with_hint(VjudgeRanking, "unique_vj_account_contest")
            .where(VjudgeRanking.contest_id == contest_id)
            .where(VjudgeRanking.account_id == account_id)
        )
        return sqlsession.execute(stmt).scalar_one_or_none()

    def get_attendance_ranking(self) -> int | None:
        """根据总参加比赛的排名，排除未选课的同学，计算选课的同学的「相对排名」"""

        if self.account.student is None or self.account.student.in_course is False:
            raise ValueError("该账号不是选课的同学或者不在 student 数据库中")

        if self.competition_rank is None:  # 没有参加比赛
            return None

        # 只计算在课程中的同学的排名（排除未选课的同学）
        # attendance_competiton_rank = list(
        #     filter(
        #         lambda x: x.competition_rank is not None  # 有排名(参加了比赛)
        #         and x.account.student  # 在 student 数据库中
        #         and x.account.student.in_course,  # 参加了课程
        #         self.contest.rankings,
        #     )
        # )
        sqlattendance_competiton_rank = (
            sqlsession.query(VjudgeRanking)
            .join(VjudgeAccount)
            .join(Student)
            .where(VjudgeRanking.contest_id == self.contest_id)
            .where(VjudgeRanking.competition_rank != None)
            .where(Student.in_course == True)
            .order_by(VjudgeRanking.competition_rank)
        ).all()
        # 从高到低排序
        # attendance_competiton_rank.sort(
        #     key=lambda x: x.competition_rank  # type: ignore
        # )  # 选课的同学按照总排名从小到大排序

        # assert len(sqlattendance_competiton_rank)  == len(attendance_competiton_rank)
        # for i, j in zip(sqlattendance_competiton_rank, attendance_competiton_rank):
        #     assert i.account_id == j.account_id
        #     assert i.competition_rank == j.competition_rank

        for i, ranking in enumerate(sqlattendance_competiton_rank, 1):
            if ranking.account_id == self.account_id:
                return i

        raise ValueError("发生了逻辑错误")  # 这个分支不应该被执行到

    def get_score(self, only_among_attendance: bool) -> int:
        """计算得分
        :param: only_among_attendance: 是否只计算在课程中的同学的得分
        :return: 得分
        """
        if only_among_attendance:
            if self.account.student is None or self.account.student.in_course is False:
                raise ValueError(
                    f"账号 {self.account} 不是选课的同学或者不在 student 数据库中，不应该在 only_among_attendance=True 的情况下计算得分"
                )
        ranking: int | None
        total: int = self.contest.get_competition_participants_num(
            only_attendance=only_among_attendance
        )
        score: float = 0
        if only_among_attendance is True:
            ranking = self.get_attendance_ranking()
        else:
            ranking = self.competition_rank
        # 1. 参加了比赛——>比赛期间得分
        if ranking is not None:
            percentage: float = ranking / total
            if percentage <= 0.2:
                score += 100
            elif percentage <= 0.4:
                score += 90
            elif percentage <= 0.6:
                score += 80
            elif percentage <= 0.8:
                score += 70
            else:
                score += 60
        # 2. 补题得分
        score += self.upsolved_cnt * 6
        return min(100, score)


# 为了防止重复提交，这里设置了唯一索引，确保同一个账号只能在同一个比赛中出现在 vjudge_ranking 中一次
Index(
    "unique_vj_account_contest",
    VjudgeRanking.account_id,
    VjudgeRanking.contest_id,
    unique=True,
)
