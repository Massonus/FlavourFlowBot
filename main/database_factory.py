import sqlalchemy
import psycopg2
import pandas as pd
import dropbox_factory as dropbox
from sqlalchemy import exc
from config import postgres_username, postgres_password
from passlib.hash import bcrypt

engine = sqlalchemy.create_engine(f"postgresql+psycopg2://{postgres_username}:{postgres_password}@localhost:5432/Test")


class PaginationData():
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


def is_authorized(telegram_id):
    return telegram_id in get_authorization_users()


def is_admin(telegram_id):
    data_consumer = pd.read_sql('consumer', engine)
    data_user_role = pd.read_sql('user_role', engine)
    try:
        user_id = data_consumer.loc[data_consumer['telegram_id'] == telegram_id, 'id'].values[0]
        admins_id = data_user_role.loc[data_user_role['roles'] == "ADMIN", 'user_id'].values.tolist()
    except IndexError:
        return False
    return user_id in admins_id


def get_authorization_users():
    data = pd.read_sql('consumer', engine)
    users = []
    try:
        users = data['telegram_id'].values.tolist()
    except KeyError:
        data['telegram_id'] = [0] * len(data)
        data.to_sql('consumer', engine, if_exists='replace', index=False, index_label='id')
    return users


def get_categories():
    df = pd.read_sql('kitchen_categories', engine)
    return pd.Series(df.title.values, index=df.id).to_dict()


def get_countries():
    df = pd.read_sql('company_country', engine)
    return pd.Series(df.title.values, index=df.id).to_dict()


def get_pending_users():
    try:
        data = pd.read_sql('pending_users', engine)
    except exc.ProgrammingError:
        data = pd.DataFrame(columns=['user_id'])
        data.to_sql('pending_users', engine, if_exists='append', index=False, index_label='id')
    pending_users = data['user_id'].values.tolist()
    return pending_users


def get_consumers_usernames():
    data = pd.read_sql('consumer', engine)
    return data['username'].values.tolist()


def get_consumers_emails():
    data = pd.read_sql('consumer', engine)
    return data['email'].values.tolist()


def is_user_exist(username):
    data = pd.read_sql('consumer', engine)
    try:
        return username == data.loc[data['username'] == username, 'username'].values[0]
    except IndexError:
        return False


def delete_product(message, bot, product_id):
    data = pd.read_sql('product', engine)
    image_link = data.loc[data['id'] == product_id, 'image_link'].values[0]

    db = PaginationData()
    sql = f"DELETE FROM product WHERE id = {product_id}"
    db.cursor.execute(sql)
    db.conn.commit()
    if "dropbox" in image_link:
        values = {'type': 'product', 'id': str(product_id)}
        dropbox.delete_file(message, bot, values)


def delete_company(message, bot, company_id):
    data = pd.read_sql('product', engine)
    products_in_company = data.loc[data['company_id'] == company_id, 'id'].values.tolist()
    for product_id in products_in_company:
        delete_product(message, bot, product_id)

    data = pd.read_sql('company', engine)
    image_link = data.loc[data['id'] == company_id, 'image_link'].values[0]

    db = PaginationData()
    sql = f"DELETE FROM company WHERE id = {company_id}"
    db.cursor.execute(sql)
    db.conn.commit()
    if "dropbox" in image_link:
        values = {'type': 'company', 'id': str(company_id)}
        dropbox.delete_file(message, bot, values)


def get_profile_info(telegram_id):
    data = pd.read_sql('consumer', engine)
    return data.loc[data['telegram_id'] == telegram_id].to_dict(orient='records')[0]


def get_orders_info(telegram_id):
    user_id = get_user_id_by_telegram_id(telegram_id)
    data = pd.read_sql('orders', engine)
    return data.loc[data['user_id'] == user_id].to_dict(orient='records')


def get_username_by_telegram_id(user_id):
    data = pd.read_sql('consumer', engine)
    try:
        return data.loc[data['telegram_id'] == user_id, 'username'].values[0]
    except IndexError:
        return "Unauthorized"


def get_company_title_by_id(company_id):
    data = pd.read_sql('company', engine)
    return data.loc[data['id'] == company_id, 'title'].values[0]


def get_user_id_by_telegram_id(user_id):
    data = pd.read_sql('consumer', engine)
    try:
        return data.loc[data['telegram_id'] == user_id, 'id'].values[0]
    except IndexError:
        return "Unauthorized"


def verify_password(username, password):
    data = pd.read_sql('consumer', engine)
    try:
        db_password = data.loc[data['username'] == username, 'password'].values[0]
        return bcrypt.verify(password, db_password)
    except IndexError:
        return "incorrect", False


def change_consumer_telebot_id(username, user_id):
    data = pd.read_sql('consumer', engine)
    data.loc[data['username'] == username, 'telegram_id'] = user_id
    data.to_sql('consumer', engine, if_exists='replace', index=False, index_label='id')


def add_pending_user(user_id):
    df1 = pd.DataFrame([{'user_id': user_id}])
    df1.to_sql('pending_users', engine, if_exists='append', index=False, index_label='id')


def add_new_consumer(username, email, password, telegram_id):
    data = pd.read_sql('consumer', engine)
    df1 = pd.DataFrame(
        [{'id': max(data['id'].values + 1), 'username': username, 'password': bcrypt.hash(password), 'bonuses': 0,
          'email': email,
          'redactor': 'telegram registration', 'telegram_id': telegram_id}])
    df1.to_sql('consumer', engine, if_exists='append', index=False, index_label='id')


def add_new_item(values):
    item_type = values.get('type').lower()
    data = pd.read_sql(item_type, engine)
    item_id = max(data['id'].values + 1)
    values.update({'id': item_id})
    values.pop('type')
    values.pop('image_way')
    df1 = pd.DataFrame([values])
    df1.to_sql(item_type, engine, if_exists='append', index=False, index_label='id')


def delete_pending_user(user_id):
    data = pd.read_sql('pending_users', engine)
    index = data[data['user_id'] == user_id].index
    data = data.drop(index)
    data.to_sql('pending_users', engine, if_exists='replace', index=False, index_label='id')
