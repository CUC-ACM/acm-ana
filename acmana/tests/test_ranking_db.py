import datetime
import logging
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from acmana.models import SQLBase
from acmana.models.account.vjudge_account import VjudgeAccount
from acmana.models.contest.vjudge_contest import VjudgeContest
from acmana.models.ranking.nowcoder_ranking import NowcoderRanking
from acmana.models.ranking.vjudge_ranking import VjudgeRanking
from acmana.models.student import Student

logger = logging.getLogger(__name__)


class TestRankingDB(unittest.TestCase):
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    testsqlsession = Session()  # Use memeory database for testing

    def setUp(self):
        logger.warning(f"Using {self.engine} for testing......")
        SQLBase.metadata.create_all(self.engine)
        self.student1 = Student(
            id="201701010101",
            real_name="张三",
            major="计算机科学与技术",
            grade="2023",
            in_course=True,
        )
        self.student1.commit_to_db(self.testsqlsession)
        self.student2 = Student(
            id="201701010102",
            real_name="李四",
            major="网络空间安全",
            grade="2022",
            in_course=True,
        )
        self.student2.commit_to_db(self.testsqlsession)
        self.contest1 = VjudgeContest(
            id=8908,
            title="某个 database 测试训练赛",
            div="div1",
            begin=datetime.datetime(
                year=2023,
                month=10,
                day=1,
                hour=5,
                minute=30,
            ),
            end=datetime.datetime(
                year=2023,
                month=10,
                day=1,
                hour=9,
            ),
        )
        self.contest1.commit_to_db(self.testsqlsession)
        self.student1.vjudge_account = VjudgeAccount(
            username="student1_vjudge_username",
            id=15354,
            student_id=self.student1.id,
            nickname="student1_vjudge_nickname",
        )
        self.student1_vj_contest1_ranking = VjudgeRanking(
            account_id=self.student1.vjudge_account.id,
            contest_id=self.contest1.id,
            competition_rank=1,
            solved_cnt=3,
            upsolved_cnt=1,
            penalty=datetime.timedelta(hours=1, minutes=30),
        )
        self.student1_vj_contest1_ranking.commit_to_db(self.testsqlsession)

    def tearDown(self):
        logger.info("Finished, Dropping all tables......")
        SQLBase.metadata.drop_all(self.engine)
        pass

    def test_ranking_unique(self):
        """确保同一个账号只能在同一个比赛中出现在 nowcoder_ranking 中一次"""
        from sqlalchemy.exc import IntegrityError

        # 同一个账号在同一个比赛中出现两次
        wrong_student1_vj_contest1_ranking = VjudgeRanking(
            account_id=self.student1.vjudge_account.id,  # type: ignore
            contest_id=self.contest1.id,
            competition_rank=2,  # 这里又排名为 2
            solved_cnt=2,
            upsolved_cnt=1,
            penalty=datetime.timedelta(hours=1, minutes=30),
        )

        self.assertRaises(
            IntegrityError,
            wrong_student1_vj_contest1_ranking.commit_to_db,
            self.testsqlsession,
        )


if __name__ == "__main__":
    unittest.main()
