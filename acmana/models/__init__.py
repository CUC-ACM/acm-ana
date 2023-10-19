from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

engine = create_engine("sqlite:///acmana/resources/sqlite_data.db", echo=False)
SessionMaker = sessionmaker(bind=engine)
sqlsession = SessionMaker()


class SQLBase(DeclarativeBase):
    pass


#  初始化 orm
from acmana.models.contest.nowcoder_contest import NowcoderContest
from acmana.models.contest.vjudge_contest import VjudgeContest
from acmana.models.account.nowcoder_account import NowcoderAccount
from acmana.models.account.vjudge_account import VjudgeAccount
from acmana.models.ranking.nowcoder_ranking import NowcoderRanking
from acmana.models.ranking.vjudge_ranking import VjudgeRanking
from acmana.models.student import Student

SQLBase.metadata.create_all(engine)
