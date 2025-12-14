from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

class SentimentType(enum.Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class PostStatus(enum.Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"

class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True, nullable=False)
    title = Column(String(500))
    content = Column(Text)
    summary = Column(Text)
    sentiment = Column(Enum(SentimentType))
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer)

    posts = relationship("Post", back_populates="article", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title[:50]}...')>"

class Post(Base):
    __tablename__ = 'posts'

    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    platform = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    hashtags = Column(String(500))

    status = Column(Enum(PostStatus), default=PostStatus.DRAFT)
    scheduled_time = Column(DateTime)
    published_time = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)

    article = relationship("Article", back_populates="posts")

    def __repr__(self):
        return f"<Post(id={self.id}, platform='{self.platform}', status='{self.status.value}')>"

class UserSettings(Base):
    __tablename__ = 'user_settings'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    brand_name = Column(String(200))
    brand_tone = Column(String(200))
    preferred_platforms = Column(String(500))
    auto_schedule = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserSettings(user_id={self.user_id}, brand='{self.brand_name}')>"