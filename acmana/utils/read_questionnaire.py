import asyncio
import logging

import aiohttp
import pandas as pd
from fake_useragent import UserAgent

import acmana
from acmana.crawler.nowcoder.user_info import get_nowcoder_nickname
from acmana.crawler.vjudge.user_info import get_vjudge_nickname
from acmana.models.contestant.nowcoder_contestant import NowcoderContestant
from acmana.models.contestant.vjudge_contestant import VjudgeContestant

logger = logging.getLogger(__name__)

ua = UserAgent()


async def read_nowcoder_questionnaire(df: pd.DataFrame):
    async with aiohttp.ClientSession() as aiosession:
        for index, row in df.iterrows():
            student_id = row["学号（必填）"]
            cached_nowcoder_contestant = NowcoderContestant.query_from_student_id(
                student_id=student_id
            )
            if (
                cached_nowcoder_contestant
                and acmana.config["input"]["using_nickname_cache"]
                and cached_nowcoder_contestant.nickname
            ):  # using cache
                logger.debug(
                    f"牛客网昵称已缓存: {row['姓名（必填）']}, nickname: {cached_nowcoder_contestant.nickname}"
                )
                continue

            newcoder_url = row["牛客个人主页网址（必填）"]
            nickname = await get_nowcoder_nickname(newcoder_url, aiosession)
            if nickname == None:
                logger.warning(f"牛客网昵称获取失败: {row['姓名（必填）']}: {newcoder_url}")

            else:
                logger.debug(f"牛客网昵称获取成功: {row['姓名（必填）']}: {newcoder_url}: {nickname}")

            is_in_course: bool
            if row["是否在选课系统中选上课（必填）"] == "是":
                is_in_course = True
            else:
                is_in_course = False
            nowcoder_contestant = NowcoderContestant(
                real_name=row["姓名（必填）"],
                student_id=row["学号（必填）"],
                nickname=nickname,
                username=row["牛客个人主页网址（必填）"].split("/")[-1],
                is_in_course=is_in_course,
                major=row["专业全称（必填）"],
                grade=row["年级（必填）"][:-1],
                div="div2",
            )
            if cached_nowcoder_contestant is not None:  # update
                cached_nowcoder_contestant.nickname = nickname
                cached_nowcoder_contestant.commit_to_db()
            else:
                nowcoder_contestant.commit_to_db()


async def read_vjudge_questionnaire(df: pd.DataFrame):
    async with aiohttp.ClientSession() as aiosession:
        for index, row in df.iterrows():
            student_id = row["学号（必填）"]
            cached_vjudge_contestant = VjudgeContestant.query_from_student_id(
                student_id=student_id
            )

            if (
                cached_vjudge_contestant
                and acmana.config["input"]["using_nickname_cache"]
                and cached_vjudge_contestant.nickname
            ):  # using cache
                logger.debug(
                    f"Vjudge网昵称已缓存: {row['姓名（必填）']}, nickname: {cached_vjudge_contestant.nickname}"
                )
                continue

            is_in_course: bool
            if row["是否在选课系统中选上课（必填）"] == "是":
                is_in_course = True
            else:
                is_in_course = False

            vjudge_username = row["Vjudge 个人主页网址（必填）"].split("/")[-1]
            nickname = await get_vjudge_nickname(vjudge_username, aiosession)
            if nickname == None:
                logger.warning(f"Vjudge网昵称获取失败: {row['姓名（必填）']}: {vjudge_username}")
            else:
                logger.debug(
                    f"Vjudge网昵称获取成功: {row['姓名（必填）']}: username: {vjudge_username}, nickname: {nickname}"
                )

            vjudge_contestant = VjudgeContestant(
                real_name=row["姓名（必填）"],
                student_id=row["学号（必填）"],
                nickname=nickname,
                username=row["Vjudge 个人主页网址（必填）"].split("/")[-1],
                is_in_course=is_in_course,
                major=row["专业全称（必填）"],
                grade=row["年级（必填）"][:-1],
                div="div1",
            )
            if cached_vjudge_contestant:
                cached_vjudge_contestant.nickname = nickname
                cached_vjudge_contestant.commit_to_db
            else:
                vjudge_contestant.commit_to_db()


def read_questionnaire():
    df = pd.read_csv(acmana.config["input"]["questionnaire_path"])

    async def main():
        tasks = [read_nowcoder_questionnaire(df), read_vjudge_questionnaire(df)]
        await asyncio.gather(*tasks)

    asyncio.run(main())


if __name__ == "__main__":
    read_questionnaire()
