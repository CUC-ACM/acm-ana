import asyncio
import unittest
from unittest import IsolatedAsyncioTestCase

import aiohttp

from acmana.crawler.nowcoder.user_info import get_nowcoder_nickname
from acmana.crawler.vjudge.user_info import get_vjudge_nickname, get_vjudge_user_id


class TestUserInfoCrawler(IsolatedAsyncioTestCase):
    nowcoder_id = 767116230
    vjudge_username = "youngwind"

    async def test_nowcoder_user_info_crawler(self):
        async with aiohttp.ClientSession() as session:
            nick_name = await get_nowcoder_nickname(
                TestUserInfoCrawler.nowcoder_id, session
            )
            self.assertEqual(nick_name, "lim_Nobody")
            nick_name = await get_nowcoder_nickname(
                TestUserInfoCrawler.vjudge_username, session  # type: ignore
            )
            self.assertEqual(nick_name, None)
            nowcoder_user_id = 804688108
            user_profile = await get_nowcoder_nickname(nowcoder_user_id, session)
            self.assertEqual(user_profile, "23数科闻学兵")

    async def test_vjudge_user_info_crawler(self):
        async with aiohttp.ClientSession() as session:

            async def test_nick_name_youngwind():
                nick_name_youngwind = await get_vjudge_nickname(
                    TestUserInfoCrawler.vjudge_username, session
                )
                self.assertEqual(nick_name_youngwind, "22物联网黄屹")

            async def test_nick_name_LUZHOU72_none():
                nick_name_LUZHOU72 = await get_vjudge_nickname(
                    TestUserInfoCrawler.nowcoder_id, session  # type: ignore
                )
                self.assertEqual(nick_name_LUZHOU72, None)

            async def test_vjudge_user_id():
                user_id = await get_vjudge_user_id("LUZHOU72", session)
                self.assertEqual(user_id, 834670)

            async def test_vjudge_user_id_exception():
                with self.assertRaises(ValueError):
                    user_id = await get_vjudge_user_id("x5u4iiuqfdadfe892w", session)
                    print(user_id)

            await asyncio.gather(
                test_nick_name_youngwind(),
                test_nick_name_LUZHOU72_none(),
                test_vjudge_user_id(),
                test_vjudge_user_id_exception(),
            )


if __name__ == "__main__":
    unittest.main()
