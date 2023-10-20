import datetime
from typing import TYPE_CHECKING

from acmana.models.account.vjudge_account import VjudgeAccount

if TYPE_CHECKING:
    from acmana.crawler.vjudge.contest import VjContest


class VjSubmission:
    def __init__(
        self,
        vaccount_id: int,
        problem_id: int,
        accepted: bool,
        time: datetime.timedelta,
        account: VjudgeAccount,
        contest: "VjContest",
    ) -> None:
        self.vaccount_id: int = vaccount_id  # 注意，这里是 vjudge 自己的 vaccount_id
        self.problem_id = problem_id
        self.accepted: bool = accepted
        self.time: datetime.timedelta = time
        self.account: VjudgeAccount = account
        self.contest: VjContest = contest

    @classmethod
    def from_api_list(
        cls,
        l: list,
        participants_dict: dict[int, VjudgeAccount],
        contest: "VjContest",
    ) -> "VjSubmission":
        return cls(
            vaccount_id=int(l[0]),
            problem_id=int(l[1]),
            accepted=bool(l[2]),
            time=datetime.timedelta(seconds=int(l[3])),
            account=participants_dict[int(l[0])],
            contest=contest,
        )

    def __repr__(self) -> str:
        return f"vaccount_id: {self.vaccount_id}, account: {self.account} promble_id: {self.problem_id}, accepted: {self.accepted}, time: {self.time}"
