from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base
from datetime import datetime

# 📰 NEWS TABLE
class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    summary = Column(Text)
    source_url = Column(String)

    role = Column(String)
    impact = Column(Text)
    action = Column(Text)
    risk = Column(Text)

    published_at = Column(DateTime, default=datetime.utcnow)


# 👤 USER TABLE
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    email = Column(String, unique=True, index=True)
    password = Column(String)

    # 🔥 NEW → INTENT AWARE SYSTEM
    role = Column(String)