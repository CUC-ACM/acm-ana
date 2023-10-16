import pandas as pd


def read_course_registration_excel(
    excel_path: str, student_id_file_path: str
) -> list[tuple[str, str, int, str]]:
    """读取课程点名表，返回学生信息列表

    :param excel_path: 课程点名表的路径（excel）
    :param student_id_file_path: 学号文件的路径（纯文本文件）

    :return: 学生信息列表，每个元素为一个元组，元组的四个元素分别为：
        (学号, 姓名, 年级, 专业)"""
    excel_data_df = pd.read_excel(
        excel_path,
        index_col=0,
    )

    names = excel_data_df["Unnamed: 2"].tolist()[6:-2]
    year_majors = excel_data_df["Unnamed: 4"].tolist()[6:-2]
    student_id_list: list[str] = []
    year_list: list[int] = []
    major_list: list[str] = []

    for year_major in year_majors:
        year = int(year_major[:4])
        major = year_major[4:]
        year_list.append(year)
        major_list.append(major)

    with open(student_id_file_path, "r") as f:
        for line in f:
            if line.strip() == "":
                continue
            student_id = line.strip()
            student_id_list.append(student_id)
    assert len(student_id_list) == len(names) == len(year_list) == len(major_list)
    return list(zip(student_id_list, names, year_list, major_list))


if __name__ == "__main__":
    students = read_course_registration_excel(
        "./data/input/students/attendance.xlsx", "./data/input/students/student_id.txt"
    )
    for student in students:
        print(student)
    print(f"总人数：{len(students)}")
