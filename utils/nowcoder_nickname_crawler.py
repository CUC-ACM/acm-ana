import re

import requests


def get_nowcoder_nickname(url: str) -> str | None:
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
