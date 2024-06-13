from sqlalchemy import create_engine, Column, Integer, BigInteger, Sequence, Double, Text, ForeignKey, String, func, \
    Date, text, \
    Time, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from passlib.hash import bcrypt
import config
import dropbox_factory as dropbox

# engine = create_engine(
#     f"postgresql+psycopg2://{config.postgres_username}:{config.postgres_test_password}@{config.postgres_test_host}:5432"
#     f"/{config.postgres_practice_database}")

engine = create_engine(
    f"postgresql+psycopg2://{config.postgres_username}:{config.postgres_password}@{config.postgres_host}:5432"
    f"/{config.postgres_database}")

Session = sessionmaker(bind=engine)
Base = declarative_base()
session = Session()


class AccessToken(Base):
    __tablename__ = 'access_token'
    id = Column(BigInteger, primary_key=True)
    value = Column(String(255))

    @staticmethod
    def get_token():
        return session.query(AccessToken).first()

    @staticmethod
    def update_token(value):
        access_token = AccessToken.get_token()
        session.delete(access_token)
        session.add(AccessToken(id=1, value=value))
        session.commit()


class Basket(Base):
    __tablename__ = 'basket'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))

    @staticmethod
    def get_by_user_id(user_id):
        return session.query(Basket).filter_by(user_id=user_id).first()

    @staticmethod
    def get_max_id():
        return session.query(func.max(Basket.id)).first()[0]

    @staticmethod
    def add_new(user_id):
        basket_id = Basket.get_max_id() + 1
        session.add(Basket(id=basket_id, user_id=user_id))
        session.commit()


class BasketObject(Base):
    __tablename__ = 'basket_object'
    id = Column(BigInteger, primary_key=True)
    title = Column(String(255))
    image_link = Column(String(255))
    price = Column(Double)
    amount = Column(Integer)
    company_id = Column(BigInteger, ForeignKey('company.id'))
    user_id = Column(BigInteger, ForeignKey('consumer.id'))
    basket_id = Column(BigInteger, ForeignKey('basket.id'))
    product_id = Column(BigInteger, ForeignKey('product.id'))

    @staticmethod
    def get_by_product_and_user_id(product_id, user_id):
        return session.query(BasketObject).where(BasketObject.product_id == product_id,
                                                 BasketObject.user_id == user_id).first()

    @staticmethod
    def get_max_id():
        result = session.query(func.max(BasketObject.id)).first()[0]
        return result if result is not None else 0

    @staticmethod
    def add_new(product_id, telegram_id):
        user_id = Consumer.get_by_telegram_id(telegram_id).id
        basket_object = BasketObject.get_by_product_and_user_id(product_id, user_id)

        if basket_object is not None:
            basket_object.amount += 1
            session.commit()
            return f"Changed amount {basket_object.amount}"
        else:
            product = Product.get_by_id(product_id)
            values = {'id': BasketObject.get_max_id() + 1,
                      'title': product.title,
                      'image_link': product.image_link,
                      'user_id': user_id,
                      'product_id': product_id,
                      'company_id': product.company_id,
                      'basket_id': Basket.get_by_user_id(user_id).id,
                      'price': product.price,
                      'amount': 1}

            new_object = BasketObject(**values)
            session.add(new_object)
            session.commit()
            return "Added to basket"


class Wish(Base):
    __tablename__ = 'wishes'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))

    @staticmethod
    def get_by_user_id(user_id):
        return session.query(Wish).filter_by(user_id=user_id).first()

    @staticmethod
    def get_max_id():
        return session.query(func.max(Wish.id)).first()[0]

    @staticmethod
    def add_new(user_id):
        wish_id = Wish.get_max_id() + 1
        session.add(Wish(id=wish_id, user_id=user_id))
        session.commit()


class WishObject(Base):
    __tablename__ = 'wish_object'
    id = Column(BigInteger, primary_key=True)
    title = Column(String(255))
    image_link = Column(String(255))
    price = Column(Double)
    company_id = Column(BigInteger, ForeignKey('company.id'))
    user_id = Column(BigInteger, ForeignKey('consumer.id'))
    wish_id = Column(BigInteger, ForeignKey('wishes.id'))
    product_id = Column(BigInteger, ForeignKey('product.id'))

    @staticmethod
    def get_max_id():
        return session.query(func.max(WishObject.id)).first()[0]

    @staticmethod
    def get_by_product_and_user_id(product_id, user_id):
        return session.query(WishObject).where(WishObject.product_id == product_id,
                                               WishObject.user_id == user_id).first()

    @staticmethod
    def add_new(product_id, telegram_id):
        user_id = Consumer.get_by_telegram_id(telegram_id).id
        wish_object = WishObject.get_by_product_and_user_id(product_id, user_id)

        if wish_object is not None:
            session.delete(wish_object)
            session.commit()
            return f"Deleted from wishes"
        else:
            product = Product.get_by_id(product_id)
            values = {'id': WishObject.get_max_id() + 1,
                      'title': product.title,
                      'image_link': product.image_link,
                      'user_id': user_id,
                      'product_id': product_id,
                      'company_id': product.company_id,
                      'wish_id': Wish.get_by_user_id(user_id).id,
                      'price': product.price}

            new_object = WishObject(**values)
            session.add(new_object)
            session.commit()
            return "Added to wishes"


