import logging
import os

import acmana
from acmana.crawler.vjudge.contest import VjudgeContestCrawler
from acmana.crawler.vjudge.title_retriver import VjudgeContestRetriever
from acmana.export.vjudge.vjudge_ranking import ExcelBook
from acmana.models.contest.vjudge_contest import VjudgeContest

logger = logging.getLogger(__name__)


def retrive_vjudge_contests():
    for div, instance in dict(acmana.config["vjudge"]["instances"]).items():
        logger.info(f"Retriving {div} contests from '{instance['title_prefix']}'......")
        retriever = VjudgeContestRetriever(title=instance["title_prefix"], div=div)
        retriever.get_contests_and_commit_to_db()
        for contest in retriever.retrieved_contests:
            logger.info(f"Retriving {contest} rank......")
            vjudge_contest_crawler = VjudgeContestCrawler(contest.id, div=div)
            vjudge_contest_crawler.db_vjudge_contest.commit_to_db()


def export_vjudge_contests_to_excel():
    """将 `数据库` 中的 VjudgeContest 导出到 Excel 文件中"""
    for div, instance in dict(acmana.config["vjudge"]["instances"]).items():
        logger.info(f"Exporting {div} contests from '{instance['title_prefix']}'......")
        total_excel_file_path: str = os.path.join(
            "outputs", instance["export_filename"] + "(全部同学).xlsx"
        )
        total_excel_book = ExcelBook(
            path=total_excel_file_path,
            div=div,
            only_attendance=False,
            sheet_name_remover=instance["sheet_name_remover"],
        )
        total_excel_book.write_book()

        attendance_excel_file_path: str = os.path.join(
            "outputs", instance["export_filename"] + "(选课同学).xlsx"
        )
        attendance_excel_book = ExcelBook(
            path=attendance_excel_file_path,
            div=div,
            only_attendance=True,
            sheet_name_remover=instance["sheet_name_remover"],
        )
        attendance_excel_book.write_book()


def run():
    retrive_vjudge_contests()
    export_vjudge_contests_to_excel()


if __name__ == "__main__":
    run()
