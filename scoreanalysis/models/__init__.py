from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

engine = create_engine("sqlite:///scoreanalysis/resources/sqlite_data.db", echo=False)
SessionMaker = sessionmaker(bind=engine)
sqlsession = SessionMaker()


class SQLBase(DeclarativeBase):
    pass


SQLBase.metadata.create_all

#  初始化 orm
from scoreanalysis.models.contest.nowcoder_contest import NowcoderContest
from scoreanalysis.models.contest.vjudge_contest import VjudgeContest
from scoreanalysis.models.contestant.nowcoder_contestant import NowcoderContestant
from scoreanalysis.models.contestant.vjudge_contestant import VjudgeContestant
from scoreanalysis.models.ranking.nowcoder_ranking import NowcoderRanking
from scoreanalysis.models.ranking.vjudge_ranking import VjudgeRanking