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
    """获取比赛终榜，其直接返回 `比赛终榜的全部排名列表` 而过滤掉其他的 api page 分页信息和一些关于比赛的元数据"""
    ranking_pages: list[dict] = []
    async with aiohttp.ClientSession(trust_env=True) as client_session:
        await get_ranking_page(contest_id, 1, client_session, ranking_pages)
        total_page = ranking_pages[0]["data"]["basicInfo"]["pageCount"]
        tasks = [
            asyncio.create_task(
                get_ranking_page(contest_id, page, client_session, ranking_pages)
            )
            for page in range(2, total_page + 1)
        ]
        await asyncio.gather(*tasks)

    rankings: list[dict] = []
    for ranking_page in ranking_pages:
        rankings.extend(ranking_page["data"]["rankData"])

    return rankings


if __name__ == "__main__":
    contest_id = 67345
    rankings = asyncio.run(fetch_contest_ranking(67345))
    with open(f"acmana/tmp/nowcoder_rank_{contest_id}.json", "w") as f:
        rankings = json.dump(rankings, f, indent=4, ensure_ascii=False)
