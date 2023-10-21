import logging

import pandas as pd

import acmana
from acmana.models.student import Student

logger = logging.getLogger(__name__)


def check_attendance() -> list[str]:
    """检查是否有已经选课的同学没有填写问卷，返回没有填写同学的姓名列表"""
    not_fill_questionnaire: list[str] = []
    df = pd.read_csv(acmana.config["input"]["attendance_path"])

    for index, row in df.iterrows():  # 遍历 attendance.csv
        student_id = row["学号"]
        db_student = Student.query_from_student_id(student_id)
        if db_student is None:
            logger.warning(f"已选课未填写问卷: {row['姓名']}")
            not_fill_questionnaire.append(row["姓名"])

    accurate_attendance_ids = set(df["学号"])
    for db_student in Student.query_all():
        if db_student.in_course:  # 调查问卷中填写自己已选课
            if not db_student.id in accurate_attendance_ids:
                logger.warning(f"学生：{db_student} 填写问卷称自己已选课，但是没有在 attendance.csv 中")
        else: # 调查问卷中填写自己未选课
            if db_student.id in accurate_attendance_ids:
                logger.warning(f"学生：{db_student} 填写问卷称自己未选课，但是在 attendance.csv 中")

    return not_fill_questionnaire


if __name__ == "__main__":
    check_attendance()
