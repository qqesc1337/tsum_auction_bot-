from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///tsum_auction.db")

if "postgres" in DATABASE_URL:
    engine = create_engine(DATABASE_URL)
else:
    engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, index=True)  # ← ИЗМЕНЕНО НА BigInteger
    tg_username = Column(String)
    play_nick = Column(String, unique=True)
    rating = Column(Float, default=5.0)
    deals_count = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    is_scammer = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    is_owner = Column(Boolean, default=False)
    registration_date = Column(DateTime, default=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    lots = relationship("Lot", foreign_keys="Lot.seller_id")
    purchases = relationship("Lot", foreign_keys="Lot.buyer_id")

class Lot(Base):
    __tablename__ = 'lots'
    id = Column(Integer, primary_key=True)
    seller_id = Column(BigInteger, ForeignKey('users.tg_id'))  # ← ИЗМЕНЕНО
    title = Column(String)
    description = Column(Text)
    photo_id = Column(String)
    start_price = Column(Float)
    current_price = Column(Float)
    min_bet = Column(Float)
    end_time = Column(DateTime)
    is_active = Column(Boolean, default=True)
    is_sold = Column(Boolean, default=False)
    buyer_id = Column(BigInteger, ForeignKey('users.tg_id'), nullable=True)  # ← ИЗМЕНЕНО
    created_at = Column(DateTime, default=datetime.utcnow)
    last_bidder_id = Column(BigInteger, ForeignKey('users.tg_id'), nullable=True)  # ← ИЗМЕНЕНО
    views_count = Column(Integer, default=0)
    bid_count = Column(Integer, default=0)
    confirmed_by_seller = Column(Boolean, default=False)
    confirmed_by_buyer = Column(Boolean, default=False)

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    lot_id = Column(Integer, ForeignKey('lots.id'))
    seller_id = Column(BigInteger, ForeignKey('users.tg_id'))  # ← ИЗМЕНЕНО
    buyer_id = Column(BigInteger, ForeignKey('users.tg_id'))  # ← ИЗМЕНЕНО
    price = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    target_id = Column(BigInteger, ForeignKey('users.tg_id'))  # ← ИЗМЕНЕНО
    author_id = Column(BigInteger, ForeignKey('users.tg_id'))  # ← ИЗМЕНЕНО
    text = Column(Text)
    rating = Column(Integer)
    date = Column(DateTime, default=datetime.utcnow)

class Achievement(Base):
    __tablename__ = 'achievements'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    icon = Column(String)
    min_deals = Column(Integer)
    description = Column(String)

class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True)
    reporter_id = Column(BigInteger, ForeignKey('users.tg_id'))  # ← ИЗМЕНЕНО
    reported_id = Column(BigInteger, ForeignKey('users.tg_id'))  # ← ИЗМЕНЕНО
    reason = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")

class Favorite(Base):
    __tablename__ = 'favorites'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.tg_id'))  # ← ИЗМЕНЕНО
    lot_id = Column(Integer, ForeignKey('lots.id'))
    date = Column(DateTime, default=datetime.utcnow)

class BlackList(Base):
    __tablename__ = 'blacklist'
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey('users.tg_id'))  # ← ИЗМЕНЕНО
    blocked_user_id = Column(BigInteger, ForeignKey('users.tg_id'))  # ← ИЗМЕНЕНО
    reason = Column(Text, nullable=True)
    date = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

def init_achievements():
    session = SessionLocal()
    if session.query(Achievement).count() == 0:
        achievements = [
            Achievement(name="Новичок", icon="🟢", min_deals=0, description="Первые шаги в мире аукционов"),
            Achievement(name="Торговец", icon="🔵", min_deals=10, description="10 успешных сделок"),
            Achievement(name="Опытный", icon="🟣", min_deals=25, description="25 сделок за плечами"),
            Achievement(name="Барон", icon="🟡", min_deals=50, description="50 сделок — ты уже профи!"),
            Achievement(name="Легенда", icon="🔴", min_deals=100, description="100 сделок! Ты легенда TSUM!"),
            Achievement(name="Магнат", icon="💎", min_deals=200, description="Невероятно! 200 сделок!"),
            Achievement(name="Топ-игрок", icon="🏅", min_deals=500, description="Топ-игрок аукциона!"),
            Achievement(name="Абсолют", icon="👑", min_deals=1000, description="Ты абсолютный чемпион!")
        ]
        session.add_all(achievements)
        session.commit()
    session.close()

init_achievements()
