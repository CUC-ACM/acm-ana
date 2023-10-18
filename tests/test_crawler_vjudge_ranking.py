import asyncio
import datetime
import json
import logging
import unittest
from unittest import IsolatedAsyncioTestCase

import aiofiles
import aiohttp
import fake_useragent

import config
from contestant.vjudge_contestant import VjudgeContestant
from crawler.vjudge_contest_crawler import VjudgeContestCrawler
from crawler.vjudge_ranking import VjudgeRankingItem
from ranking.vjudge_ranking import VjudgeRanking

logger = logging.getLogger(__name__)


class TestCrawlerVjudgeRanking(IsolatedAsyncioTestCase):
    async def test_nowcoder_nickname_crawler(self):
        async with aiohttp.ClientSession() as aiosession:
            vjudge_ranking_items = await VjudgeRankingItem.get_vjudge_ranking_items(
                contest_id=587010, aiosession=aiosession
            )
        logger.info(f"测试排名前三名")
        # 测试 youngwind (22物联网黄屹)
        accurate_penalty = datetime.timedelta(hours=5, minutes=44, seconds=27)
        self.assertEqual(vjudge_ranking_items[0].total_penalty, accurate_penalty)

        # 测试 fzhan (22电信车宜峰)
        accurate_penalty = datetime.timedelta(hours=10, minutes=6, seconds=43)
        self.assertEqual(vjudge_ranking_items[1].total_penalty, accurate_penalty)

        logger.info(f"测试 sjkw (黄采薇) 「带有重复提交已经通过的题」")
        # 测试 sjkw (黄采薇) 「带有重复提交已经通过的题」
        accurate_penalty = datetime.timedelta(hours=5, minutes=20, seconds=37)
        self.assertEqual(vjudge_ranking_items[2].total_penalty, accurate_penalty)

        # No.14 ADITLINK (张博)
        logger.info(f"测试 No.14 ADITLINK (张博)")
        self.assertEqual(vjudge_ranking_items[13].contestant.username, "ADITLINK")

        logger.info(f"测试过题数为 0 的同学的排名")

        def test_0_solve_cnt(rank: int, username: str):
            """测试过题数为 0 的同学"""
            logger.info(f"测试过题数为 0 的同学: {vjudge_ranking_items[rank]}")
            self.assertEqual(vjudge_ranking_items[rank].contestant.username, username)
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


if __name__ == "__main__":
    unittest.main()
