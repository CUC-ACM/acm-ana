import unittest

from utils import nowcoder_nickname_crawler, vjudge_nickname_crawler


class TestNicknameCrawler(unittest.TestCase):
    nowcoder_profile_url = "https://ac.nowcoder.com/acm/contest/profile/767116230"
    vjudge_profile_url = "https://vjudge.net/user/youngwind"

    def test_nowcoder_nickname_crawler(self):
        nick_name = nowcoder_nickname_crawler.get_nowcoder_nickname(
            TestNicknameCrawler.nowcoder_profile_url
        )
        self.assertEqual(nick_name, "lim_Nobody")
        nick_name = nowcoder_nickname_crawler.get_nowcoder_nickname(
            TestNicknameCrawler.vjudge_profile_url
        )
        self.assertEqual(nick_name, None)

    def test_vjudge_nickname_crawler(self):
        nick_name = vjudge_nickname_crawler.get_vjudge_nickname(
            TestNicknameCrawler.vjudge_profile_url
        )
        self.assertEqual(nick_name, "22物联网黄屹")

        nick_name = vjudge_nickname_crawler.get_vjudge_nickname(
            TestNicknameCrawler.nowcoder_profile_url
        )
        self.assertEqual(nick_name, None)

    def test_nowcoder_user_profile(self):
        """测试非 contest profile 的 nowcoder 用户主页"""

        nowcoder_user_profile_url = "https://www.nowcoder.com/users/804688108"
        user_profile = nowcoder_nickname_crawler.get_nowcoder_nickname(
            nowcoder_user_profile_url
        )
        self.assertEqual(user_profile, "23数科闻学兵")


if __name__ == "__main__":
    unittest.main()