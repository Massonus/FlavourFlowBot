from sqlalchemy import create_engine, Column, Integer, BigInteger, Double, ForeignKey, String, exc
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
    id = Column(BigInteger, primary_key=True)
    username = Column(String)
    email = Column(String)
    password = Column(String)
    redactor = Column(String)
    bonuses = Column(Double)
    telegram_id = Column(BigInteger)

    @staticmethod
    def get_user_by_id(user_id):
        return session.query(Consumer).filter_by(id=user_id).first()


class PendingUser(Base):
    __tablename__ = 'pending_users'
    id = Column(BigInteger, primary_key=True)
    telegram_id = Column(BigInteger)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))


class UserRole(Base):
    __tablename__ = 'user_role'
    user_id = Column(BigInteger, ForeignKey('consumer.id'))
    roles = Column(String)


class Company(Base):
    __tablename__ = 'company'
    id = Column(BigInteger, primary_key=True)
    title = Column(String)
    description = Column(String)
    image_link = Column(String)
    rating = Column(String)
    category_id = Column(BigInteger, ForeignKey('kitchen_categories.id'))
    country_id = Column(BigInteger, ForeignKey('company_country.id'))


class Product(Base):
    __tablename__ = 'product'
    id = Column(BigInteger, primary_key=True)
    title = Column(String)
    description = Column(String)
    composition = Column(String)
    image_link = Column(String)
    product_company = Column(String)
    price = Column(Double)
    company_id = Column(BigInteger, ForeignKey('company.id'))


class Country(Base):
    __tablename__ = 'company_country'
    id = Column(BigInteger, primary_key=True)
    title = Column(String)
    company = relationship("Company", back_populates="company_country")


class Kitchen(Base):
    __tablename__ = 'kitchen_categories'
    id = Column(BigInteger, primary_key=True)
    title = Column(String)
    company = relationship("Company", back_populates="kitchen_categories")


class Basket(Base):
    __tablename__ = 'basket'
    id = Column(BigInteger, primary_key=True)
    company_id = Column(BigInteger, ForeignKey('consumer.id'))


class BasketObject(Base):
    __tablename__ = 'basket_object'
    id = Column(BigInteger, primary_key=True)
    title = Column(String)
    image_link = Column(String)
    price = Column(Double)
    amount = Column(Integer)
    company_id = Column(BigInteger, ForeignKey('company.id'))
    user_id = Column(BigInteger, ForeignKey('user.id'))
    basket_id = Column(BigInteger, ForeignKey('basket.id'))
    product_id = Column(BigInteger, ForeignKey('product.id'))


class Wish(Base):
    __tablename__ = 'wishes'
    id = Column(BigInteger, primary_key=True)
    company_id = Column(BigInteger, ForeignKey('consumer.id'))


class WishObject(Base):
    __tablename__ = 'wish_object'
    id = Column(BigInteger, primary_key=True)
    title = Column(String)
    image_link = Column(String)
    price = Column(Double)
    company_id = Column(BigInteger, ForeignKey('company.id'))
    user_id = Column(BigInteger, ForeignKey('user.id'))
    basket_id = Column(BigInteger, ForeignKey('basket.id'))
    product_id = Column(BigInteger, ForeignKey('product.id'))


class AccessToken(Base):
    __tablename__ = 'access_token'
    id = Column(BigInteger, primary_key=True)
    value = Column(String)


print(Consumer.get_user_by_id(1).username)
