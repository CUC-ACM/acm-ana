import pandas as pd
from sqlalchemy.orm import Session

import config

from contest.nowcoder_contest import NowcoderContest
from contest.vjudge_contest import VjudgeContest
from contestant.nowcoder_contestant import NowcoderContestant
from contestant.vjudge_contestant import VjudgeContestant
from ranking.nowcoder_ranking import NowcoderRanking
from ranking.vjudge_ranking import VjudgeRanking

from contest import ContestBase
from contestant import ContestantBase
from ranking import RankingBase

from sql_base import SQLBase

SQLBase.metadata.create_all(config.engine)

df = pd.read_csv(config.config["input"]["questionnaire_path"])
# print(df.head())


def read_nowcoder_questionnaire():
    with Session(config.engine) as session:
        for index, row in df.iterrows():
            is_incourse = False
            nowcoder_contestant = NowcoderContestant(
                real_name=row["姓名（必填）"],
                student_id=row["学号（必填）"],
                nickname=None,
                username=row["牛客个人主页网址（必填）"].split("/")[-1],
                is_in_course=True,
                major=row["专业全称（必填）"],
                grade=row["年级（必填）"][:-1],
                div="div2",
            )
            # print(row["姓名（必填）"])

            session.add(nowcoder_contestant)
        session.commit()


def read_vjudge_questionnaire():
    with Session(config.engine) as session:
        for index, row in df.iterrows():
            is_incourse = False
            vjudge_contestant = VjudgeContestant(
                real_name=row["姓名（必填）"],
                student_id=row["学号（必填）"],
                nickname=None,
                username=row["Vjudge 个人主页网址（必填）"].split("/")[-1],
                is_in_course=True,
                major=row["专业全称（必填）"],
                grade=row["年级（必填）"][:-1],
                div="div1",
            )
            # print(row["姓名（必填）"])

            session.add(vjudge_contestant)
        session.commit()


if __name__ == "__main__":
    read_nowcoder_questionnaire()
    read_vjudge_questionnaire()
