import re
from urllib import parse

import requests

import config


def get_nowcoder_nickname(url: str) -> str | None:
    domain = parse.urlparse(url).netloc
    if domain == "www.nowcoder.com":
        nowcoder_id = url.split("/")[-1]
        url = f"https://ac.nowcoder.com/acm/contest/profile/{nowcoder_id}"

    response = requests.get(url)

    re_nickname = re.compile(r'data-title="(.*)"', re.M | re.I)
    matchObj = re_nickname.search(response.text)

    if matchObj is not None:
        return matchObj.group(1).strip()
    else:
        
        return None


if __name__ == "__main__":
    nick_name = get_nowcoder_nickname(
        "https://ac.nowcoder.com/acm/contest/profile/767116230"
    )
    print(nick_name)
    assert nick_name == "lim_Nobody"
    user_url = "https://www.nowcoder.com/users/804688108"  # 非 contest profile
    nick_name = get_nowcoder_nickname(user_url)
    print(nick_name)
