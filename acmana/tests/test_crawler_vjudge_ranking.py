import datetime
import logging
import unittest
from unittest import IsolatedAsyncioTestCase

import aiohttp

from acmana.crawler.vjudge.ranker import VjudgeRankingItem

logger = logging.getLogger(__name__)


class TestCrawlerVjudgeRanking(IsolatedAsyncioTestCase):
    async def test_vjudge_total_ranking_items(self):
        async with aiohttp.ClientSession() as aiosession:
            _, vjudge_ranking_items = await VjudgeRankingItem.get_vjudge_ranking_items(
                contest_id=587010, aiosession=aiosession
            )
        logger.debug(f"测试排名前三名")
        # 测试 youngwind (22物联网黄屹)
        accurate_penalty = datetime.timedelta(hours=5, minutes=44, seconds=27)
        self.assertEqual(vjudge_ranking_items[0].total_penalty, accurate_penalty)

        # 测试 fzhan (22电信车宜峰)
        accurate_penalty = datetime.timedelta(hours=10, minutes=6, seconds=43)
        self.assertEqual(vjudge_ranking_items[1].total_penalty, accurate_penalty)

        logger.debug(f"测试 sjkw (黄采薇) 「带有重复提交已经通过的题」")
        # 测试 sjkw (黄采薇) 「带有重复提交已经通过的题」
        accurate_penalty = datetime.timedelta(hours=5, minutes=20, seconds=37)
        self.assertEqual(vjudge_ranking_items[2].total_penalty, accurate_penalty)

        # No.14 ADITLINK (张博)
        logger.debug(f"测试 No.14 ADITLINK (张博)")
        self.assertEqual(vjudge_ranking_items[13].account.username, "ADITLINK")

        logger.debug(f"测试过题数为 0 的同学的排名")

        def test_0_solve_cnt(rank: int, username: str):
            """测试过题数为 0 的同学"""
            logger.debug(f"测试过题数为 0 的同学: {vjudge_ranking_items[rank]}")
            self.assertEqual(vjudge_ranking_items[rank].account.username, username)
            self.assertEqual(
                vjudge_ranking_items[rank].total_penalty, datetime.timedelta()
            )
            self.assertEqual(vjudge_ranking_items[rank].solved_cnt, 0)

        # ovovo (王玮泽)
        test_0_solve_cnt(rank=-6, username="ovovo")
        # LUZHOU72 (22广电工周璐)
        test_0_solve_cnt(rank=-5, username="LUZHOU72")
        # Ciallo_ (22网安杜鑫)
        test_0_solve_cnt(rank=-4, username="Ciallo_")
        # NOVICIATE (李思扬)
        test_0_solve_cnt(rank=-3, username="NOVICIATE")
        # STAYCARRIE (22网安程铄淇)
        test_0_solve_cnt(rank=-2, username="STAYCARRIE")
        # sun_song
        test_0_solve_cnt(rank=-1, username="sun_song")

    async def test_vjudge_attentance_ranking_items(self):
        """测试 vjudge_attentance_ranking_items(参加了课程的同学的排名)"""
        async with aiohttp.ClientSession() as aiosession:
            (
                vjudge_attendance_total_ranking_items,
                _,
            ) = await VjudgeRankingItem.get_vjudge_ranking_items(
                contest_id=587010, aiosession=aiosession, only_attendance=True
            )

        for item in vjudge_attendance_total_ranking_items:
            self.assertIsNotNone(
                item.account.student, "在参加了课程的同学排名中的同学必须已经在 student 数据库中"
            )
            self.assertTrue(item.account.student.in_course, "只测试参加了课程的同学")  # type: ignore
            self.assertLessEqual(item.score, 100, "得分不应该超过 100 分")

        item_dict: dict[int, VjudgeRankingItem] = {
            item.vaccount_id: item for item in vjudge_attendance_total_ranking_items
        }

        # 王戈(没有参加比赛，但是补了一道题)
        crt_id = 834306
        self.assertGreater(
            item_dict[crt_id].first_submit_time,
            item_dict[crt_id].contest.length,  # type: ignore
            "没有参加比赛",
        )
        self.assertEqual(item_dict[crt_id].solved_cnt, 0)
        self.assertEqual(item_dict[crt_id].total_penalty, datetime.timedelta())
        self.assertEqual(item_dict[crt_id].upsolved_cnt, 1)
        self.assertEqual(item_dict[crt_id].score, 6)

        # 李思扬(参加了比赛，没有过题，没有补题)
        crt_id = 835024
        self.assertLessEqual(
            item_dict[crt_id].first_submit_time,
            item_dict[crt_id].contest.length,  # type: ignore
            "参加了比赛",
        )
        self.assertEqual(item_dict[crt_id].solved_cnt, 0, "没有过题")
        self.assertEqual(item_dict[crt_id].total_penalty, datetime.timedelta())
        self.assertEqual(item_dict[crt_id].upsolved_cnt, 0, "没有补题")
        self.assertEqual(item_dict[crt_id].score, 60)

        # 车宜峰(参加了比赛，`课程中` 比赛第一名，没有补题)
        crt_id = 834865
        self.assertLessEqual(
            item_dict[crt_id].first_submit_time,
            item_dict[crt_id].contest.length,  # type: ignore
            "参加了比赛",
        )
        self.assertEqual(item_dict[crt_id].solved_cnt, 3, "过了 3 题")
        self.assertEqual(
            item_dict[crt_id].total_penalty,
            datetime.timedelta(hours=10, minutes=6, seconds=43),
        )
        self.assertEqual(item_dict[crt_id].upsolved_cnt, 0, "没有补题")


if __name__ == "__main__":
    unittest.main()
