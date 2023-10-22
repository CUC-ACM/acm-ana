import asyncio
import datetime
import json
import os

import aiohttp
import fake_useragent

from acmana.crawler.nowcoder.contest import NowcoderContestCrawler
from acmana.models.account.nowcoder_account import NowcoderAccount

cookie = os.environ["NOWCODER_COOKIE"]


class NowcoderSubmission:
    def __init__(
        self,
        problem_id: int,
        accepted: bool,
        time: datetime.timedelta,
        db_nowcoder_account: NowcoderAccount,
        contest_crawler: "NowcoderContestCrawler",
    ) -> None:
        self.problem_id = problem_id
        self.accepted: bool = accepted
        self.time: datetime.timedelta = time
        self.db_nowcoder_account: NowcoderAccount = db_nowcoder_account
        self.contest_crawler: NowcoderContestCrawler = contest_crawler

    def __repr__(self) -> str:
        return f"account: {self.db_nowcoder_account} promble_id: {self.problem_id}, accepted: {self.accepted}, time: {self.time}"


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
    submission_jsons.sort(key=lambda x: x["data"]["basicInfo"]["pageCurrent"])
    return submission_jsons


if __name__ == "__main__":
    submission_jsons = asyncio.run(fetch_contest_submisions(67345))
    with open("acmana/tmp/nowcoder_submissions_aio.json", "w") as f:
        json.dump(submission_jsons, f, indent=4, ensure_ascii=False)
