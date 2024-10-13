import datetime
import json
import logging
import os
import time

import fake_useragent
import requests
from lxml import etree

import acmana
from acmana.models.contest.nowcoder_contest import NowcoderContest

logger = logging.getLogger(__name__)


class NowcoderContestRetriever:
    def __init__(self, title_prefix: str, div: str, category: int = 15) -> None:
        """注意，目前只实现了检索网页第一页上显示的比赛，如果有更多的比赛，需要手动修改代码

        :param title_prefix: 比赛标题的前缀
        :param div: div1, div2, div3
        :param category: 15: 自主创建赛, 14: 高校校赛, 13: 牛客系列赛"""
        self.div = div
        self.title_prefix = title_prefix
        cache_path: str = (
            f"acmana/tmp/cache/nowcoder_retrive_contests_{self.title_prefix}.html"
        )
        if os.getenv("DEBUG_CACHE", "False").lower() in (
            "true",
            "1",
            "t",
        ) and os.path.exists(cache_path):
            logger.info(f"DEBUG_CACHE is True, use cache {cache_path}")
            with open(cache_path, "r", encoding="utf-8") as f:
                html: str = f.read()
        else:
            logger.info(
                f"Getting contests from nowcoder.com with title '{self.title_prefix}'......"
            )
            headers = {
                "authority": "ac.nowcoder.com",
                "user-agent": fake_useragent.UserAgent().random,
            }
            params = {
                "searchName": self.title_prefix,
                "topCategoryFilter": category,  # 自主创建赛
            }
            response = requests.get(
                "https://ac.nowcoder.com/acm-heavy/acm/contest/search-detail",
                params=params,
                headers=headers,
            )
            html = response.text
            with open(cache_path, "w", encoding="utf-8") as f:
                f.write(html)

        self.retrieved_contests: list["NowcoderContest"] = []
        xpath = "/html/body/div[1]/div[2]/section/table/tbody/tr"
        for element in etree.HTML(html, parser=etree.HTMLParser()).xpath(xpath):
            # contest_id = int(herf.split("/")[-1])
            contest_id = element.attrib["data-id"]
            data_json = json.loads(element.attrib["data-json"].replace("&quot;", '"'))
            title: str = data_json["contestName"]
            begin: datetime.datetime = datetime.datetime.utcfromtimestamp(
                data_json["contestStartTime"] / 1000
            ).replace(tzinfo=datetime.timezone.utc)
            end: datetime.datetime = datetime.datetime.utcfromtimestamp(
                data_json["contestEndTime"] / 1000
            ).replace(tzinfo=datetime.timezone.utc)
            if end - begin < datetime.timedelta(minutes=20):
                logger.warning(f"比赛 {title} 的时长小于 20 分钟，跳过")
                continue
            nowcoder_contest: NowcoderContest = NowcoderContest.query_from_id(  # type: ignore
                contest_id
            )
            if nowcoder_contest is None:  # 如果数据库中没有这个比赛——>新建
                nowcoder_contest = NowcoderContest(
                    id=contest_id, div=div, title=title, begin=begin, end=end
                )
            else:  # 如果数据库中有这个比赛——>更新
                nowcoder_contest.title = title
                nowcoder_contest.div = self.div
                nowcoder_contest.begin = begin
                nowcoder_contest.end = end
            self.retrieved_contests.append(nowcoder_contest)


if __name__ == "__main__":
    nowcoder_contest_retriever = NowcoderContestRetriever(
        title_prefix=acmana.config["nowcoder"]["instances"]["div2"]["title_prefix"],
        div="div2",
    )
    for contest in nowcoder_contest_retriever.retrieved_contests:
        print(contest)
        contest.commit_to_db()
