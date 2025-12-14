from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from database.db import get_db, get_scheduled_posts
from database.models import PostStatus
import logging

logger = logging.getLogger(__name__)

class PostScheduler:

    def __init__(self):
        self.scheduler = AsyncIOScheduler()

    def start(self):
        self.scheduler.add_job(
            self.check_scheduled_posts,
            'interval',
            minutes=5,
            id='check_posts'
        )

        self.scheduler.start()
        logger.info("✅ Планировщик запущен")

    async def check_scheduled_posts(self):
        db = get_db()

        try:
            posts = get_scheduled_posts(db)
            now = datetime.utcnow()

            for post in posts:
                if post.scheduled_time and post.scheduled_time <= now:
                    await self.publish_post(post)

                    post.status = PostStatus.PUBLISHED
                    post.published_time = now
                    db.commit()

                    logger.info(f"✅ Пост {post.id} опубликован на {post.platform}")

        except Exception as e:
            logger.error(f"Ошибка при проверке постов: {e}")
        finally:
            db.close()

    async def publish_post(self, post):

        logger.info(f"📤 Публикация поста на {post.platform}")
        logger.info(f"Содержание: {post.content[:100]}...")

        return True

    def stop(self):
        self.scheduler.shutdown()
        logger.info("Планировщик остановлен")


scheduler = PostScheduler()