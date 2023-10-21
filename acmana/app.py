import logging

import acmana
from acmana.crawler.vjudge.contest import VjudgeContestCrawler
from acmana.crawler.vjudge.title_retriver import VjudgeContestRetriever
from acmana.export.vjudge.vjudge_ranking import ExcelBook
from acmana.models.contest.vjudge_contest import VjudgeContest

logger = logging.getLogger(__name__)


def retrive_vjudge_contests():
    for instance in acmana.config["vjudge"]["instances"]:
        logger.info(
            f"Retriving {instance['div']} contests from '{instance['title_prefix']}'......"
        )
        retriever = VjudgeContestRetriever(
            title=instance["title_prefix"], div=instance["div"]
        )
        retriever.get_contests_and_commit_to_db()
        for contest in retriever.retrieved_contests:
            logger.info(f"Retriving {contest} rank......")
            vjudge_contest_crawler = VjudgeContestCrawler(
                contest.id, div=instance["div"]
            )
            vjudge_contest_crawler.db_vjudge_contest.commit_to_db()


def export_vjudge_contests_to_excel():
    """将 `数据库` 中的 VjudgeContest 导出到 Excel 文件中"""
    excel_book = ExcelBook()
    excel_book.write_book()


def run():
    retrive_vjudge_contests()
    export_vjudge_contests_to_excel()


if __name__ == "__main__":
    run()
