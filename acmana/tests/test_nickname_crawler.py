import unittest
from unittest import IsolatedAsyncioTestCase

import aiohttp

from acmana.crawler.nowcoder.get_nickname import get_nowcoder_nickname
from acmana.crawler.vjudge.user_info import get_vjudge_nickname


class TestNicknameCrawler(IsolatedAsyncioTestCase):
    nowcoder_id = "767116230"
    vjudge_username = "youngwind"

    async def test_nowcoder_nickname_crawler(self):
        async with aiohttp.ClientSession() as session:
            nick_name = await get_nowcoder_nickname(
                TestNicknameCrawler.nowcoder_id, session
            )
            self.assertEqual(nick_name, "lim_Nobody")
            nick_name = await get_nowcoder_nickname(
                TestNicknameCrawler.vjudge_username, session
            )
            self.assertEqual(nick_name, None)
            nowcoder_user_id = "804688108"
            user_profile = await get_nowcoder_nickname(
                nowcoder_user_id, session
            )
            self.assertEqual(user_profile, "23数科闻学兵")

    async def test_vjudge_nickname_crawler(self):
        async with aiohttp.ClientSession() as session:
            nick_name = await get_vjudge_nickname(
                TestNicknameCrawler.vjudge_username, session
            )
            self.assertEqual(nick_name, "22物联网黄屹")

            nick_name = await get_vjudge_nickname(
                TestNicknameCrawler.nowcoder_id, session
            )
            self.assertEqual(nick_name, None)


if __name__ == "__main__":
    unittest.main()
