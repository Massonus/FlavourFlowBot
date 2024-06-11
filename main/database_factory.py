from sqlalchemy import create_engine, Column, Integer, BigInteger, Double, ForeignKey, String, exc
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import psycopg2
import pandas as pd
import dropbox_factory as dropbox
import config
from passlib.hash import bcrypt

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


def delete_product(message, bot, product_id):
    data = pd.read_sql('product', engine)
    image_link = data.loc[data['id'] == product_id, 'image_link'].values[0]

    db = PsycopgDB()
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

    db = PsycopgDB()
    sql = f"DELETE FROM company WHERE id = {company_id}"
    db.cursor.execute(sql)
    db.conn.commit()
    if "dropbox" in image_link:
        values = {'type': 'company', 'id': str(company_id)}
        dropbox.delete_file(message, bot, values)


def get_orders_info(telegram_id):
    user_id = get_user_id_by_telegram_id(telegram_id)
    data = pd.read_sql('orders', engine)
    return data.loc[data['user_id'] == user_id].to_dict(orient='records')


def add_to_basket(product_id, telegram_id, bot, message):
    product_data = pd.read_sql('product', engine)
    basket_object_data = pd.read_sql('basket_object', engine)
    basket_data = pd.read_sql('basket', engine)
    user_id = get_user_id_by_telegram_id(telegram_id)

    product = product_data.loc[product_data['id'] == product_id].to_dict(orient='records')[0]

    basket_id = basket_data.loc[basket_data['user_id'] == user_id, 'id'].values[0]

    sql = (f"SELECT * FROM public.basket_object AS obj "
           f"WHERE product_id = {product_id} AND user_id = {user_id}")
    db = PsycopgDB()
    db.cursor.execute(sql)
    product_params = db.cursor.fetchone()

    if product_params is None:

        df1 = pd.DataFrame(
            [{'title': product.get('title'), 'image_link': product.get('image_link'), 'user_id': user_id,
              'product_id': product_id, 'id': max(basket_object_data['id'].values + 1),
              'company_id': product.get('company_id'), 'basket_id': basket_id, 'price': product.get('price'),
              'amount': 1}])
        df1.to_sql('basket_object', engine, if_exists='append', index=False, index_label='id')
        bot.send_message(message.chat.id, 'Added to your basket')
    else:
        amount = basket_object_data.loc[basket_object_data['id'] == product_params[4], 'amount'].values[0]
        sql = (f"UPDATE public.basket_object "
               f"SET amount={amount + 1} "
               f"WHERE id={product_params[4]}")
        db.cursor.execute(sql)
        db.conn.commit()
        bot.send_message(message.chat.id, f'Changed amount to {amount + 1}')


def add_to_wish(product_id, telegram_id, bot, message):
    product_data = pd.read_sql('product', engine)
    wish_object_data = pd.read_sql('wish_object', engine)
    wish_data = pd.read_sql('wishes', engine)
    user_id = get_user_id_by_telegram_id(telegram_id)

    product = product_data.loc[product_data['id'] == product_id].to_dict(orient='records')[0]

    wish_id = wish_data.loc[wish_data['user_id'] == user_id, 'id'].values[0]

    sql = (f"SELECT * FROM public.wish_object AS obj "
           f"WHERE product_id = {product_id} AND user_id = {user_id}")
    db = PsycopgDB()
    db.cursor.execute(sql)
    product_params = db.cursor.fetchone()

    if product_params is None:

        df1 = pd.DataFrame(
            [{'title': product.get('title'), 'image_link': product.get('image_link'), 'wish_id': wish_id,
              'user_id': user_id,
              'product_id': product_id, 'id': max(wish_object_data['id'].values + 1),
              'company_id': product.get('company_id'), 'price': product.get('price')}])
        df1.to_sql('wish_object', engine, if_exists='append', index=False, index_label='id')
        bot.send_message(message.chat.id, 'Added to your wishes')
    else:
        sql = (f"DELETE FROM public.wish_object "
               f"WHERE id = {product_params[3]} ")
        db.cursor.execute(sql)
        db.conn.commit()
        bot.send_message(message.chat.id, 'Deleted from wishes')


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
    sql = (f"UPDATE public.consumer "
           f"SET telegram_id={user_id} "
           f"WHERE username='{username}' ")
    db = PsycopgDB()
    db.cursor.execute(sql)
    db.conn.commit()


def add_new_consumer(username, email, password, telegram_id):
    consumer_data = pd.read_sql('consumer', engine)
    user_id = max(consumer_data['id'].values + 1)
    consumer_data = pd.DataFrame(
        [{'id': user_id, 'username': username, 'password': bcrypt.hash(password), 'bonuses': 0,
          'email': email,
          'redactor': 'telegram registration', 'telegram_id': telegram_id}])
    consumer_data.to_sql('consumer', engine, if_exists='append', index=False, index_label='id')

    basket_data = pd.read_sql('basket', engine)
    wish_data = pd.read_sql('wish_object', engine)
    basket_id = max(basket_data['id'].values + 1)
    wish_id = max(wish_data['id'].values + 1)
    basket_data = pd.DataFrame([{'id': basket_id, 'user_id': user_id}])
    wish_data = pd.DataFrame([{'id': wish_id, 'user_id': user_id}])
    user_role_data = pd.DataFrame([{'user_id': user_id, 'roles': "USER"}])
    user_role_data.to_sql('user_role', engine, if_exists='append', index=False, index_label='id')
    basket_data.to_sql('basket', engine, if_exists='append', index=False, index_label='id')
    wish_data.to_sql('wishes', engine, if_exists='append', index=False, index_label='id')


def add_new_item(values):
    item_type = values.get('type').lower()
    data = pd.read_sql(item_type, engine)
    item_id = max(data['id'].values + 1)
    values.update({'id': item_id})
    values.pop('type')
    values.pop('image_way')
    df1 = pd.DataFrame([values])
    df1.to_sql(item_type, engine, if_exists='append', index=False, index_label='id')
