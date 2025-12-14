"""
Тестовый скрипт для проверки работы планировщика
"""
import asyncio
from datetime import datetime, timedelta
from database.db import init_db, get_db
from database.models import Article, Post, PostStatus, SentimentType
from core.scheduler import scheduler

def create_test_posts():
    """Создает тестовые посты с разным временем публикации"""
    db = get_db()

    try:
        # Создаем тестовую статью
        article = Article(
            url="https://test.com/test-scheduler",
            title="Тест планировщика",
            content="Это тестовая статья для проверки планировщика",
            summary="Тест",
            sentiment=SentimentType.POSITIVE,
            user_id=123456
        )
        db.add(article)
        db.commit()
        db.refresh(article)

        # Создаем пост, который должен быть опубликован через 1 минуту
        now = datetime.utcnow()
        post1 = Post(
            article_id=article.id,
            platform="telegram",
            content="Тестовый пост №1 - публикуется через 1 минуту",
            hashtags="#test #scheduler",
            status=PostStatus.SCHEDULED,
            scheduled_time=now + timedelta(minutes=1)
        )

        # Создаем пост, который должен быть опубликован через 3 минуты
        post2 = Post(
            article_id=article.id,
            platform="vk",
            content="Тестовый пост №2 - публикуется через 3 минуты",
            hashtags="#test #scheduler",
            status=PostStatus.SCHEDULED,
            scheduled_time=now + timedelta(minutes=3)
        )

        # Создаем пост, который должен быть опубликован уже (прошедшее время)
        post3 = Post(
            article_id=article.id,
            platform="twitter",
            content="Тестовый пост №3 - публикуется сразу (прошедшее время)",
            hashtags="#test #scheduler",
            status=PostStatus.SCHEDULED,
            scheduled_time=now - timedelta(minutes=1)
        )

        db.add_all([post1, post2, post3])
        db.commit()

        print("✅ Созданы тестовые посты:")
        print(f"   Пост 1 (Telegram): {post1.scheduled_time}")
        print(f"   Пост 2 (VK): {post2.scheduled_time}")
        print(f"   Пост 3 (Twitter): {post3.scheduled_time} (прошедшее время)")
        print(f"\nТекущее время: {now}")
        print(f"\nПланировщик будет проверять посты каждые 5 минут")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        db.rollback()
    finally:
        db.close()

async def main():
    print("=" * 50)
    print("ТЕСТ ПЛАНИРОВЩИКА")
    print("=" * 50)

    # Инициализируем БД
    print("\n1. Инициализация базы данных...")
    init_db()

    # Создаем тестовые посты
    print("\n2. Создание тестовых постов...")
    create_test_posts()

    # Запускаем планировщик
    print("\n3. Запуск планировщика...")
    scheduler.start()
    print("✅ Планировщик запущен")

    # Ждем 10 минут, наблюдая за работой планировщика
    print("\n4. Наблюдение за работой планировщика (10 минут)...")
    print("   (Нажмите Ctrl+C для остановки)")

    try:
        await asyncio.sleep(600)  # 10 минут
    except KeyboardInterrupt:
        print("\n\n⏹ Остановка по запросу пользователя")
    finally:
        print("\n5. Остановка планировщика...")
        scheduler.stop()
        print("✅ Планировщик остановлен")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n✅ Тест завершен")
