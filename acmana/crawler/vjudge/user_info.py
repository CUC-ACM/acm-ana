import asyncio
import logging
import os
import re

import aiofiles
import aiohttp
import fake_useragent
from lxml import etree

logger = logging.getLogger(__name__)


async def get_vjudge_nickname(
    username: str, session: aiohttp.ClientSession
) -> str | None:
    cache_path = f"acmana/tmp/cache/vjudge_user_{username}.html"
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
            f"https://vjudge.net/user/{username}", headers=headers
        ) as response:
            html = await response.text()
        with open(cache_path, "w") as f:
            f.write(html)

    xpath = "/html/body/div[1]/div[2]/div[2]/span"
    try:
        nick_name: str = (
            etree.HTML(html, parser=etree.HTMLParser()).xpath(xpath)[0].text
        )
    except IndexError:
        return None
    else:
        return nick_name.strip()


async def get_vjudge_user_id(username: str, session: aiohttp.ClientSession) -> int:
    """使用 vjudge username 通过 message 接口获取 vjudge user id。注意需要设置 cookie"""
    cache_path = f"acmana/tmp/cache/vjudge_user_id_{username}.html"
    if os.getenv("DEBUG_CACHE", "False").lower() in (
        "true",
        "1",
        "t",
    ) and os.path.exists(cache_path):
        async with aiofiles.open(cache_path, mode="r") as f:
            html = await f.read()
    else:
        params = {
            "to": username,
        }
        headers = {
            "authority": "vjudge.net",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "cache-control": "max-age=0",
            "cookie": os.environ["VJUDGE_COOKIE"],
            "referer": "https://vjudge.net/",
            "sec-ch-ua": '"Chromium";v="118", "Microsoft Edge";v="118", "Not=A?Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": fake_useragent.UserAgent().random,
        }
        async with session.get(
            "https://vjudge.net/message", headers=headers, params=params
        ) as response:
            html = await response.text()
        with open(cache_path, "w") as f:
            f.write(html)

    re_vjudge_account_id = re.compile(
        r'<li class="list-group-item contact "([\s\S]*)data-contact-id="(.*)">([\w\W]*)<b>{}</b>([\w\W]*)</li>'.format(
            username
        ),
        re.M | re.I,
    )
    matchObj = re_vjudge_account_id.search(html)

    if matchObj:
        uid = int(matchObj.group(2).strip())
        logger.info(f"vjudge username: {username}, user_id: {uid}")
        return uid
    else:
        raise ValueError(f"vjudge username: {username} 不存在或者 VJUDGE_COOKIE 环境变量设置错误或过期")


if __name__ == "__main__":

    async def main():
        async with aiohttp.ClientSession() as session:
            nick_name = await get_vjudge_nickname("youngwind", session)
            print(nick_name)
            assert nick_name == "22物联网黄屹"

            nick_name = await get_vjudge_nickname("CUC_2023", session)
            print(nick_name)
            assert nick_name == "侯理想"
            id = 835096

            user_id = await get_vjudge_user_id("Chen_Lang", session)
            print(user_id)
            assert user_id == 835096

    asyncio.run(main())
