import logging

import pandas as pd

import acmana
from acmana.models.account.nowcoder_account import NowcoderAccount

logger = logging.getLogger(__name__)


def check_attendance():
    """检查是否有已经选课的同学没有填写问卷"""

    df = pd.read_csv(acmana.config["input"]["attendance_path"])
    for index, row in df.iterrows():
        student_id = row["学号"]
        cached_nowcoder_contestant = NowcoderAccount.query_from_student_id(
            student_id=student_id
        )

        if not cached_nowcoder_contestant:
            logging.info(f"已选课未填表: {row['姓名']}")


if __name__ == "__main__":
    check_attendance()
