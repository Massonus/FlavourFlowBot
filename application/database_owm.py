import asyncio

from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from passlib.hash import bcrypt
from psycopg import errors
from sqlalchemy import (create_engine, Column, Integer, BigInteger, Sequence, Double, Text, ForeignKey, String, func,
                        Date, Time, DateTime, text)
from sqlalchemy import exc as sqlalchemy_exc
from sqlalchemy.orm import exc as sqlalchemy_orm_exc
from sqlalchemy.orm import sessionmaker, declarative_base

import application.dropbox_factory as dropbox
from application.config import INITIALIZE_ENGINE, ADMIN_ID
from application.handlers.output_handler import send_alarm

engine = create_engine(INITIALIZE_ENGINE)

Session = sessionmaker(bind=engine)
Base = declarative_base()


class DatabaseSessionManager:
    def __init__(self, message: Message = None):
        self.session = Session()
        self.message = message

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_value, traceback_obj):
        if self.session.dirty or self.session.new or self.session.deleted:
            if exc_type is None:
                try:
                    self.session.commit()
                    if self.message is not None:
                        if asyncio.get_event_loop().is_running():
                            asyncio.create_task(self.print_message('success'))
                        else:
                            asyncio.run(self.print_message('success'))

                except (errors.ForeignKeyViolation, sqlalchemy_exc.IntegrityError):
                    self.session.rollback()
                    if asyncio.get_event_loop().is_running():
                        asyncio.create_task(self.print_message('fail'))
                    else:
                        asyncio.run(self.print_message('fail'))
                    raise
                except Exception as error:
                    self.session.rollback()
                    if asyncio.get_event_loop().is_running():
                        asyncio.create_task(self.handle_error(error))
                    else:
                        asyncio.run(self.handle_error(error))
                    raise
            else:
                self.session.rollback()
        self.session.close()

    @staticmethod
    async def handle_error(error):
        await send_alarm(ADMIN_ID, error)

    async def print_message(self, operation_result: str):
        if operation_result == 'success':
            await self.message.answer('Operation was successful')
        elif operation_result == 'fail':
            await self.message.answer('Operation failed')
        else:
            await self.message.answer('Fatal error')


class AccessToken(Base):
    __tablename__ = 'access_token'
    id = Column(BigInteger, primary_key=True)
    value = Column(String(255))

    @staticmethod
    def get_token():
        with DatabaseSessionManager() as session:
            return session.query(AccessToken).first()

    @staticmethod
    async def update_token(value: str):
        with DatabaseSessionManager() as session:
            try:
                access_token = AccessToken.get_token()
                session.delete(access_token)
            except sqlalchemy_orm_exc.UnmappedInstanceError:
                print("Token is empty. adding new one")
            session.add(AccessToken(id=1, value=value))


