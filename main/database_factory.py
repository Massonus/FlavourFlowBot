from sqlalchemy import create_engine, Column, Integer, BigInteger, Double, ForeignKey, String, exc
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import psycopg2
import pandas as pd
import dropbox_factory as dropbox
import config
from passlib.hash import bcrypt
import new_db

engine = create_engine(
    f"postgresql+psycopg2://{config.postgres_username}:{config.postgres_test_password}@{config.postgres_test_host}:5432"
    f"/{config.postgres_test_database}")

# engine = sqlalchemy.create_engine(
#     f"postgresql+psycopg2://{config.postgres_username}:{config.postgres_password}@{config.postgres_host}:5432"
#     f"/{config.postgres_database}")

Session = sessionmaker(bind=engine)
Base = declarative_base()
session = Session()


class PsycopgDB:
    def __init__(self):
        # self.conn = psycopg2.connect(database=f'{config.postgres_database}', user=f'{config.postgres_username}',
        #                              password=f'{config.postgres_password}', host=f'{config.postgres_host}',
        #                              port=5432)

        self.conn = psycopg2.connect(database=f'{config.postgres_test_database}', user=f'{config.postgres_username}',
                                     password=f'{config.postgres_test_password}', host=f'{config.postgres_test_host}',
                                     port=5432)
        self.cursor = self.conn.cursor()
