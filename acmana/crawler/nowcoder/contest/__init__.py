import bisect
import datetime
import json
import logging
import os
import re

import fake_useragent
import requests

from acmana.models.contest.nowcoder_contest import NowcoderContest

logger = logging.getLogger(__name__)


class NowcoderContestCrawler:
    def __init__(self, contest_id: int, div: str) -> None:
        self._contest_id = contest_id
        self.db_nowcoder_contest: NowcoderContest = NowcoderContest.query_from_id(contest_id)  # type: ignore
        if self.db_nowcoder_contest is None:
            self.db_nowcoder_contest = NowcoderContest(id=contest_id, div=div)

        self._contest_metadata: dict = self.crawl_contest_metadata_json()
        self.db_nowcoder_contest.title = self._contest_metadata["name"]
        self.db_nowcoder_contest.begin = datetime.datetime.utcfromtimestamp(
            self._contest_metadata["startTime"] / 1000
        )
        self.db_nowcoder_contest.end = datetime.datetime.utcfromtimestamp(
            self._contest_metadata["endTime"] / 1000
        )

    def crawl_contest_metadata_json(self) -> dict:
        """获取比赛的基础信息"""
        cache_path = f"acmana/tmp/cache/nowcoder_contest_{self._contest_id}.html"
        if os.getenv("DEBUG_CACHE", "False").lower() in (
            "true",
            "1",
            "t",
        ) and os.path.exists(cache_path):
            with open(cache_path, "r") as f:
                html = f.read()
        else:
            headers = {
                "authority": "ac.nowcoder.com",
                "user-agent": fake_useragent.UserAgent().random,
            }

            response = requests.get(
                f"https://ac.nowcoder.com/acm/contest/{self.db_nowcoder_contest.id}",
                headers=headers,
            )
            html = response.text
            with open(cache_path, "w") as f:
                f.write(html)

        re_contest_info = re.compile(r"window.pageInfo = ([\w\W]*);\s+window.gioInfo")

        matchObj = re_contest_info.search(html)

        if matchObj is not None:
            return json.loads(matchObj.group(1).strip())
        else:
            raise RuntimeError(f"比赛 {self.db_nowcoder_contest} 信息获取失败")


if __name__ == "__main__":
    nowcoder_contest_crawler = NowcoderContestCrawler(67345, "div2")
    print(nowcoder_contest_crawler.db_nowcoder_contest)
    nowcoder_contest_crawler.db_nowcoder_contest.commit_to_db()
