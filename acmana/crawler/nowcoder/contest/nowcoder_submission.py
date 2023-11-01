import asyncio
import datetime
import json
import logging
import os
from typing import TYPE_CHECKING

import aiohttp
import fake_useragent

from acmana.crawler.nowcoder.contest.nowcoder_ranking_item import NowcoderRankingItem
from acmana.models.account.nowcoder_account import NowcoderAccount

if TYPE_CHECKING:
    from acmana.crawler.nowcoder.contest import NowcoderContestCrawler

logger = logging.getLogger(__name__)

cookie = os.environ["NOWCODER_COOKIE"]


class NowcoderSubmission:
    def __init__(
        self,
        problem_id: int,
        accepted: bool,
        time_from_begin: datetime.timedelta,
        db_nowcoder_account: NowcoderAccount,
        contest_crawler: "NowcoderContestCrawler",
    ) -> None:
        self.problem_id = problem_id
        self.accepted: bool = accepted
        self.time_from_begin: datetime.timedelta = time_from_begin
        self.db_nowcoder_account: NowcoderAccount = db_nowcoder_account
        self.contest_crawler: "NowcoderContestCrawler" = contest_crawler

    @classmethod
    def from_api_submission_dict(
        cls,
        api_submission_dict: dict,
        contest_crawler: "NowcoderContestCrawler",
    ):
        problem_id: int = api_submission_dict["problemId"]
        accepted: bool = (
            True if api_submission_dict["statusMessage"] == "答案正确" else False
        )
        time_from_begin = (
            datetime.datetime.utcfromtimestamp(
                int(api_submission_dict["submitTime"] / 1000)
            ).replace(tzinfo=datetime.timezone.utc)
            - contest_crawler.db_nowcoder_contest.begin
        )
        nowcoder_account_id = api_submission_dict["userId"]
        if nowcoder_account_id not in contest_crawler.nowcoder_ranking_items_dict:
            logger.info(
                f"First Submission! Nowcoder Ranking Item {nowcoder_account_id}, contest_id: {contest_crawler._contest_id} not found, create a new 「NowcoderRankingItem」......"
            )
            contest_crawler.nowcoder_ranking_items_dict[
                nowcoder_account_id
            ] = NowcoderRankingItem(
                nowcoder_account_id=nowcoder_account_id,
                nowcoder_account_nickename=api_submission_dict["userName"],
                nowcoder_contest_crawler=contest_crawler,
            )
            contest_crawler.nowcoder_ranking_items_dict[
                nowcoder_account_id
            ].db_account.commit_to_db()

        return cls(
            problem_id=problem_id,
            accepted=accepted,
            time_from_begin=time_from_begin,
            db_nowcoder_account=contest_crawler.nowcoder_ranking_items_dict[
                nowcoder_account_id
            ].db_account,
            contest_crawler=contest_crawler,
        )

    def __repr__(self) -> str:
        return f"account: {self.db_nowcoder_account} promble_id: {self.problem_id}, accepted: {self.accepted}, time: {self.time_from_begin}"


async def get_submission_page(
    contest_id: int,
    page: int,
    session: aiohttp.ClientSession,
    submission_jsons: list[dict],
):
    params = {
        "token": "",
        "id": contest_id,
        "pageSize": "50",
        "page": page,
        "searchUserName": "",
        "_": "1697959628450",
    }
    headers = {
        "User-Agent": fake_useragent.UserAgent().random,
        "Referer": f"https://ac.nowcoder.com/acm/contest/{contest_id}",
        "cookie": cookie,
    }

    async with session.get(
        "https://ac.nowcoder.com/acm-heavy/acm/contest/status-list",
        params=params,
        headers=headers,
    ) as response:
        submission_jsons.append(await response.json())


async def fetch_contest_submisions(contest_id: int) -> list[dict]:
    """去除其他信息，只保留提交 `列表`"""
    submission_jsons: list[dict] = []
    async with aiohttp.ClientSession() as client_session:
        await get_submission_page(contest_id, 1, client_session, submission_jsons)
        total_page = submission_jsons[0]["data"]["basicInfo"]["pageCount"]

        tasks: list[asyncio.Task] = [
            asyncio.create_task(
                get_submission_page(contest_id, page, client_session, submission_jsons)
            )
            for page in range(2, total_page + 1)
        ]
        await asyncio.gather(*tasks)

    if submission_jsons[0]["data"]["basicInfo"]["statusCount"] == 200:
        raise ValueError(
            f"比赛 {contest_id} 只爬取到 200 条提交，这多半是因为 NOWCODER_COOKIE 过期导致的"
            "（当然也不排除这次比赛的提交次数刚好等于 200 次数导致的）"
            "请更新 NOWCODER_COOKIE 环境变量！"
        )

    submission_jsons.sort(key=lambda x: x["data"]["basicInfo"]["pageCurrent"])
    submission_list: list[dict] = []
    for submission_json in submission_jsons:
        submission_list.extend(submission_json["data"]["data"])
    logger.info(
        f"fetch {len(submission_list)} submissions from nowcoder contest {contest_id}"
    )
    assert submission_jsons[0]["data"]["basicInfo"]["statusCount"] == len(
        submission_list
    ), "len(submission_list) 与 submission_jsons 中元数据显示的的总提交数目不一致"
    return submission_list


if __name__ == "__main__":
    submission_jsons = asyncio.run(fetch_contest_submisions(67976))
    with open("acmana/tmp/nowcoder_submissions_aio.json", "w") as f:
        json.dump(submission_jsons, f, indent=4, ensure_ascii=False)
