from sqlalchemy import create_engine, Column, Integer, BigInteger, Double, ForeignKey, String, exc, DateTime, func
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
from passlib.hash import bcrypt
import config

engine = create_engine(
    f"postgresql+psycopg2://{config.postgres_username}:{config.postgres_test_password}@{config.postgres_test_host}:5432"
    f"/{config.postgres_test_database}")

# engine = create_engine(
#     f"postgresql+psycopg2://{config.postgres_username}:{config.postgres_password}@{config.postgres_host}:5432"
#     f"/{config.postgres_database}")

Session = sessionmaker(bind=engine)
Base = declarative_base()
session = Session()


class Consumer(Base):
    __tablename__ = 'consumer'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)
    password = Column(String)
    redactor = Column(String)
    bonuses = Column(Double)
    telegram_id = Column(BigInteger)

    @staticmethod
    def get_user_by_id(user_id):
        result = session.query(Consumer).filter_by(id=user_id).first()
        return result if result is not None else Consumer(username="Unauthorized")

    @staticmethod
    def get_user_by_telegram_id(telegram_id):
        result = session.query(Consumer).filter_by(telegram_id=telegram_id).first()
        return result if result is not None else Consumer(username="Unauthorized")

    @staticmethod
    def get_user_by_username(username):
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
        user = Consumer.get_user_by_username(username)
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
    def add_consumer(values):
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
    def add_pending_user(telegram_id):
        pending = PendingUser(telegram_id=telegram_id)
        session.add(pending)
        session.commit()

    @staticmethod
    def delete_pending_user(telegram_id):
        pending = session.query(PendingUser).filter_by(telegram_id=telegram_id).first()
        session.delete(pending)
        session.commit()


class UserRole(Base):
    __tablename__ = 'user_role'
    user_id = Column(Integer, ForeignKey('consumer.id'), primary_key=True)
    roles = Column(String)

    @staticmethod
    def get_role_by_user_id(user_id):
        return session.query(UserRole).filter_by(user_id=user_id).first()

    @staticmethod
    def add_new(user_id):
        new = UserRole(user_id=user_id, roles="USER")
        session.add(new)
        session.commit()


class Company(Base):
    __tablename__ = 'company'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    image_link = Column(String)
    rating = Column(Integer)
    category_id = Column(Integer, ForeignKey('kitchen_categories.id'))
    country_id = Column(Integer, ForeignKey('company_country.id'))

    @staticmethod
    def get_company_by_id(company_id):
        return session.query(Company).filter_by(id=company_id).first()

    @staticmethod
    def get_companies_for_catalog(page=1, skip_size=1):
        skips_page = (page - 1) * skip_size
        company_count = session.query(Company).count()
        return session.query(Company).order_by(Company.title).offset(skips_page).limit(skip_size).first(), company_count

    @staticmethod
    def add_new_company(values):
        session.add(Company(id=values.get('id'), title=values.get('title'), description=values.get('description'),
                            image_link=values.get('image_link'), country_id=values.get('country_id'),
                            category_id=values.get('category_id'), rating=0))
        session.commit()


class Product(Base):
    __tablename__ = 'product'
    id = Column(BigInteger, primary_key=True)
    title = Column(String)
    description = Column(String)
    composition = Column(String)
    image_link = Column(String)
    product_category = Column(String)
    price = Column(Double)
    company_id = Column(BigInteger, ForeignKey('company.id'))

    @staticmethod
    def get_product_by_id(product_id):
        return session.query(Product).filter_by(id=product_id).first()

    @staticmethod
    def get_products_for_catalog(company_id, page=1, skip_size=1):
        skips_page = (page - 1) * skip_size
        product_count = session.query(Product).where(Product.company_id == company_id).count()
        return session.query(Product).where(Product.company_id == company_id).order_by(Product.title).offset(
            skips_page).limit(skip_size).first(), product_count


class Country(Base):
    __tablename__ = 'company_country'
    id = Column(BigInteger, primary_key=True)
    title = Column(String)

    @staticmethod
    def get_country_by_id(country_id):
        return session.query(Country).filter_by(id=country_id).first()

    @staticmethod
    def get_all():
        return session.query(Country).all()


class Kitchen(Base):
    __tablename__ = 'kitchen_categories'
    id = Column(BigInteger, primary_key=True)
    title = Column(String)

    @staticmethod
    def get_kitchen_by_id(kitchen_id):
        return session.query(Kitchen).filter_by(id=kitchen_id).first()

    @staticmethod
    def get_all():
        return session.query(Kitchen).all()


class Order(Base):
    __tablename__ = 'orders'
    id = Column(BigInteger, primary_key=True)
    total = Column(Double)
    date = Column(DateTime)
    time = Column(DateTime)
    earned_bonuses = Column(Double)
    address = Column(String)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))
    company_id = Column(BigInteger, ForeignKey('company.id'))

    @staticmethod
    def get_kitchen_by_id(kitchen_id):
        return session.query(Kitchen).filter_by(id=kitchen_id).first()

    @staticmethod
    def get_orders_by_user_id(user_id):
        return session.query(Order).filter_by(user_id=user_id).all()


class Basket(Base):
    __tablename__ = 'basket'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))

    @staticmethod
    def get_basket_by_user_id(user_id):
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
    title = Column(String)
    image_link = Column(String)
    price = Column(Double)
    amount = Column(Integer)
    company_id = Column(BigInteger, ForeignKey('company.id'))
    user_id = Column(BigInteger, ForeignKey('consumer.id'))
    basket_id = Column(BigInteger, ForeignKey('basket.id'))
    product_id = Column(BigInteger, ForeignKey('product.id'))

    @staticmethod
    def get_basket_object_by_user_id(user_id):
        return session.query(BasketObject).filter_by(user_id=user_id).first()

    @staticmethod
    def get_basket_object_by_basket_id(basket_id):
        return session.query(BasketObject).filter_by(basket_id=basket_id).first()


class Wish(Base):
    __tablename__ = 'wishes'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))

    @staticmethod
    def get_wish_by_user_id(user_id):
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
    title = Column(String)
    image_link = Column(String)
    price = Column(Double)
    company_id = Column(BigInteger, ForeignKey('company.id'))
    user_id = Column(BigInteger, ForeignKey('consumer.id'))
    wish_id = Column(BigInteger, ForeignKey('wishes.id'))
    product_id = Column(BigInteger, ForeignKey('product.id'))

    @staticmethod
    def get_wish_object_by_user_id(user_id):
        return session.query(BasketObject).filter_by(user_id=user_id).first()

    @staticmethod
    def get_wish_object_by_basket_id(basket_id):
        return session.query(BasketObject).filter_by(basket_id=basket_id).first()


class AccessToken(Base):
    __tablename__ = 'access_token'
    id = Column(BigInteger, primary_key=True)
    value = Column(String)


Base.metadata.create_all(engine)

# print(Company.get_company_by_id(1).title)
# print(Consumer.get_user_by_id(1).username)
# print(UserRole.get_role_by_user_id(1).roles)
# print(Product.get_product_by_id(1).title)
# print(Country.get_country_by_id(1).title)
# print(Kitchen.get_kitchen_by_id(1).title)
# print(Basket.get_basket_by_user_id(1).user_id)
# print(BasketObject.get_basket_object_by_basket_id(11).title)
# print(Wish.get_wish_by_user_id(1).user_id)
# print(WishObject.get_wish_object_by_user_id(1).title)
