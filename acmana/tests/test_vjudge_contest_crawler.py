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

    # def test_vjudge_attentance_ranking_items(self):
    #     """测试参加了课程的同学的得分"""
    #     contest_id = 587010
    #     vjudge_contest_crawler = VjudgeContestCrawler(contest_id=contest_id, div="div1")

    #     (
    #         attendance_until_now_ranking_items,
    #         _,
    #     ) = VjudgeRankingItem.simulate_contest(
    #         only_attendance=True,
    #         vjudge_contest_crawler=vjudge_contest_crawler,
    #     )

    #     # 测试确保 get_vjudge_ranking_items() 不对 vjudge_contest_crawler.attendance_until_now_ranking_items 产生影响
    #     self.assertEqual(
    #         len(attendance_until_now_ranking_items),
    #         len(vjudge_contest_crawler.attendance_until_now_ranking_items),
    #     )

    #     for item in attendance_until_now_ranking_items:
    #         self.assertIsNotNone(
    #             item.account.student, "在参加了课程的同学排名中的同学必须已经在 student 数据库中"
    #         )
    #         self.assertTrue(item.account.student.in_course, "只测试参加了课程的同学")  # type: ignore
    #         self.assertLessEqual(item.score, 100, "得分不应该超过 100 分")

    #     item_dict: dict[int, VjudgeRankingItem] = {
    #         item.account.id: item for item in attendance_until_now_ranking_items
    #     }

    #     # 王戈(没有参加比赛，但是补了一道题)
    #     crt_id = 834306
    #     self.assertGreater(
    #         item_dict[crt_id].first_submit_time,
    #         item_dict[crt_id].vjudge_contest_crawler.db_vjudge_contest.length,  # type: ignore
    #         "没有参加比赛",
    #     )
    #     self.assertEqual(item_dict[crt_id].solved_cnt, 0)
    #     self.assertEqual(item_dict[crt_id].total_penalty, datetime.timedelta())
    #     self.assertEqual(item_dict[crt_id].upsolved_cnt, 1)
    #     self.assertEqual(item_dict[crt_id].score, 6)

    #     # 李思扬(参加了比赛，没有过题，没有补题)
    #     crt_id = 835024
    #     self.assertLessEqual(
    #         item_dict[crt_id].first_submit_time,
    #         item_dict[crt_id].vjudge_contest_crawler.db_vjudge_contest.length,  # type: ignore
    #         "参加了比赛",
    #     )
    #     self.assertEqual(item_dict[crt_id].solved_cnt, 0, "没有过题")
    #     self.assertEqual(item_dict[crt_id].total_penalty, datetime.timedelta())
    #     self.assertEqual(item_dict[crt_id].upsolved_cnt, 0, "没有补题")
    #     self.assertEqual(item_dict[crt_id].score, 60)

    #     # 车宜峰(参加了比赛，`课程中` 比赛第一名，没有补题)
    #     crt_id = 834865
    #     self.assertLessEqual(
    #         item_dict[crt_id].first_submit_time,
    #         item_dict[crt_id].vjudge_contest_crawler.db_vjudge_contest.length,  # type: ignore
    #         "参加了比赛",
    #     )
    #     self.assertEqual(item_dict[crt_id].solved_cnt, 3, "过了 3 题")
    #     self.assertEqual(
    #         item_dict[crt_id].total_penalty,
    #         datetime.timedelta(hours=10, minutes=6, seconds=43),
    #     )
    #     self.assertEqual(item_dict[crt_id].upsolved_cnt, 0, "没有补题")


if __name__ == "__main__":
    unittest.main()