class Order(Base):
    __tablename__ = 'orders'
    id = Column(BigInteger, primary_key=True)
    total = Column(Double)
    date = Column(Date)
    time = Column(Time)
    earned_bonuses = Column(Double)
    address = Column(String(255))
    user_id = Column(BigInteger, ForeignKey('consumer.id'))
    company_id = Column(BigInteger, ForeignKey('company.id'))

    @staticmethod
    def get_by_id(kitchen_id):
        return session.query(Kitchen).filter_by(id=kitchen_id).first()

    @staticmethod
    def get_all_by_user_id(user_id):
        return session.query(Order).filter_by(user_id=user_id).all()


class OrderObject(Base):
    __tablename__ = 'order_object'
    id = Column(BigInteger, primary_key=True)
    title = Column(String(255))
    amount = Column(Integer)
    sum = Column(Double)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))
    order_id = Column(BigInteger, ForeignKey('orders.id'))
    product_id = Column(BigInteger, ForeignKey('product.id'))
    company_id = Column(BigInteger, ForeignKey('company.id'))


class Country(Base):
    __tablename__ = 'company_country'
    id = Column(BigInteger, primary_key=True)
    title = Column(String(255))

    @staticmethod
    def get_by_id(country_id):
        return session.query(Country).filter_by(id=country_id).first()

    @staticmethod
    def get_all():
        return session.query(Country).all()


class Kitchen(Base):
    __tablename__ = 'kitchen_categories'
    id = Column(BigInteger, primary_key=True)
    title = Column(String(255))

    @staticmethod
    def get_by_id(kitchen_id):
        return session.query(Kitchen).filter_by(id=kitchen_id).first()

    @staticmethod
    def get_all():
        return session.query(Kitchen).all()


class Company(Base):
    __tablename__ = 'company'
    id = Column(BigInteger, Sequence('company_seq', start=10), primary_key=True)
    title = Column(String(255))
    description = Column(String(255))
    image_link = Column(String(255))
    rating = Column(Integer)
    category_id = Column(BigInteger, ForeignKey('kitchen_categories.id'))
    country_id = Column(BigInteger, ForeignKey('company_country.id'))

    @staticmethod
    def get_company_by_id(company_id):
        return session.query(Company).filter_by(id=company_id).first()

    @staticmethod
    def get_for_catalog(page=1, skip_size=1):
        skips_page = (page - 1) * skip_size
        company_count = session.query(Company).count()
        return session.query(Company).order_by(Company.title).offset(skips_page).limit(skip_size).first(), company_count

    @staticmethod
    def get_max_id():
        return session.query(func.max(Company.id)).first()[0]

    @staticmethod
    def add_new(values):
        company_id = Company.get_max_id() + 1
        values.update({'rating': None, 'id': company_id})
        session.add(Company(**values))
        sql = text(f"SELECT setval('public.company_seq', {company_id}, true);")
        engine.connect().execute(sql)
        session.commit()

    @staticmethod
    def delete(message, bot, company_id):
        company = session.query(Company).filter_by(id=company_id).first()
        image_link = company.image_link

        products = Product.get_all_by_company_id(company_id)
        for product in products:
            Product.delete(message, bot, product.id)

        if "dropbox" in image_link:
            values = {'type': 'company', 'id': str(company_id)}
            dropbox.delete_file(message, bot, values)
        session.delete(company)
        session.commit()


class Product(Base):
    __tablename__ = 'product'
    id = Column(BigInteger, Sequence('product_seq', start=50), primary_key=True)
    title = Column(String(255))
    description = Column(String(255))
    composition = Column(String(255))
    image_link = Column(String(255))
    product_category = Column(Text)
    price = Column(Double)
    company_id = Column(BigInteger, ForeignKey('company.id'))

    @staticmethod
    def get_by_id(product_id):
        return session.query(Product).filter_by(id=product_id).first()

    @staticmethod
    def get_for_catalog(company_id, page=1, skip_size=1):
        skips_page = (page - 1) * skip_size
        product_count = session.query(Product).where(Product.company_id == company_id).count()
        return session.query(Product).where(Product.company_id == company_id).order_by(Product.title).offset(
            skips_page).limit(skip_size).first(), product_count

    @staticmethod
    def get_all_by_company_id(company_id):
        return session.query(Product).filter_by(company_id=company_id).all()

    @staticmethod
    def delete(message, bot, product_id):
        product = session.query(Product).filter_by(id=product_id).first()
        image_link = product.image_link
        if "dropbox" in image_link:
            values = {'type': 'product', 'id': str(product_id)}
            dropbox.delete_file(message, bot, values)
        session.delete(product)
        session.commit()

    @staticmethod
    def get_max_id():
        return session.query(func.max(Product.id)).first()[0]

    @staticmethod
    def add_new(values):
        product_id = Product.get_max_id() + 1
        values.update({'id': product_id})
        session.add(Product(**values))
        sql = text(f"SELECT setval('public.product_seq', {product_id}, true);")
        engine.connect().execute(sql)
        session.commit()


