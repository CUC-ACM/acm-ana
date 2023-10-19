from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

engine = create_engine("sqlite:///acmana/resources/sqlite_data.db", echo=False)
SessionMaker = sessionmaker(bind=engine)
sqlsession = SessionMaker()


class SQLBase(DeclarativeBase):
    pass


import acmana.models.account.nowcoder_account
import acmana.models.account.vjudge_account
import acmana.models.contest.nowcoder_contest
import acmana.models.contest.vjudge_contest
import acmana.models.ranking.nowcoder_ranking
import acmana.models.ranking.vjudge_ranking
import acmana.models.student

SQLBase.metadata.create_all(engine)
