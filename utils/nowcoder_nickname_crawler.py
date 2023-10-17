import asyncio
import re
from urllib import parse

import aiohttp
import fake_useragent
import requests

import config


async def get_nowcoder_nickname(url: str, session: aiohttp.ClientSession) -> str | None:
    domain = parse.urlparse(url).netloc
    if domain == "www.nowcoder.com":
        nowcoder_id = url.split("/")[-1]
        url = f"https://ac.nowcoder.com/acm/contest/profile/{nowcoder_id}"
    elif domain == "m.nowcoder.com":
        nowcoder_id = url.split("/")[-1]
        url = f"https://ac.nowcoder.com/acm/contest/profile/{nowcoder_id}"

    headers = {
        "User-Agent": fake_useragent.UserAgent().random,
    }
    async with session.get(url, headers=headers) as response:
        re_nickname = re.compile(r'data-title="(.*)"', re.M | re.I)

        matchObj = re_nickname.search(await response.text())

        if matchObj is not None:
            return matchObj.group(1).strip()
        else:
            return None


async def main():
    async with aiohttp.ClientSession() as session:
        nick_name = await get_nowcoder_nickname(
            "https://ac.nowcoder.com/acm/contest/profile/767116230", session
        )
        assert nick_name == "lim_Nobody"
        user_url = "https://www.nowcoder.com/users/804688108"  # 非 contest profile
        nick_name = await get_nowcoder_nickname(user_url, session)
        print(nick_name)


if __name__ == "__main__":
    asyncio.run(main())
