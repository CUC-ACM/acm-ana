import datetime
import pandas as pd
import pytz
from xlsxwriter import Workbook

import acmana
from acmana.models.account.nowcoder_account import NowcoderAccount
from acmana.models.contest.nowcoder_contest import NowcoderContest
from acmana.models.ranking.nowcoder_ranking import NowcoderRanking


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
        self.finished_nowcoder_contests: list[
            NowcoderContest
        ] = NowcoderContest.query_finished_contests()
        if div:
            self.finished_nowcoder_contests = list(
                filter(lambda x: x.div == div, self.finished_nowcoder_contests)
            )
        self.finished_nowcoder_contests.sort(key=lambda x: x.begin)
        self.sheets: list["Sheet"] = []

    def write_book(self):
        self.summary_sheet: SummarySheet = SummarySheet(self)
        self.sheets.append(self.summary_sheet)
        for nowcoder_contest in self.finished_nowcoder_contests:
            self.sheets.append(Sheet(self, nowcoder_contest))

        for sheet in self.sheets:
            sheet.write_sheet()
        self.writer.close()


class Sheet:
    def __init__(self, excel_book: "ExcelBook", nowcoder_contest: NowcoderContest) -> None:
        self.excel_book: ExcelBook = excel_book
        self.nowcoder_contest: NowcoderContest = nowcoder_contest
        assert self.nowcoder_contest is not None
        self.sheet_title: str = self.nowcoder_contest.title
        self.deadline: datetime.datetime = self.nowcoder_contest.end + datetime.timedelta(
            days=acmana.config["upsolve"]["expiration"]
        )
        self.sheet_name: str = self.nowcoder_contest.title
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
            rankings = self.nowcoder_contest.get_only_attendance_rankings()
        else:  # 计算所有参加比赛的同学的排名
            rankings = self.nowcoder_contest.get_rankings_append_unregistered()

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
    def __init__(self, excel_book: "ExcelBook") -> None:
        self.excel_book: ExcelBook = excel_book
        self.sheet_name: str = "Summary"
        self.sheet_title: str = self.sheet_name
        self.df = pd.DataFrame()
        if self.excel_book.only_attendance:
            self.nowcoder_accounts: list[
                NowcoderAccount
            ] = NowcoderAccount.query_all_attendance()
        else:
            self.nowcoder_accounts: list[
                NowcoderAccount
            ] = NowcoderAccount.query_all_append_unregistered()

        if excel_book.only_attendance:
            self.sheet_title += "(选课同学)"
        else:
            self.sheet_title += "(所有同学)"
        self.df = pd.DataFrame()
        for nowcoder_account in self.nowcoder_accounts:
            if self.excel_book.div:
                nowcoder_account.rankings = list(
                    filter(
                        lambda x: x.contest.div == self.excel_book.div,
                        nowcoder_account.rankings,
                    )
                )
            if self.excel_book.only_attendance:
                nowcoder_account.rankings = list(
                    filter(
                        lambda x: x.account.student is not None
                        and x.account.student.in_course,
                        nowcoder_account.rankings,
                    )
                )
            self.df = pd.concat(
                [
                    self.df,
                    pd.DataFrame(
                        {
                            "姓名": [
                                nowcoder_account.student.real_name
                                if nowcoder_account.student is not None
                                else ""
                            ],
                            "学号": [
                                nowcoder_account.student.id
                                if nowcoder_account.student is not None
                                else ""
                            ],
                            "Nickname": [nowcoder_account.nickname],
                            "Score": [
                                sum(
                                    map(
                                        lambda x: x.get_score(
                                            only_among_attendance=self.excel_book.only_attendance
                                        ),
                                        nowcoder_account.rankings,
                                    )
                                )
                            ],
                            "Solved": [
                                sum(
                                    map(
                                        lambda x: x.solved_cnt,
                                        nowcoder_account.rankings,
                                    )
                                )
                            ],
                            "Upsolved": [
                                sum(
                                    map(
                                        lambda x: x.upsolved_cnt,
                                        nowcoder_account.rankings,
                                    )
                                )
                            ],
                            "Penalty": [
                                sum(
                                    map(  # type: ignore
                                        lambda x: x.penalty.total_seconds(),
                                        nowcoder_account.rankings,
                                    )
                                )
                            ],
                            "选课": [
                                nowcoder_account.student.in_course
                                if nowcoder_account.student
                                else ""
                            ],
                        }
                    ),
                ]
            )


if __name__ == "__main__":
    excel_book = ExcelBook(
        path="acmana/tmp/nowcoder_div2(选课同学).xlsx",
        div="div2",
        only_attendance=True,
        sheet_name_remover="CUC-ACM-2023秋季学期",
    )
    excel_book.write_book()
    excel_book = ExcelBook(
        path="acmana/tmp/nowcoder_div2(全部同学).xlsx",
        div="div2",
        only_attendance=True,
        sheet_name_remover="CUC-ACM-2023秋季学期",
    )
    excel_book.write_book()
