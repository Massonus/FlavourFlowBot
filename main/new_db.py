from sqlalchemy import create_engine, Column, Integer, BigInteger, Double, ForeignKey, String, exc, DateTime
from sqlalchemy.orm import sessionmaker, relationship, declarative_base
import config

engine = create_engine(
    f"postgresql+psycopg2://{config.postgres_username}:{config.postgres_test_password}@{config.postgres_test_host}:5432"
    f"/{config.postgres_test_database}")

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


class PendingUser(Base):
    __tablename__ = 'pending_users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))

    @staticmethod
    def get_user_by_telegram_id(telegram_id):
        return session.query(PendingUser).filter_by(user_id=telegram_id).first()


class UserRole(Base):
    __tablename__ = 'user_role'
    user_id = Column(Integer, ForeignKey('consumer.id'), primary_key=True)
    roles = Column(String)

    @staticmethod
    def get_role_by_user_id(user_id):
        return session.query(UserRole).filter_by(user_id=user_id).first()


class Company(Base):
    __tablename__ = 'company'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    image_link = Column(String)
    rating = Column(String)
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


class Basket(Base):
    __tablename__ = 'basket'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))

    @staticmethod
    def get_basket_by_user_id(user_id):
        return session.query(Basket).filter_by(user_id=user_id).first()


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


# Base.metadata.create_all(engine)


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


