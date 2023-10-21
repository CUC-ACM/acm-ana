import datetime
import logging
import unittest

from acmana.crawler.vjudge.contest import VjudgeContestCrawler
from acmana.crawler.vjudge.contest.vjudge_ranking_item import VjudgeRankingItem
from acmana.models.account.vjudge_account import VjudgeAccount
from acmana.models.ranking.vjudge_ranking import VjudgeRanking

logger = logging.getLogger(__name__)


class TestVjudgeContestCrawler(unittest.TestCase):
    def test_vjudge_total_ranking_items(self):
        contest_id = 587010
        vjudge_contest_crawler = VjudgeContestCrawler(contest_id=contest_id, div="div1")

        vjudge_contest_crawler.db_vjudge_contest.commit_to_db()

        def sub_test(username: str, competition_rank: int, penalty: datetime.timedelta):
            """测试排名前三名"""
            account: VjudgeAccount = VjudgeAccount.query_from_username(username)  # type: ignore
            self.assertIsNotNone(account)
            vjudge_ranking: VjudgeRanking = VjudgeRanking.index_query(
                account_id=account.id, contest_id=contest_id  # type: ignore
            )
            self.assertIsNotNone(vjudge_ranking)
            self.assertEqual(vjudge_ranking.penalty, penalty)
            self.assertEqual(vjudge_ranking.competition_rank, competition_rank)

        logger.info(f"测试排名前三名")

        # 测试 youngwind (22物联网黄屹)
        sub_test("youngwind", 1, datetime.timedelta(hours=5, minutes=44, seconds=27))

        # 测试 fzhan (22电信车宜峰)
        sub_test("fzhan", 2, datetime.timedelta(hours=10, minutes=6, seconds=43))

        # 测试 sjkw (黄采薇) 「带有重复提交已经通过的题」
        logger.debug(f"测试 sjkw (黄采薇) 「带有重复提交已经通过的题」")
        sub_test("sjkw", 3, datetime.timedelta(hours=5, minutes=20, seconds=37))

        # No.14 ADITLINK (张博)
        sub_test("ADITLINK", 14, datetime.timedelta(hours=3, minutes=25, seconds=56))

        logger.debug(f"测试确保没有所有得分在 100 分以下")
        for vjudge_ranking in vjudge_contest_crawler.db_vjudge_contest.rankings:
            self.assertLessEqual(
                vjudge_ranking.get_score(only_among_attendance=False),
                100,
                "得分不应该超过 100 分",
            )

        logger.debug(f"测试过题数为 0 的同学的排名")

        def test_0_solve_cnt(rank: int, username: str):
            """测试过题数为 0 的同学"""
            vjudge_account: VjudgeAccount = VjudgeAccount.query_from_username(username)  # type: ignore
            self.assertIsNotNone(vjudge_account)
            vjudge_ranking: VjudgeRanking = VjudgeRanking.index_query(
                account_id=vjudge_account.id, contest_id=contest_id  # type: ignore
            )
            self.assertIsNotNone(vjudge_ranking)
            self.assertEqual(vjudge_ranking.competition_rank, rank)

        # ovovo (王玮泽)
        test_0_solve_cnt(rank=17, username="ovovo")
        # LUZHOU72 (22广电工周璐)
        test_0_solve_cnt(rank=18, username="LUZHOU72")
        # Ciallo_ (22网安杜鑫)
        test_0_solve_cnt(rank=19, username="Ciallo_")
        # NOVICIATE (李思扬)
        test_0_solve_cnt(rank=20, username="NOVICIATE")
        # STAYCARRIE (22网安程铄淇)
        test_0_solve_cnt(rank=21, username="STAYCARRIE")
        # sun_song
        test_0_solve_cnt(rank=22, username="sun_song")

        def test_vjudge_attentance_ranking_items():
            """只在「选课」的同学中计算排名得分"""

            for vjudge_ranking in filter(
                lambda x: x.account.student is not None and x.account.student.in_course,  # type: ignore
                vjudge_contest_crawler.db_vjudge_contest.rankings,
            ):
                self.assertLessEqual(
                    vjudge_ranking.get_score(only_among_attendance=True),
                    100,
                    "得分不应该超过 100 分",
                )
                vjudge_ranking.account.id

            vjudge_ranking_dict: dict[int, VjudgeRanking] = {
                ranking.account.id: ranking
                for ranking in vjudge_contest_crawler.db_vjudge_contest.rankings
            }

            # 王戈(没有参加比赛，但是补了一道题) 已选课
            crt_id = 834306
            self.assertEqual(vjudge_ranking_dict[crt_id].solved_cnt, 0)
            self.assertEqual(vjudge_ranking_dict[crt_id].penalty, datetime.timedelta())
            self.assertEqual(vjudge_ranking_dict[crt_id].upsolved_cnt, 1)
            self.assertEqual(
                vjudge_ranking_dict[crt_id].get_score(only_among_attendance=True), 6
            )
            self.assertIsNone(
                vjudge_ranking_dict[crt_id].get_attendance_ranking(), "全部排名与选课排名不同"
            )
            self.assertIsNone(
                vjudge_ranking_dict[crt_id].competition_rank, "全部排名与选课排名不同"
            )
            

            # 李思扬(参加了比赛，没有过题，没有补题)
            crt_id = 835024
            self.assertEqual(vjudge_ranking_dict[crt_id].solved_cnt, 0, "没有过题")
            self.assertEqual(vjudge_ranking_dict[crt_id].penalty, datetime.timedelta())
            self.assertEqual(vjudge_ranking_dict[crt_id].upsolved_cnt, 0, "没有补题")
            self.assertEqual(
                vjudge_ranking_dict[crt_id].get_score(only_among_attendance=True), 60
            )
            self.assertNotEqual(
                vjudge_ranking_dict[crt_id].get_attendance_ranking(),
                vjudge_ranking_dict[crt_id].competition_rank,
                "全部排名与选课排名不同",
            )

            # 车宜峰(参加了比赛，`课程中` 比赛第一名，没有补题)
            crt_id = 834865
            self.assertEqual(vjudge_ranking_dict[crt_id].solved_cnt, 3, "过了 3 题")
            self.assertEqual(
                vjudge_ranking_dict[crt_id].penalty,
                datetime.timedelta(hours=10, minutes=6, seconds=43),
            )
            self.assertEqual(vjudge_ranking_dict[crt_id].upsolved_cnt, 0, "没有补题")
            self.assertNotEqual(
                vjudge_ranking_dict[crt_id].get_attendance_ranking(),
                vjudge_ranking_dict[crt_id].competition_rank,
                "全部排名与选课排名不同",
            )

        test_vjudge_attentance_ranking_items()


if __name__ == "__main__":
    unittest.main()