class Basket(Base):
    __tablename__ = 'basket'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))

    @staticmethod
    def get_by_user_id(user_id: int):
        with DatabaseSessionManager() as session:
            return session.query(Basket).filter_by(user_id=user_id).first()

    @staticmethod
    def get_max_id():
        with DatabaseSessionManager() as session:
            return session.query(func.max(Basket.id)).first()[0]

    @staticmethod
    async def add_new(user_id: int):
        with DatabaseSessionManager() as session:
            basket_id = Basket.get_max_id() + 1
            session.add(Basket(id=basket_id, user_id=user_id))
            await change_sequence(Basket.__tablename__, basket_id)


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
        with DatabaseSessionManager() as session:
            return session.query(BasketObject).where(BasketObject.product_id == product_id,
                                                     BasketObject.user_id == user_id).first()

    @staticmethod
    def get_max_id():
        with DatabaseSessionManager() as session:
            result = session.query(func.max(BasketObject.id)).first()[0]
            return result if result is not None else 0

    @staticmethod
    async def add_new(product_id: int, telegram_id: int):
        with DatabaseSessionManager() as session:
            user_id = Consumer.get_by_telegram_id(telegram_id).id
            basket_object = BasketObject.get_by_product_and_user_id(product_id, user_id)

            if basket_object is not None:
                basket_object.amount += 1
                return f"Changed amount {basket_object.amount}"
            else:
                basket_object_id = BasketObject.get_max_id() + 1
                product = Product.get_by_id(product_id)
                values = {'id': basket_object_id,
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
                await change_sequence(BasketObject.__tablename__, basket_object_id)
                return "Added to basket"


class Wish(Base):
    __tablename__ = 'wishes'
    id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))

    @staticmethod
    def get_by_user_id(user_id: int):
        with DatabaseSessionManager() as session:
            return session.query(Wish).filter_by(user_id=user_id).first()

    @staticmethod
    def get_max_id():
        with DatabaseSessionManager() as session:
            return session.query(func.max(Wish.id)).first()[0]

    @staticmethod
    async def add_new(user_id: int):
        with DatabaseSessionManager() as session:
            wish_id = Wish.get_max_id() + 1
            session.add(Wish(id=wish_id, user_id=user_id))
            await change_sequence(Wish.__tablename__, wish_id)


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
        with DatabaseSessionManager() as session:
            return session.query(func.max(WishObject.id)).first()[0]

    @staticmethod
    def get_by_product_and_user_id(product_id, user_id):
        with DatabaseSessionManager() as session:
            return session.query(WishObject).where(WishObject.product_id == product_id,
                                                   WishObject.user_id == user_id).first()

    @staticmethod
    async def add_new(product_id: int, telegram_id: int):
        with DatabaseSessionManager() as session:
            user_id = Consumer.get_by_telegram_id(telegram_id).id
            wish_object = WishObject.get_by_product_and_user_id(product_id, user_id)

            if wish_object is not None:
                session.delete(wish_object)
                return f"Deleted from wishes"
            else:
                wish_object_id = WishObject.get_max_id() + 1
                product = Product.get_by_id(product_id)
                values = {'id': wish_object_id,
                          'title': product.title,
                          'image_link': product.image_link,
                          'user_id': user_id,
                          'product_id': product_id,
                          'company_id': product.company_id,
                          'wish_id': Wish.get_by_user_id(user_id).id,
                          'price': product.price}

                new_object = WishObject(**values)
                session.add(new_object)
                await change_sequence(WishObject.__tablename__, wish_object_id)
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
    def get_by_id(kitchen_id: int):
        with DatabaseSessionManager() as session:
            return session.query(Kitchen).filter_by(id=kitchen_id).first()

    @staticmethod
    def get_all_by_user_id(user_id: int):
        with DatabaseSessionManager() as session:
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
    def get_by_id(country_id: int):
        with DatabaseSessionManager() as session:
            return session.query(Country).filter_by(id=country_id).first()

    @staticmethod
    def get_all():
        with DatabaseSessionManager() as session:
            return session.query(Country).all()


class Kitchen(Base):
    __tablename__ = 'kitchen_category'
    id = Column(BigInteger, primary_key=True)
    title = Column(String(255))

    @staticmethod
    def get_by_id(kitchen_id: int):
        with DatabaseSessionManager() as session:
            return session.query(Kitchen).filter_by(id=kitchen_id).first()

    @staticmethod
    def get_all():
        with DatabaseSessionManager() as session:
            return session.query(Kitchen).all()


