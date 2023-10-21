import pandas as pd
from xlsxwriter import Workbook

from acmana.models.contest.vjudge_contest import VjudgeContest


class ExcelBook:
    def __init__(
        self,
        path: str,
        div: str | None,
        only_attendance: bool,
        sheet_name_remover: str | None = None,
    ) -> None:
        """
        :param: sheet_name_remover: 用于 replace `sheet_name` 中的字符串
        """
        self.writer = pd.ExcelWriter(path, engine="xlsxwriter")
        self.workbook = self.writer.book
        self.div: str | None = div
        self.only_attendance: bool = only_attendance
        self.sheet_name_remover: str | None = sheet_name_remover
        self.finished_vjudge_contests: list[
            VjudgeContest
        ] = VjudgeContest.query_finished_contests()
        if div:
            self.finished_vjudge_contests = list(
                filter(lambda x: x.div == div, self.finished_vjudge_contests)
            )
        self.finished_vjudge_contests.sort(key=lambda x: x.begin)
        self.sheets: list["Sheet"] = []

    def write_book(self):
        for vjudge_contest in self.finished_vjudge_contests:
            self.sheets.append(Sheet(self, vjudge_contest))
            self.sheets[-1].write_sheet()
        self.writer.close()


class Sheet:
    def __init__(self, excel_book: "ExcelBook", vjudge_contest: VjudgeContest) -> None:
        self.excel_book: ExcelBook = excel_book
        self.vjudge_contest: VjudgeContest = vjudge_contest
        assert self.vjudge_contest is not None
        self.sheet_title: str = self.vjudge_contest.title
        self.sheet_name: str = self.vjudge_contest.title
        if self.excel_book.sheet_name_remover:
            self.sheet_name = self.sheet_name.replace(
                self.excel_book.sheet_name_remover, ""
            )
        if excel_book.only_attendance:
            self.sheet_title += "(选课同学)"
        else:
            self.sheet_title += "(所有同学)"
        self.df = pd.DataFrame()

        if self.excel_book.only_attendance:  # 只计算选课的同学的排名（排除未选课的同学）
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
                                    only_among_attendance=self.excel_book.only_attendance
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

    def write_sheet(self):
        # writer = pd.ExcelWriter()
        self.df.to_excel(
            self.excel_book.writer,
            startrow=1,
            sheet_name=self.sheet_name,
            index=False,
            header=False,
        )
        worksheet = self.excel_book.writer.sheets[self.sheet_name]
        # Write the column headers with the defined format.
        header_format = self.excel_book.workbook.add_format(  # type: ignore
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

        # Set the column width and format.
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

        # Add a title row.
        title_format = self.excel_book.workbook.add_format(  # type: ignore
            {
                "bold": 1,
                "border": 1,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "yellow",
            }
        )
        worksheet.merge_range("A1:I1", self.sheet_title, title_format)


if __name__ == "__main__":
    excel_book = ExcelBook(
        path="acmana/tmp/vjudge_div1(选课同学).xlsx",
        div="div1",
        only_attendance=True,
        sheet_name_remover="CUC-ACM-2023秋季学期",
    )
    excel_book.write_book()
    excel_book = ExcelBook(
        path="acmana/tmp/vjudge_div1(全部同学).xlsx",
        div="div1",
        only_attendance=True,
        sheet_name_remover="CUC-ACM-2023秋季学期",
    )
    excel_book.write_book()