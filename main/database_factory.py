import sqlalchemy
import psycopg2
import pandas as pd
from sqlalchemy import exc
from config import postgres_username, postgres_password

engine = sqlalchemy.create_engine(f"postgresql+psycopg2://{postgres_username}:{postgres_password}@localhost:5432/Test")


class Database():
    def __init__(self):
        self.conn = psycopg2.connect(database='Test', user='postgres',
                                     password='root', host='localhost', port=5432)
        self.cursor = self.conn.cursor()

    def data_list_for_page(self, tables, order, schema='public', page=1, skip_size=1, wheres='WHERE company_id = 5'):
        skips_page = ((page - 1) * skip_size)
        sql = f"""SELECT * FROM {schema}.{tables} AS o
        {wheres}
        ORDER BY o.{order}
        OFFSET {skips_page} ROWS FETCH NEXT {skip_size} ROWS ONLY;"""
        self.cursor.execute(sql)
        res = self.cursor.fetchall()
        self.cursor.execute(f"""SELECT Count(*) FROM {schema}.{tables} AS o {wheres};""")
        count = self.cursor.fetchone()[0]
        return res[0], count


def get_pending_users():
    try:
        data = pd.read_sql('pending_users', engine)
    except exc.ProgrammingError:
        data = pd.DataFrame(columns=['user_id'])
        data.to_sql('pending_users', engine, if_exists='append', index=False, index_label='id')
    user_id = data['user_id'].values.tolist()
    return user_id


def add_pending_user(user_id):
    df1 = pd.DataFrame([{'user_id': user_id}])
    df1.to_sql('pending_users', engine, if_exists='append', index=False, index_label='id')


def delete_pending_user(user_id):
    data = pd.read_sql('pending_users', engine)
    index = data[data['user_id'] == user_id].index
    data = data.drop(index)
    data.to_sql('pending_users', engine, if_exists='replace', index=False, index_label='id')