class Rating(Base):
    __tablename__ = 'rating'
    id = Column(BigInteger, primary_key=True)
    rate = Column(Integer)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))
    company_id = Column(BigInteger, ForeignKey('company.id'))


class Message(Base):
    __tablename__ = 'message'
    id = Column(BigInteger, primary_key=True)
    text = Column(String(255))
    comment_time = Column(DateTime)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))
    item_id = Column(BigInteger)


class MessageLike(Base):
    __tablename__ = 'message_likes'
    message_id = Column(BigInteger, ForeignKey('message.id'), primary_key=True)
    user_id = Column(BigInteger, ForeignKey('consumer.id'), primary_key=True)


class CompanyMessage(Base):
    __tablename__ = 'company_messages'
    company_id = Column(BigInteger, ForeignKey('company.id'), primary_key=True)
    messages_id = Column(BigInteger, ForeignKey('message.id'), primary_key=True)


class Consumer(Base):
    __tablename__ = 'consumer'
    id = Column(BigInteger, primary_key=True)
    username = Column(String(255))
    email = Column(String(255))
    password = Column(String(255))
    redactor = Column(String(255))
    bonuses = Column(Double)
    telegram_id = Column(BigInteger)

    @staticmethod
    def get_user_by_id(user_id):
        result = session.query(Consumer).filter_by(id=user_id).first()
        return result if result is not None else Consumer(username="Unauthorized")

    @staticmethod
    def get_by_telegram_id(telegram_id):
        result = session.query(Consumer).filter_by(telegram_id=telegram_id).first()
        return result if result is not None else Consumer(username="Unauthorized")

    @staticmethod
    def get_by_username(username):
        result = session.query(Consumer).filter_by(username=username).first()
        return result if result is not None else Consumer(username="Unauthorized")

    @staticmethod
    def is_authenticated(telegram_id):
        result = session.query(Consumer).filter_by(telegram_id=telegram_id).first()
        return True if result is not None else False

    @staticmethod
    def is_admin(telegram_id):
        if Consumer.is_authenticated(telegram_id):
            result = session.query(Consumer).filter_by(telegram_id=telegram_id).first()
            role = session.query(UserRole).filter_by(user_id=result.id).first()
            return True if role.roles == "ADMIN" else False
        else:
            return False

    @staticmethod
    def verify_password(username, password):
        user = Consumer.get_by_username(username)
        return bcrypt.verify(password, user.password)

    @staticmethod
    def change_telegram_id(username, telegram_id):
        consumer = session.query(Consumer).filter_by(username=username).first()
        consumer.telegram_id = telegram_id
        session.commit()

    @staticmethod
    def is_username_already_exists(username):
        result = session.query(Consumer).filter_by(username=username).first()
        return True if result is not None else False

    @staticmethod
    def is_email_already_exists(email):
        result = session.query(Consumer).filter_by(email=email).first()
        return True if result is not None else False

    @staticmethod
    def get_max_id():
        return session.query(func.max(Consumer.id)).first()[0]

    @staticmethod
    def add_new(values):
        user_id = Consumer.get_max_id() + 1
        values.update(
            {'password': bcrypt.hash(values.get('password')), 'bonuses': 0, 'redactor': 'telegram registration',
             'id': user_id})
        consumer = Consumer(**values)
        session.add(consumer)
        session.commit()

        Basket.add_new(user_id)
        Wish.add_new(user_id)
        UserRole.add_new(user_id)


class PendingUser(Base):
    __tablename__ = 'pending_users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)

    @staticmethod
    def is_pending(telegram_id):
        result = session.query(PendingUser).filter_by(telegram_id=telegram_id).first()
        return True if result is not None else False

    @staticmethod
    def add_new_pending(telegram_id):
        pending = PendingUser(telegram_id=telegram_id)
        session.add(pending)
        session.commit()

    @staticmethod
    def delete_pending(telegram_id):
        pending = session.query(PendingUser).filter_by(telegram_id=telegram_id).first()
        session.delete(pending)
        session.commit()


class UserRole(Base):
    __tablename__ = 'user_role'
    user_id = Column(BigInteger, ForeignKey('consumer.id'), primary_key=True)
    roles = Column(String(255))

    @staticmethod
    def get_by_user_id(user_id):
        return session.query(UserRole).filter_by(user_id=user_id).first()

    @staticmethod
    def add_new(user_id):
        new = UserRole(user_id=user_id, roles="USER")
        session.add(new)
        session.commit()


# initialize all tables
if __name__ == '__main__':
    Base.metadata.create_all(engine)
