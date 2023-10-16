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


if __name__ == "__main__":
    unittest.main()
