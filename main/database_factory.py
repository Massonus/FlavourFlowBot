import sqlalchemy
import psycopg2
import pandas as pd
from sqlalchemy import exc
from config import postgres_username, postgres_password
from passlib.hash import bcrypt

engine = sqlalchemy.create_engine(f"postgresql+psycopg2://{postgres_username}:{postgres_password}@localhost:5432/Test")


class Database():
    def __init__(self):
        self.conn = psycopg2.connect(database='Test', user='postgres',
                                     password='root', host='localhost', port=5432)
        self.cursor = self.conn.cursor()

    def data_list_for_page(self, tables, order, schema='public', page=1, skip_size=1, wheres=''):
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


def get_authorization_users():
    data = pd.read_sql('consumer', engine)
    user_id = []
    try:
        user_id = data['telegram_id'].values.tolist()
    except KeyError:
        data['telegram_id'] = [0] * len(data)
        data.to_sql('consumer', engine, if_exists='replace', index=False, index_label='id')
    return user_id


def get_pending_users():
    try:
        data = pd.read_sql('pending_users', engine)
    except exc.ProgrammingError:
        data = pd.DataFrame(columns=['user_id'])
        data.to_sql('pending_users', engine, if_exists='append', index=False, index_label='id')
    user_id = data['user_id'].values.tolist()
    return user_id


def get_user_by_username(username):
    data = pd.read_sql('consumer', engine)
    dict_username = data[data['username'] == username].to_dict().get('username')
    if dict_username == {}:
        return "empty"
    for val in dict_username.values():
        return val


def get_user_password(username):
    data = pd.read_sql('consumer', engine)
    dict_username = data[data['username'] == username].to_dict().get('password')
    for val in dict_username.values():
        return val


def compare_passwords(password, username):
    return bcrypt.verify(password, get_user_password(username))


def add_pending_user(user_id):
    df1 = pd.DataFrame([{'user_id': user_id}])
    df1.to_sql('pending_users', engine, if_exists='append', index=False, index_label='id')


def delete_pending_user(user_id):
    data = pd.read_sql('pending_users', engine)
    index = data[data['user_id'] == user_id].index
    data = data.drop(index)
    data.to_sql('pending_users', engine, if_exists='replace', index=False, index_label='id')
