import datetime
from typing import TYPE_CHECKING

from acmana.models.account.vjudge_account import VjudgeAccount

if TYPE_CHECKING:
    from acmana.crawler.vjudge.contest import VjudgeContestCrawler


class VjudgeSubmission:
    def __init__(
        self,
        problem_id: int,
        accepted: bool,
        time: datetime.timedelta,
        account: VjudgeAccount,
        contest: "VjudgeContestCrawler",
    ) -> None:
        self.problem_id = problem_id
        self.accepted: bool = accepted
        self.time: datetime.timedelta = time
        self.account: VjudgeAccount = account
        self.contest: VjudgeContestCrawler = contest

    @classmethod
    def from_api_list(
        cls,
        l: list,
        participants_dict: dict[int, VjudgeAccount],
        contest: "VjudgeContestCrawler",
    ) -> "VjudgeSubmission":
        return cls(
            problem_id=int(l[1]),
            accepted=bool(l[2]),
            time=datetime.timedelta(seconds=int(l[3])),
            account=participants_dict[int(l[0])],
            contest=contest,
        )

    def __repr__(self) -> str:
        return f"account: {self.account} promble_id: {self.problem_id}, accepted: {self.accepted}, time: {self.time}"
