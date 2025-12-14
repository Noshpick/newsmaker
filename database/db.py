from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from config.settings import DATABASE_URL
from database.models import Base, Article, Post, UserSettings

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ База данных инициализирована")


def get_db() -> Session:
    db = SessionLocal()
    try:
        return db
    finally:
        pass

def create_article(db: Session, url: str, user_id: int, title: str = None,
                   content: str = None, summary: str = None, sentiment: str = None):
    article = Article(
        url=url,
        user_id=user_id,
        title=title,
        content=content,
        summary=summary,
        sentiment=sentiment
    )
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def get_article_by_url(db: Session, url: str):
    return db.query(Article).filter(Article.url == url).first()


def create_post(db: Session, article_id: int, platform: str, content: str,
                hashtags: str = None, scheduled_time=None):
    post = Post(
        article_id=article_id,
        platform=platform,
        content=content,
        hashtags=hashtags,
        scheduled_time=scheduled_time
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def get_posts_by_article(db: Session, article_id: int):
    return db.query(Post).filter(Post.article_id == article_id).all()


def get_user_settings(db: Session, user_id: int):
    return db.query(UserSettings).filter(UserSettings.user_id == user_id).first()


def update_user_settings(db: Session, user_id: int, **kwargs):
    settings = get_user_settings(db, user_id)
    if not settings:
        settings = UserSettings(user_id=user_id)
        db.add(settings)

    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)

    db.commit()
    db.refresh(settings)
    return settings


def get_scheduled_posts(db: Session):
    from database.models import PostStatus
    return db.query(Post).filter(
        Post.status == PostStatus.SCHEDULED,
        Post.scheduled_time.isnot(None)
    ).all()