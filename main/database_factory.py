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


def add_to_basket(product_id, telegram_id, bot, message):
    product_data = pd.read_sql('product', engine)
    basket_object_data = pd.read_sql('basket_object', engine)
    basket_data = pd.read_sql('basket', engine)
    user_id = new_db.Consumer.get_user_by_telegram_id(telegram_id).id

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
    user_id = new_db.Consumer.get_user_by_telegram_id(telegram_id).id

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


def add_new_item(values):
    item_type = values.get('type').lower()
    data = pd.read_sql(item_type, engine)
    item_id = max(data['id'].values + 1)
    values.update({'id': item_id})
    values.pop('type')
    values.pop('image_way')
    df1 = pd.DataFrame([values])
    df1.to_sql(item_type, engine, if_exists='append', index=False, index_label='id')
