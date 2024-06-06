import sqlalchemy
import pandas as pd
from sqlalchemy import exc
from config import postgres_username, postgres_password

engine = sqlalchemy.create_engine(f"postgresql+psycopg2://{postgres_username}:{postgres_password}@localhost:5432/Test")


def get_pending_users():
    try:
        data = pd.read_sql('pending_users', engine)
    except exc.ProgrammingError as e:
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
