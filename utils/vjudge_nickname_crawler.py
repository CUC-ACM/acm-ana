import requests
from lxml import etree


def get_vjudge_nickname(url: str) -> str | None:
    response = requests.get(url)
    xpath = "/html/body/div[1]/div[2]/div[2]/span"
    try:
        nick_name: str = (
            etree.HTML(response.text, parser=etree.HTMLParser()).xpath(xpath)[0].text
        )
    except IndexError:
        return None
    else:
        return nick_name.strip()


if __name__ == "__main__":
    nick_name = get_vjudge_nickname("https://vjudge.net/user/youngwind")
    print(nick_name)
    assert nick_name == "22物联网黄屹"

    nick_name = get_vjudge_nickname(
        "https://ac.nowcoder.com/acm/contest/profile/767116230"
    )
    print(nick_name)
    assert nick_name == None
