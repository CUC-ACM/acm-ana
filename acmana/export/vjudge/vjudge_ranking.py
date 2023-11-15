import datetime

import pandas as pd
import pytz
from xlsxwriter import Workbook

import acmana
from acmana.models.account.vjudge_account import VjudgeAccount
from acmana.models.contest.vjudge_contest import VjudgeContest
from acmana.models.ranking.vjudge_ranking import VjudgeRanking


class VjudgeExcelBook:
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
        ] = VjudgeContest.query_finished_contests(div=div)

        self.finished_vjudge_contests.sort(key=lambda x: x.end)
        self.sheets: list["Sheet"] = []

    def write_book(self):
        self.summary_sheet: SummarySheet = SummarySheet(self)
        self.sheets.append(self.summary_sheet)
        for vjudge_contest in self.finished_vjudge_contests:
            self.sheets.append(Sheet(self, vjudge_contest))

        for sheet in self.sheets:
            if acmana.config["common"]["upsolve"]["sort_by_score"]:
                sheet.df.sort_values(by=["Score"], ascending=False, inplace=True)
            sheet.write_sheet()
        self.writer.close()


class Sheet:
    def __init__(
        self, excel_book: "VjudgeExcelBook", vjudge_contest: VjudgeContest
    ) -> None:
        self.excel_book: VjudgeExcelBook = excel_book
        self.vjudge_contest: VjudgeContest = vjudge_contest
        assert self.vjudge_contest is not None
        self.sheet_title: str = self.vjudge_contest.title
        self.deadline: datetime.datetime = self.vjudge_contest.end + datetime.timedelta(
            days=acmana.config["common"]["upsolve"]["expiration"]
        )
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

        if datetime.datetime.now(datetime.timezone.utc) < self.deadline:
            beijing_tz = pytz.timezone("Asia/Shanghai")
            self.ddl_info = (
                f"(Upsolved 更新至 "
                + f"{datetime.datetime.now(datetime.timezone.utc).astimezone(beijing_tz).strftime('%m-%d %H:%M')}"
                + "；截止日期 "
                + f"{self.deadline.astimezone(beijing_tz).strftime('%m-%d %H:%M')})"
            )

            # self.sheet_title = self.sheet_title + self.ddl_info
        if self.excel_book.only_attendance:  # 只计算选课的同学的排名（排除未选课的同学）
            rankings = self.vjudge_contest.get_only_attendance_rankings()
        else:  # 计算所有参加比赛的同学的排名
            rankings = self.vjudge_contest.get_all_rankings()

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
                                if self.excel_book.only_attendance
                                and crt_ranking_is_in_course
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
                            "选课": [crt_ranking_is_in_course],
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
        start_row = 2  # start writing at this row number(0-indexed)
        if getattr(self, "ddl_info", None):
            start_row += 1

        self.df.to_excel(
            self.excel_book.writer,
            startrow=start_row,
            sheet_name=self.sheet_name,
            index=False,
            header=False,
        )

        worksheet = self.excel_book.writer.sheets[self.sheet_name]

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
        col_num = len(self.df.columns)
        worksheet.merge_range(
            f"A1:{chr(64 + col_num)}1", self.sheet_title, title_format
        )

        if getattr(self, "ddl_info", None):
            ddl_format = self.excel_book.workbook.add_format(  # type: ignore
                {
                    "bold": 0,
                    "border": 0,
                    "align": "center",
                    "valign": "vcenter",
                    "fg_color": "#CCFFFF",
                }
            )
            worksheet.merge_range(f"A2:{chr(64 + col_num)}2", self.ddl_info, ddl_format)

        # Write the column headers with the defined format.
        header_format = self.excel_book.workbook.add_format(  # type: ignore
            {
                "bold": True,
                "text_wrap": True,
                "align": "center",
                "valign": "vcenter",
                "fg_color": "#D7E4BC",
                "border": 1,
            }
        )
        for col_num, value in enumerate(self.df.columns.values):
            worksheet.write(start_row - 1, col_num, value, header_format)

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


class SummarySheet(Sheet):
    def __init__(self, excel_book: "VjudgeExcelBook") -> None:
        self.excel_book: VjudgeExcelBook = excel_book
        self.sheet_name: str = "Summary"
        self.sheet_title: str = self.sheet_name
        self.df = pd.DataFrame()
        if self.excel_book.only_attendance:
            self.vjudge_accounts: list[
                VjudgeAccount
            ] = VjudgeAccount.query_all_attendance()
        else:
            self.vjudge_accounts: list[
                VjudgeAccount
            ] = VjudgeAccount.query_all_append_unregistered()

        if excel_book.only_attendance:
            self.sheet_title += "(选课同学)"
        else:
            self.sheet_title += "(所有同学)"
        self.df = pd.DataFrame()
        for vjudge_account in self.vjudge_accounts:
            if self.excel_book.div:
                vjudge_account.rankings = list(
                    filter(
                        lambda x: x.contest.div == self.excel_book.div,
                        vjudge_account.rankings,
                    )
                )
            if self.excel_book.only_attendance:
                vjudge_account.rankings = list(
                    filter(
                        lambda x: x.account.student is not None
                        and x.account.student.in_course,
                        vjudge_account.rankings,
                    )
                )
            self.df = pd.concat(
                [
                    self.df,
                    pd.DataFrame(
                        {
                            "姓名": [
                                vjudge_account.student.real_name
                                if vjudge_account.student is not None
                                else ""
                            ],
                            "学号": [
                                vjudge_account.student.id
                                if vjudge_account.student is not None
                                else ""
                            ],
                            "Nickname": [vjudge_account.nickname],
                            "Username": [vjudge_account.username],
                            "Score": [
                                sum(
                                    map(
                                        lambda x: x.get_score(
                                            only_among_attendance=self.excel_book.only_attendance
                                        ),
                                        vjudge_account.rankings,
                                    )
                                )
                            ],
                            "Solved": [
                                sum(
                                    map(
                                        lambda x: x.solved_cnt,
                                        vjudge_account.rankings,
                                    )
                                )
                            ],
                            "Upsolved": [
                                sum(
                                    map(
                                        lambda x: x.upsolved_cnt,
                                        vjudge_account.rankings,
                                    )
                                )
                            ],
                            "Penalty": [
                                sum(
                                    map(  # type: ignore
                                        lambda x: x.penalty.total_seconds(),
                                        vjudge_account.rankings,
                                    )
                                )
                            ],
                            "选课": [
                                vjudge_account.student.in_course
                                if vjudge_account.student
                                else ""
                            ],
                        }
                    ),
                ]
            )


if __name__ == "__main__":
    excel_book = VjudgeExcelBook(
        path="acmana/tmp/vjudge_div1(选课同学).xlsx",
        div="div1",
        only_attendance=True,
        sheet_name_remover="CUC-ACM-2023秋季学期",
    )
    excel_book.write_book()
    excel_book = VjudgeExcelBook(
        path="acmana/tmp/vjudge_div1(全部同学).xlsx",
        div="div1",
        only_attendance=True,
        sheet_name_remover="CUC-ACM-2023秋季学期",
    )
    excel_book.write_book()
