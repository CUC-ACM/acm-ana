import asyncio
import re

import aiohttp
import fake_useragent


async def get_nowcoder_nickname(
    nowcoder_id: int, session: aiohttp.ClientSession
) -> str | None:
    """获取牛客网昵称"""

    headers = {
        "User-Agent": fake_useragent.UserAgent().random,
    }
    async with session.get(
        f"https://ac.nowcoder.com/acm/contest/profile/{nowcoder_id}", headers=headers
    ) as response:
        re_nickname = re.compile(r'data-title="(.*)"', re.M | re.I)

        matchObj = re_nickname.search(await response.text())

        if matchObj is not None:
            return matchObj.group(1).strip()
        else:
            return None


if __name__ == "__main__":

    async def main():
        async with aiohttp.ClientSession() as session:
            nick_name = await get_nowcoder_nickname(767116230, session)
            assert nick_name == "lim_Nobody"
            now_coder_id = 804688108  # 非 contest profile
            nick_name = await get_nowcoder_nickname(now_coder_id, session)
            print(nick_name)

    asyncio.run(main())
