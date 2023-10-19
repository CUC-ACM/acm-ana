import asyncio
import logging

import aiohttp
import pandas as pd

import acmana
from acmana.crawler.nowcoder.user_info import get_nowcoder_nickname
from acmana.crawler.vjudge.user_info import get_vjudge_nickname, get_vjudge_user_id
from acmana.models.account.nowcoder_account import NowcoderAccount
from acmana.models.account.vjudge_account import VjudgeAccount
from acmana.models.student import Student

logger = logging.getLogger(__name__)


class Questionnaire:
    def __init__(
        self,
        name: str,
        student_id: str,
        grade: str,
        major: str,
        in_course: bool,
        nowcoder_id: int,
        vjudge_username: str,
    ) -> None:
        self.name: str = name
        self.student_id: str = student_id
        self.grade: str = grade
        self.major: str = major
        self.in_course: bool = in_course
        self.nowcoder_id: int = nowcoder_id
        self.nowcoder_nickname: str | None
        self.cached_nowcoder_account: NowcoderAccount | None = None
        self.vjudge_username: str = vjudge_username
        self.vjudge_nickename: str | None
        self.vjudge_userid: int
        self.cache_vjudge_account: VjudgeAccount | None = None

    def update_student_db(self):
        student = Student.query_from_student_id(self.student_id)
        if student:
            student.real_name = self.name
            student.grade = self.grade
            student.major = self.major
            student.in_course = self.in_course
            student.commit_to_db()
        else:
            student = Student(
                id=self.student_id,
                real_name=self.name,
                grade=self.grade,
                major=self.major,
                in_course=self.in_course,
            )
            student.commit_to_db()

    def update_vjudge_db(self):
        if self.cache_vjudge_account:
            self.cache_vjudge_account.nickname = self.vjudge_nickename
            self.cache_vjudge_account.id = self.vjudge_userid
            self.cache_vjudge_account.commit_to_db()
        else:
            vjudge_account = VjudgeAccount(
                id=self.vjudge_userid,
                nickname=self.vjudge_nickename,
                username=self.vjudge_username,
                student_id=self.student_id,
            )
            vjudge_account.commit_to_db()

    def update_nowcoder_db(self):
        if self.cached_nowcoder_account:
            self.cached_nowcoder_account.nickname = self.nowcoder_nickname
            self.cached_nowcoder_account.commit_to_db()
        else:
            nowcoder_account = NowcoderAccount(
                id=self.nowcoder_id,
                nickname=self.nowcoder_nickname,
                student_id=self.student_id,
            )
            nowcoder_account.commit_to_db()


async def async_read_questionnaire_update_db(df: pd.DataFrame, concurrency: int = 3):
    tasks: list[asyncio.Task] = []

    async def update_questionnaire_nowcoder_nickname(
        questionnaire: Questionnaire,
        clientsession: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
    ):
        async with semaphore:
            questionnaire.nowcoder_nickname = await get_nowcoder_nickname(
                questionnaire.nowcoder_id, session=clientsession
            )
            logger.info(
                f"牛客网昵称获取成功: {questionnaire.name}: {questionnaire.nowcoder_nickname}"
            )
            questionnaire.update_nowcoder_db()

    async def update_questionnaire_vjudge_nickname(
        questionnaire: Questionnaire,
        clientsession: aiohttp.ClientSession,
        semaphore: asyncio.Semaphore,
    ):
        async with semaphore:
            questionnaire.vjudge_nickename = await get_vjudge_nickname(
                questionnaire.vjudge_username, session=clientsession
            )
            questionnaire.vjudge_userid = await get_vjudge_user_id(
                questionnaire.vjudge_username, session=clientsession
            )
            logger.info(
                f"Vjudge网昵称获取成功: {questionnaire.name}: {questionnaire.vjudge_nickename}"
            )
            questionnaire.update_vjudge_db()

    semaphore = asyncio.Semaphore(concurrency)
    async with aiohttp.ClientSession() as clientsession:
        for index, row in df.iterrows():
            crt_questionnaire = Questionnaire(
                name=row["姓名（必填）"],
                student_id=row["学号（必填）"],
                grade=row["年级（必填）"][:-1],
                major=row["专业全称（必填）"],
                in_course=True if row["是否在选课系统中选上课（必填）"] == "是" else False,
                nowcoder_id=int(str(row["牛客个人主页网址（必填）"]).split("/")[-1]),
                vjudge_username=str(row["Vjudge 个人主页网址（必填）"]).split("/")[-1],
            )

            crt_questionnaire.update_student_db()

            nowcoder_account = NowcoderAccount.query_from_student_id(
                crt_questionnaire.student_id
            )
            if nowcoder_account is not None:  # 已经有缓存了——>更新
                crt_questionnaire.nowcoder_nickname = (
                    nowcoder_account.nickname
                )  # 准备之后更新数据库
                crt_questionnaire.cached_nowcoder_account = nowcoder_account
            else:  # 没有缓存——>获取
                tasks.append(
                    asyncio.create_task(
                        update_questionnaire_nowcoder_nickname(
                            crt_questionnaire, clientsession, semaphore=semaphore
                        )
                    )
                )
            vjudge_account = VjudgeAccount.query_from_student_id(
                crt_questionnaire.student_id
            )
            if vjudge_account is not None:  # 已经有缓存了——>更新
                crt_questionnaire.vjudge_nickename = vjudge_account.nickname
                crt_questionnaire.vjudge_userid = vjudge_account.id
                crt_questionnaire.cache_vjudge_account = vjudge_account
            else:  # 没有缓存——>获取
                tasks.append(
                    asyncio.create_task(
                        update_questionnaire_vjudge_nickname(
                            crt_questionnaire, clientsession, semaphore=semaphore
                        )
                    )
                )

        await asyncio.gather(*tasks)  # 等待所有任务完成


def read_questionnaire_update_db():
    """读取问卷，更新数据库"""
    df = pd.read_csv(acmana.config["input"]["questionnaire_path"])

    async def main():
        await async_read_questionnaire_update_db(df)

    asyncio.run(main())


if __name__ == "__main__":
    read_questionnaire_update_db()