class Company(Base):
    __tablename__ = 'company'
    id = Column(BigInteger, Sequence('company_seq', start=10), primary_key=True)
    title = Column(String(255))
    description = Column(String(255))
    image_link = Column(String(255))
    rating = Column(Integer)
    category_id = Column(BigInteger, ForeignKey('kitchen_category.id'))
    country_id = Column(BigInteger, ForeignKey('company_country.id'))

    @staticmethod
    def get_company_by_id(company_id: int):
        with DatabaseSessionManager() as session:
            return session.query(Company).filter_by(id=company_id).first()

    @staticmethod
    def get_for_catalog(page: int = 1, skip_size: int = 1):
        with DatabaseSessionManager() as session:
            skips_page = (page - 1) * skip_size
            company_count = session.query(Company).count()
            return session.query(Company).order_by(Company.title).offset(skips_page).limit(
                skip_size).first(), company_count

    @staticmethod
    def get_max_id():
        with DatabaseSessionManager() as session:
            return session.query(func.max(Company.id)).first()[0]

    @staticmethod
    async def add_new(values: dict):
        with DatabaseSessionManager() as session:
            company_id = Company.get_max_id() + 1
            values.update({'rating': None, 'id': company_id})
            session.add(Company(**values))
            await change_sequence(Company.__tablename__, company_id)

    @staticmethod
    async def delete(message: Message, state: FSMContext, company_id: int):
        with DatabaseSessionManager() as session:
            company = session.query(Company).filter_by(id=company_id).first()
            image_link = company.image_link

            if "dropbox" in image_link:
                values = {'type': 'company', 'id': str(company_id)}
                await dropbox.delete_file(message, state, values)
            else:
                await Company.delete_directly(company_id, message, state)

    @staticmethod
    async def delete_directly(company_id: int, message: Message, state: FSMContext):
        with DatabaseSessionManager(message) as session:
            try:
                products = Product.get_all_by_company_id(company_id)
                for product in products:
                    await Product.delete(message=message, product_id=product.id, state=state)

                company = session.query(Company).filter_by(id=company_id).first()
                session.delete(company)
                return True
            except (errors.ForeignKeyViolation, sqlalchemy_exc.IntegrityError):
                await message.answer('Foreign Key violation')


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
    def get_by_id(product_id: int):
        with DatabaseSessionManager() as session:
            return session.query(Product).filter_by(id=product_id).first()

    @staticmethod
    def get_for_catalog(company_id, page: int = 1, skip_size: int = 1):
        with DatabaseSessionManager() as session:
            skips_page = (page - 1) * skip_size
            product_count = session.query(Product).where(Product.company_id == company_id).count()
            return session.query(Product).where(Product.company_id == company_id).order_by(Product.title).offset(
                skips_page).limit(skip_size).first(), product_count

    @staticmethod
    def get_all_by_company_id(company_id: int):
        with DatabaseSessionManager() as session:
            return session.query(Product).filter_by(company_id=company_id).all()

    @staticmethod
    async def delete(message: Message, state: FSMContext, product_id):
        with DatabaseSessionManager() as session:
            product = session.query(Product).filter_by(id=product_id).first()
            image_link = product.image_link
            if "dropbox" in image_link:
                values = {'type': 'product', 'id': str(product_id)}
                await dropbox.delete_file(message, state, values)
            else:
                await Product.delete_directly(product.id, message)

    @staticmethod
    async def delete_directly(product_id: int, message: Message):
        with DatabaseSessionManager(message) as session:
            try:
                product = session.query(Product).filter_by(id=product_id).first()
                title = product.title
                session.delete(product)
                await message.answer(f"Trying to delete product: {title}")
                return True
            except (errors.ForeignKeyViolation, sqlalchemy_exc.IntegrityError):
                await message.answer('Foreign Key violation')

    @staticmethod
    def get_max_id():
        with DatabaseSessionManager() as session:
            return session.query(func.max(Product.id)).first()[0]

    @staticmethod
    async def add_new(values):
        with DatabaseSessionManager() as session:
            product_id = Product.get_max_id() + 1
            values.update({'id': product_id})
            session.add(Product(**values))
            await change_sequence(Product.__tablename__, product_id)


class Rating(Base):
    __tablename__ = 'rating'
    id = Column(BigInteger, primary_key=True)
    rate = Column(Integer)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))
    company_id = Column(BigInteger, ForeignKey('company.id'))


class Comment(Base):
    __tablename__ = 'comment'
    id = Column(BigInteger, primary_key=True)
    text = Column(String(255))
    comment_time = Column(DateTime)
    user_id = Column(BigInteger, ForeignKey('consumer.id'))
    item_id = Column(BigInteger)


class CommentLike(Base):
    __tablename__ = 'comment_like'
    message_id = Column(BigInteger, ForeignKey('comment.id'), primary_key=True)
    user_id = Column(BigInteger, ForeignKey('consumer.id'), primary_key=True)


