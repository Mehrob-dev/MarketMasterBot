from sqlalchemy import create_engine, Column, Integer, Float, BigInteger, String, DateTime, Boolean, ForeignKey
from datetime import datetime
from sqlalchemy.orm import declarative_base, relationship
from dotenv import load_dotenv
import os

load_dotenv()
db_name = os.getenv('DB_NAME')
user = os.getenv('USER')
password = os.getenv('PASSWORD')

db_url = f'postgresql://{user}:{password}@localhost:5432/{db_name}'
engine = create_engine(db_url)

Base = declarative_base()


class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True)
    username = Column(String)
    full_name = Column(String)
    name = Column(String)
    surname = Column(String)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now())
    balance = Column(Float, default=0.0)
    age = Column(Integer)
    carts = relationship('Carts', back_populates='user')
    orders = relationship('Orders', back_populates='user')
    reviews = relationship('Reviews', back_populates='user')


class Categories(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    title = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.now())

    products = relationship('Products', back_populates='category')


class Products(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('categories.id'))
    title = Column(String)
    description = Column(String)
    price = Column(Integer)
    stock = Column(Integer, default=0)
    photo_file_id = Column(String)
    created_at = Column(DateTime, default=datetime.now())
    avg_rating = Column(Float, default=0)
    reviews_count = Column(Integer, default=0)

    category = relationship('Categories', back_populates='products')
    cart_items = relationship('CartItems', back_populates='product')
    order_items = relationship('OrderItems', back_populates='product')
    reviews = relationship('Reviews', back_populates='product')


class Carts(Base):
    __tablename__ = 'carts'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String, default='active')
    created_at = Column(DateTime, default=datetime.now())

    user = relationship('Users', back_populates='carts')
    items = relationship('CartItems', back_populates='cart')


class CartItems(Base):
    __tablename__ = 'cart_items'

    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey('carts.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    qty = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.now())

    cart = relationship('Carts', back_populates='items')
    product = relationship('Products', back_populates='cart_items')


class Orders(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    total_price = Column(Integer, default=0)
    status = Column(String, default='new')
    payment_method = Column(String, default='manual_card')
    created_at = Column(DateTime, default=datetime.now())

    user = relationship('Users', back_populates='orders')
    items = relationship('OrderItems', back_populates='order')


class OrderItems(Base):
    __tablename__ = 'order_items'

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    qty = Column(Integer, default=1)
    price_at_buy = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now())

    order = relationship('Orders', back_populates='items')
    product = relationship('Products', back_populates='order_items')


class Reviews(Base):
    __tablename__ = 'reviews'

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    stars = Column(Integer)
    text = Column(String)
    created_at = Column(DateTime, default=datetime.now())

    product = relationship('Products', back_populates='reviews')
    user = relationship('Users', back_populates='reviews')


Base.metadata.create_all(engine)
