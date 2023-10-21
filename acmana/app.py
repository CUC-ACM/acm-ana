import logging

import acmana
from acmana.crawler.vjudge.contest import VjudgeContestCrawler
from acmana.crawler.vjudge.title_retriver import VjudgeContestRetriever

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


def run():
    retrive_vjudge_contests()


if __name__ == "__main__":
    run()
