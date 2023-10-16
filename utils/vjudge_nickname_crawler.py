import asyncio

import aiohttp
import requests
from lxml import etree


async def get_vjudge_nickname(url: str, session: aiohttp.ClientSession) -> str | None:
    async with session.get(url) as response:
        xpath = "/html/body/div[1]/div[2]/div[2]/span"
        try:
            nick_name: str = (
                etree.HTML(await response.text(), parser=etree.HTMLParser())
                .xpath(xpath)[0]
                .text
            )
        except IndexError:
            return None
        else:
            return nick_name.strip()


async def main():
    async with aiohttp.ClientSession() as session:
        nick_name = await get_vjudge_nickname(
            "https://vjudge.net/user/youngwind", session
        )
        print(nick_name)
        assert nick_name == "22物联网黄屹"

        nick_name = await get_vjudge_nickname(
            "https://ac.nowcoder.com/acm/contest/profile/767116230", session
        )
        print(nick_name)
        assert nick_name == None


if __name__ == "__main__":
    asyncio.run(main())
