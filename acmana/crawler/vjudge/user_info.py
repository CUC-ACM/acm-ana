"""获取 vjudge 用户的 nickname, user_id 等信息"""

import asyncio
import logging
import os
import re

import aiofiles
import aiohttp
import fake_useragent
import requests
from lxml import etree

from acmana.crawler.vjudge import VjudgeCookieExpiredError

logger = logging.getLogger(__name__)

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ja;q=0.5",
    "cache-control": "max-age=0",
    "cookie": os.environ["VJUDGE_COOKIE"],
    "priority": "u=0, i",
    "sec-ch-ua": '"Microsoft Edge";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": fake_useragent.UserAgent().random,
}


async def get_vjudge_nickname(
    username: str, session: aiohttp.ClientSession
) -> str | None:
    """直接通过 vjudge 用户页面获取 nickname，不需要设置 cookie"""
    cache_path = f"acmana/tmp/cache/vjudge_user_{username}.html"
    if os.getenv("DEBUG_CACHE", "False").lower() in (
        "true",
        "1",
        "t",
    ) and os.path.exists(cache_path):
        async with aiofiles.open(cache_path, mode="r") as f:
            html = await f.read()
    else:
        html = requests.get(
            f"https://vjudge.net/user/{username}", headers=headers, timeout=10
        ).text

        with open(cache_path, "w", encoding="utf-8") as f:
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
        html = requests.get(
            "https://vjudge.net/message",
            headers=headers,
            params=params,
            allow_redirects=False,
            timeout=10,
        ).text

        with open(cache_path, "w", encoding="UTF-8") as f:
            f.write(html)

    re_vjudge_account_id = re.compile(
        r'<li class="list-group-item contact "([\s\S]*)data-contact-id="(.*)">([\w\W]*)<b>{}</b>([\w\W]*)</li>'.format(
            username
        ),
        re.M | re.I,
    )
    match_obj = re_vjudge_account_id.search(html)

    if match_obj:
        uid = int(match_obj.group(2).strip())
        logger.info(f"vjudge username: {username}, user_id: {uid}")
        return uid
    else:
        raise ValueError(
            f"vjudge username: {username} 不存在或者 VJUDGE_COOKIE 环境变量设置错误或过期"
        )


if __name__ == "__main__":

    async def main():
        async with aiohttp.ClientSession(trust_env=True) as session:
            nick_name = await get_vjudge_nickname("youngwind", session)
            print(nick_name)
            assert nick_name == "22物联网黄屹"

            nick_name = await get_vjudge_nickname("CUC_2023", session)
            print(nick_name)
            assert nick_name == "侯理想"

            user_id = await get_vjudge_user_id("Chen_Lang", session)
            print(user_id)
            assert user_id == 835096

    asyncio.run(main())
