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
from acmana.models.contestant.nowcoder_contestant import NowcoderContestant
from acmana.models.contestant.vjudge_contestant import VjudgeContestant
from acmana.models.ranking.nowcoder_ranking import NowcoderRanking
from acmana.models.ranking.vjudge_ranking import VjudgeRanking

SQLBase.metadata.create_all(engine)
