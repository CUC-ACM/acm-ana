import asyncio
import json

import aiohttp
import fake_useragent


async def get_ranking_page(
    contest_id: int,
    page: int,
    session: aiohttp.ClientSession,
    ranking_pages: list[dict],
):
    headers = {
        "authority": "ac.nowcoder.com",
        "referer": f"https://ac.nowcoder.com/acm/contest/{contest_id}",
        "user-agent": fake_useragent.UserAgent().random,
    }
    params = {
        "token": "",
        "id": contest_id,
        "page": page,
        "limit": "0",
        "_": "1697961389311",
    }
    async with session.get(
        "https://ac.nowcoder.com/acm-heavy/acm/contest/real-time-rank-data",
        params=params,
        headers=headers,
    ) as response:
        ranking_pages.append(await response.json())


async def fetch_contest_ranking(contest_id: int) -> list[dict]:
    ranking_pages: list[dict] = []
    async with aiohttp.ClientSession() as client_session:
        await get_ranking_page(contest_id, 1, client_session, ranking_pages)
        total_page = ranking_pages[0]["data"]["basicInfo"]["pageCount"]
        tasks = [
            asyncio.create_task(
                get_ranking_page(contest_id, page, client_session, ranking_pages)
            )
            for page in range(2, total_page + 1)
        ]
        await asyncio.gather(*tasks)
    return ranking_pages


if __name__ == "__main__":
    contest_id = 67345
    with open(f"acmana/tmp/nowcoder_rank_{contest_id}.json", "w") as f:
        json.dump(
            asyncio.run(fetch_contest_ranking(67345)),
            f,
            indent=4,
            ensure_ascii=False,
        )
