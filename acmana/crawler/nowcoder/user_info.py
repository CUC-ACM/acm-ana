import asyncio
import os
import re

import aiofiles
import aiohttp
import fake_useragent


async def get_nowcoder_nickname(
    nowcoder_id: int, session: aiohttp.ClientSession
) -> str | None:
    """获取牛客网昵称"""
    cache_path = f"acmana/tmp/cache/nowcoder_user_{nowcoder_id}.html"
    if os.getenv("DEBUG_CACHE", "False").lower() in (
        "true",
        "1",
        "t",
    ) and os.path.exists(cache_path):
        async with aiofiles.open(cache_path, mode="r") as f:
            html = await f.read()
    else:
        headers = {
            "User-Agent": fake_useragent.UserAgent().random,
        }
        async with session.get(
            f"https://ac.nowcoder.com/acm/contest/profile/{nowcoder_id}",
            headers=headers,
        ) as response:
            html = await response.text()
        with open(cache_path, "w") as f:
            f.write(html)

    re_nickname = re.compile(r'data-title="(.*)"', re.M | re.I)

    matchObj = re_nickname.search(html)

    if matchObj is not None:
        return matchObj.group(1).strip()
    else:
        return None


if __name__ == "__main__":

    async def main():
        async with aiohttp.ClientSession(trust_env=True) as session:
            nick_name = await get_nowcoder_nickname(767116230, session)
            assert nick_name == "lim_Nobody"
            now_coder_id = 804688108  # 非 contest profile
            nick_name = await get_nowcoder_nickname(now_coder_id, session)
            print(nick_name)

    asyncio.run(main())
