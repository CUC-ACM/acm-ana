import asyncio
import logging

import aiohttp
import pandas as pd
from fake_useragent import UserAgent
from sqlalchemy import select

import scoreanalysis.config as config
from scoreanalysis.config import sqlsession
from contest import ContestBase
from contest.nowcoder_contest import NowcoderContest
from contest.vjudge_contest import VjudgeContest
from contestant import ContestantBase
from contestant.nowcoder_contestant import NowcoderContestant
from contestant.vjudge_contestant import VjudgeContestant
from ranking import RankingBase
from ranking.nowcoder_ranking import NowcoderRanking
from ranking.vjudge_ranking import VjudgeRanking
from scoreanalysis.models.sql_base import SQLBase
from scoreanalysis.crawler.nowcoder.nowcoder_nickname_crawler import get_nowcoder_nickname
from scoreanalysis.crawler.vjudge.vjudge_nickname_crawler import get_vjudge_nickname

logger = logging.getLogger(__name__)

ua = UserAgent()
SQLBase.metadata.create_all(config.engine)

df = pd.read_csv(config.config["input"]["questionnaire_path"])
# print(df.head())


async def read_nowcoder_questionnaire():
    async with aiohttp.ClientSession() as aiosession:
        for index, row in df.iterrows():
            student_id = row["学号（必填）"]
            stmt = select(NowcoderContestant).where(
                NowcoderContestant.student_id == student_id
            )
            cached_nowcoder_contestant = sqlsession.execute(stmt).scalar_one_or_none()

            if (
                cached_nowcoder_contestant
                and config.config["input"]["using_nickname_cache"]
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
            if cached_nowcoder_contestant:  # update
                cached_nowcoder_contestant.nickname = nickname
                sqlsession.add(cached_nowcoder_contestant)
            else:
                sqlsession.add(nowcoder_contestant)
            sqlsession.commit()


async def read_vjudge_questionnaire():
    async with aiohttp.ClientSession() as aiosession:
        for index, row in df.iterrows():
            student_id = row["学号（必填）"]
            stmt = select(VjudgeContestant).where(
                VjudgeContestant.student_id == student_id
            )
            cached_vjudge_contestant = sqlsession.execute(stmt).scalar_one_or_none()

            if (
                cached_vjudge_contestant
                and config.config["input"]["using_nickname_cache"]
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

            vjudge_url = row["Vjudge 个人主页网址（必填）"]
            nickname = await get_vjudge_nickname(vjudge_url, aiosession)
            if nickname == None:
                logger.warning(f"Vjudge网昵称获取失败: {row['姓名（必填）']}: {vjudge_url}")
            else:
                logger.debug(
                    f"Vjudge网昵称获取成功: {row['姓名（必填）']}: {vjudge_url}: {nickname}"
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
                sqlsession.add(cached_vjudge_contestant)
            else:
                sqlsession.add(vjudge_contestant)
            sqlsession.commit()


async def main():
    tasks = [read_nowcoder_questionnaire(), read_vjudge_questionnaire()]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
