import asyncio
import unittest
from unittest import IsolatedAsyncioTestCase

import aiohttp
from scoreanalysis.crawler.vjudge import get_nickname

from scoreanalysis.crawler.nowcoder import get_nickname


class TestNicknameCrawler(IsolatedAsyncioTestCase):
    nowcoder_profile_url = "https://ac.nowcoder.com/acm/contest/profile/767116230"
    vjudge_profile_url = "https://vjudge.net/user/youngwind"

    async def test_nowcoder_nickname_crawler(self):
        async with aiohttp.ClientSession() as session:
            nick_name = await get_nickname.get_nowcoder_nickname(
                TestNicknameCrawler.nowcoder_profile_url, session
            )
            self.assertEqual(nick_name, "lim_Nobody")
            nick_name = await get_nickname.get_nowcoder_nickname(
                TestNicknameCrawler.vjudge_profile_url, session
            )
            self.assertEqual(nick_name, None)

    async def test_vjudge_nickname_crawler(self):
        async with aiohttp.ClientSession() as session:
            nick_name = await get_nickname.get_vjudge_nickname(
                TestNicknameCrawler.vjudge_profile_url, session
            )
            self.assertEqual(nick_name, "22物联网黄屹")

            nick_name = await get_nickname.get_vjudge_nickname(
                TestNicknameCrawler.nowcoder_profile_url, session
            )
            self.assertEqual(nick_name, None)

    async def test_nowcoder_user_profile(self):
        """测试非 contest profile 的 nowcoder 用户主页"""

        async with aiohttp.ClientSession() as session:
            nowcoder_user_profile_url = "https://www.nowcoder.com/users/804688108"
            user_profile = await get_nickname.get_nowcoder_nickname(
                nowcoder_user_profile_url, session
            )
            self.assertEqual(user_profile, "23数科闻学兵")


if __name__ == "__main__":
    unittest.main()
