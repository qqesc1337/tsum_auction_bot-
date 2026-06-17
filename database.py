from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import DATABASE_URL
import os

# Если на Railway — используем PostgreSQL, иначе SQLite
if "postgres" in DATABASE_URL:
    # PostgreSQL (Railway)
    engine = create_engine(DATABASE_URL)
else:
    # SQLite (локально)
    engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ... ВСЕ ТВОИ МОДЕЛИ (User, Lot, Transaction, Review, Achievement, Report, Favorite, BlackList) ...

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