class CompanyComment(Base):
    __tablename__ = 'company_comment'
    company_id = Column(BigInteger, ForeignKey('company.id'), primary_key=True)
    message_id = Column(BigInteger, ForeignKey('comment.id'), primary_key=True)


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
    def get_user_by_id(user_id: int):
        with DatabaseSessionManager() as session:
            result = session.query(Consumer).filter_by(id=user_id).first()
            return result if result is not None else Consumer(username="Unauthorized")

    @staticmethod
    def get_by_telegram_id(telegram_id: int):
        with DatabaseSessionManager() as session:
            result = session.query(Consumer).filter_by(telegram_id=telegram_id).first()
            return result if result is not None else Consumer(username="Unauthorized")

    @staticmethod
    def get_by_username(username: str):
        with DatabaseSessionManager() as session:
            result = session.query(Consumer).filter_by(username=username).first()
            return result if result is not None else Consumer(username="Unauthorized")

    @staticmethod
    def is_authenticated(telegram_id: int):
        with DatabaseSessionManager() as session:
            result = session.query(Consumer).filter_by(telegram_id=telegram_id).first()
            return True if result is not None else False

    @staticmethod
    def is_admin(telegram_id: int):
        with DatabaseSessionManager() as session:
            if Consumer.is_authenticated(telegram_id):
                result = session.query(Consumer).filter_by(telegram_id=telegram_id).first()
                role = session.query(UserRole).filter_by(user_id=result.id).first()
                return True if role.roles == "ADMIN" else False
            else:
                return False

    @staticmethod
    def verify_password(username: str, password: str):
        user = Consumer.get_by_username(username)
        try:
            return bcrypt.verify(password, user.password)
        except TypeError:
            return False

    @staticmethod
    async def change_telegram_id(username: str, telegram_id: int):
        with DatabaseSessionManager() as session:
            consumer = session.query(Consumer).filter_by(username=username).first()
            consumer.telegram_id = telegram_id

    @staticmethod
    def is_username_already_exists(username: str):
        with DatabaseSessionManager() as session:
            result = session.query(Consumer).filter_by(username=username).first()
            return True if result is not None else False

    @staticmethod
    def is_email_already_exists(email: str):
        with DatabaseSessionManager() as session:
            result = session.query(Consumer).filter_by(email=email).first()
            return True if result is not None else False

    @staticmethod
    def get_max_id():
        with DatabaseSessionManager() as session:
            return session.query(func.max(Consumer.id)).first()[0]

    @staticmethod
    async def add_new(values: dict):
        with DatabaseSessionManager() as session:
            user_id = Consumer.get_max_id() + 1
            values.update(
                {'password': bcrypt.hash(values.get('password')), 'bonuses': 0, 'redactor': 'telegram registration',
                 'id': user_id})
            consumer = Consumer(username=values.get('username'), email=values.get('email'),
                                password=values.get('password'),
                                telegram_id=values.get('telegram_id'), bonuses=0, redactor='telegram registration',
                                id=values.get('id'))
            session.add(consumer)
            await change_sequence(Consumer.__tablename__, user_id)

            await Basket.add_new(user_id)
            await Wish.add_new(user_id)
            await UserRole.add_new(user_id)


class PendingUser(Base):
    __tablename__ = 'pending_users'
    id = Column(BigInteger, primary_key=True)
    telegram_id = Column(BigInteger)

    @staticmethod
    def get_max_id():
        with DatabaseSessionManager() as session:
            result = session.query(func.max(PendingUser.id)).first()[0]
            return result if result is not None else 0

    @staticmethod
    def is_pending(telegram_id: int):
        with DatabaseSessionManager() as session:
            result = session.query(PendingUser).filter_by(telegram_id=telegram_id).first()
            return True if result is not None else False

    @staticmethod
    async def add_new_pending(telegram_id: int):
        with DatabaseSessionManager() as session:
            pending_id = PendingUser.get_max_id() + 1
            pending = PendingUser(id=pending_id, telegram_id=telegram_id)
            session.add(pending)

    @staticmethod
    async def delete_pending(telegram_id: int):
        with DatabaseSessionManager() as session:
            pending = session.query(PendingUser).filter_by(telegram_id=telegram_id).first()
            session.delete(pending)


class UserRole(Base):
    __tablename__ = 'user_role'
    user_id = Column(BigInteger, ForeignKey('consumer.id'), primary_key=True)
    roles = Column(String(255))

    @staticmethod
    def get_by_user_id(user_id: int):
        with DatabaseSessionManager() as session:
            return session.query(UserRole).filter_by(user_id=user_id).first()

    @staticmethod
    async def add_new(user_id: int):
        with DatabaseSessionManager() as session:
            new = UserRole(user_id=user_id, roles="USER")
            session.add(new)


async def change_sequence(table: str, value: int):
    sql = text(f"SELECT setval('public.{table.lower()}_seq', {value}, true);")
    engine.connect().execute(sql)


# initialize all tables
if __name__ == '__main__':
    # Base.metadata.create_all(engine)
    Base.metadata.tables['consumer'].create(bind=engine)
