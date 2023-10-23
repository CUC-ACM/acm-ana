import datetime
import json
import logging
import os

import requests

import acmana
from acmana.crawler.vjudge.contest import VjudgeContestCrawler
from acmana.crawler.vjudge.title_retriver import VjudgeContestRetriever
from acmana.export.vjudge.vjudge_ranking import ExcelBook
from acmana.models.contest.vjudge_contest import VjudgeContest

logger = logging.getLogger(__name__)


def retrive_vjudge_contests():
    for div, instance in dict(acmana.config["vjudge"]["instances"]).items():
        logger.info(
            f"Retriving {div} contests from title_prefix '{instance['title_prefix']}'......"
        )
        retriever = VjudgeContestRetriever(
            title_prefix=instance["title_prefix"], div=div
        )
        retriever.get_contests_and_commit_to_db()
        for contest in retriever.retrieved_contests:
            logger.info(f"Retriving {contest} rank......")
            if contest.end > datetime.datetime.now(tz=datetime.timezone.utc):
                logger.warning(f"Contest {contest} has not ended yet, skip......")
                continue

            try:
                vjudge_contest_crawler = VjudgeContestCrawler(contest.id, div=div)
            except requests.exceptions.JSONDecodeError:
                logger.critical(f"JSONDecodeError: {contest}。这场比赛可能设置有密码，跳过......")
                continue
            except json.decoder.JSONDecodeError:
                logger.critical(
                    f"JSONDecodeError: {contest}。在之前缓存这场比赛的 api json 时，这场比赛设置有密码。"
                    f"请检查现在是否还设有密码并 unset 环境变量 `DEBUG_CACHE`"
                )
            else:
                vjudge_contest_crawler.db_vjudge_contest.commit_to_db()


def export_vjudge_contests_to_excel():
    """将 `数据库` 中的 VjudgeContest 导出到 Excel 文件中"""
    for div, instance in dict(acmana.config["vjudge"]["instances"]).items():
        logger.info(
            f"Exporting {div} contests from title_prefix '{instance['title_prefix']}'......"
        )
        total_excel_file_path: str = os.path.join(
            "outputs", instance["export_filename"] + "(全部同学).xlsx"
        )
        logger.warning(f"Exporting to {total_excel_file_path}")
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
        logger.warning(f"Exporting to {attendance_excel_file_path}")
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
    # run()
    from acmana.models.account.vjudge_account import VjudgeAccount

    print(VjudgeAccount.query_from_account_id(582048))
