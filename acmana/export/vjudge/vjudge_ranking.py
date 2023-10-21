import pandas as pd

from acmana.models.contest.vjudge_contest import VjudgeContest


class Sheet:
    def __init__(self, contest_id: int, only_attendance: bool) -> None:
        self.vjudge_contest: VjudgeContest = VjudgeContest.query_from_id(contest_id)  # type: ignore
        assert self.vjudge_contest is not None
        self.sheet_name: str = self.vjudge_contest.title
        if only_attendance:
            self.sheet_name += "(选课同学)"
        else:
            self.sheet_name += "(所有同学)"
        self.df = pd.DataFrame()
        self.only_attendance: bool = only_attendance

        if only_attendance:  # 只计算选课的同学的排名（排除未选课的同学）
            rankings = filter(
                lambda x: x.account.student is not None and x.account.student.in_course,
                self.vjudge_contest.rankings,
            )
        else:  # 计算所有参加比赛的同学的排名
            rankings = self.vjudge_contest.rankings

        for ranking in rankings:
            crt_ranking_is_in_course: bool = bool(
                ranking.account.student and ranking.account.student.in_course
            )

            self.df = pd.concat(
                [
                    self.df,
                    pd.DataFrame(
                        {
                            "姓名": [
                                ranking.account.student.real_name
                                if ranking.account.student is not None
                                else ""
                            ],
                            "学号": [
                                ranking.account.student.id
                                if ranking.account.student is not None
                                else ""
                            ],
                            "Nickname": [ranking.account.nickname],
                            "Username": [ranking.account.username],
                            "Ranking": [
                                ranking.get_attendance_ranking()
                                if crt_ranking_is_in_course
                                else ranking.competition_rank
                            ],
                            "Score": [
                                ranking.get_score(
                                    only_among_attendance=self.only_attendance
                                )
                            ],
                            "Solved": [ranking.solved_cnt],
                            "Upsolved": [ranking.upsolved_cnt],
                            "Penalty": [str(ranking.penalty)],
                        }
                    ),
                ]
            )

    @staticmethod
    def _chinese_len(s: str) -> int:
        """计算中文字符的长度"""
        cnt = 0  # 长宽度中文字符数量
        for word in s:  # 检测长宽度中文字符
            if (word >= "\u4e00" and word <= "\u9fa5") or word in {
                "；",
                "：",
                "，",
                "（",
                "）",
                "！",
                "？",
                "——",
                "……",
                "、",
                "》",
                "《",
            }:
                cnt += 1
        return len(s) + cnt

    def to_excel(self, path: str):
        # with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
            workbook = writer.book
            self.df.to_excel(
                writer,
                startrow=1,
                sheet_name=self.sheet_name,
                index=False,
                header=False,
            )
            worksheet = writer.sheets[self.sheet_name]
            # Write the column headers with the defined format.
            header_format = workbook.add_format(  # type: ignore
                {
                    "bold": True,
                    "text_wrap": True,
                    "valign": "top",
                    "fg_color": "#D7E4BC",
                    "border": 1,
                }
            )
            for col_num, value in enumerate(self.df.columns.values):
                worksheet.write(1, col_num, value, header_format)

            for idx, col in enumerate(self.df):  # loop through all columns
                series = self.df[col]
                max_len = (
                    max(
                        (
                            int(
                                series.astype(str).map(self._chinese_len).max()
                            ),  # len of largest item
                            len(str(series.name)),  # len of column name/header
                        )
                    )
                    + 1
                )  # adding a little extra space
                worksheet.set_column(idx, idx, max_len)  # set column width
            merge_format = workbook.add_format(  # type: ignore
                {
                    "bold": 1,
                    "border": 1,
                    "align": "center",
                    "valign": "vcenter",
                    "fg_color": "yellow",
                }
            )
            worksheet.merge_range("A1:I1", self.sheet_name, merge_format)


if __name__ == "__main__":
    Sheet(588777, only_attendance=True).to_excel("acmana/tmp/588777_attendance.xlsx")
    Sheet(588777, only_attendance=False).to_excel("acmana/tmp/588777_all.xlsx")
