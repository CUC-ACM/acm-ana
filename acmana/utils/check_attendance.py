import logging

import pandas as pd

import acmana
from acmana.models.student import Student

logger = logging.getLogger(__name__)


def check_attendance() -> list[str]:
    """检查是否有已经选课的同学没有填写问卷，返回没有填写同学的姓名列表"""
    not_fill_questionnaire: list[str] = []
    df = pd.read_csv(acmana.config["input"]["attendance_path"])
    for index, row in df.iterrows():
        student_id = row["学号"]
        db_student = Student.query_from_student_id(student_id)
        if db_student is None:
            logger.warning(f"已选课未填写问卷: {row['姓名']}")
            not_fill_questionnaire.append(row["姓名"])
    return not_fill_questionnaire


if __name__ == "__main__":
    check_attendance()
