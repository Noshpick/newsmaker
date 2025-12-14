from core.content_fetcher import ContentFetcher
from core.universal_ai_analyzer import UniversalAIAnalyzer
from database.db import (create_article, create_post, get_article_by_url,
                         get_user_settings, get_db)
from database.models import SentimentType
from datetime import datetime, timedelta
import json


class ContentGenerator:

    def __init__(self):
        self.fetcher = ContentFetcher()
        self.analyzer = UniversalAIAnalyzer()

    async def process_article_url(self, url: str, user_id: int, platforms: list = None) -> dict:

        db = get_db()

        try:
            existing = get_article_by_url(db, url)
            if existing:
                return {
                    'error': True,
                    'message': 'Эта статья уже была обработана ранее'
                }

            user_settings = get_user_settings(db, user_id)
            brand_info = {}
            if user_settings:
                brand_info = {
                    'brand_name': user_settings.brand_name,
                    'brand_tone': user_settings.brand_tone
                }

                if not platforms and user_settings.preferred_platforms:
                    platforms = json.loads(user_settings.preferred_platforms)

            if not platforms:
                platforms = ['telegram', 'vk', 'linkedin']

            print(f"📥 Загружаю статью: {url}")
            article_data = await self.fetcher.fetch_article(url)

            print(f"🤖 Анализирую контент...")
            analysis = await self.analyzer.analyze_article(
                title=article_data['title'],
                content=article_data['content'],
                brand_info=brand_info
            )

            sentiment_map = {
                'positive': SentimentType.POSITIVE,
                'negative': SentimentType.NEGATIVE,
                'neutral': SentimentType.NEUTRAL
            }

            article = create_article(
                db=db,
                url=url,
                user_id=user_id,
                title=article_data['title'],
                content=article_data['content'],
                summary=analysis['summary'],
                sentiment=sentiment_map.get(analysis['sentiment'], SentimentType.NEUTRAL)
            )

            print(f"✍️ Генерирую посты для платформ: {', '.join(platforms)}")
            post_data = {
                'title': article_data['title'],
                'summary': analysis['summary'],
                'sentiment': analysis['sentiment'],
                'key_points': analysis['key_points']
            }

            posts = await self.analyzer.generate_posts(
                article_data=post_data,
                platforms=platforms,
                brand_info=brand_info
            )

            auto_schedule_enabled = user_settings.auto_schedule if user_settings else True

            saved_posts = {}
            for platform, post_content in posts.items():
                scheduled_time = None
                schedule_info = {}

                if auto_schedule_enabled:
                    print(f"📅 Автоматически планирую расписание для {platform}...")
                    schedule = await self.analyzer.suggest_posting_schedule(
                        posts={platform: post_content},
                        sentiment=analysis['sentiment']
                    )
                    scheduled_time = self._parse_schedule_time(
                        schedule.get(platform, {}).get('time_slot', 'сегодня 14:00')
                    )
                    schedule_info = schedule.get(platform, {})
                else:
                    print(f"📝 Автопланирование выключено, время публикации не установлено")

                post = create_post(
                    db=db,
                    article_id=article.id,
                    platform=platform,
                    content=post_content.get('content', ''),
                    hashtags=post_content.get('hashtags', ''),
                    scheduled_time=scheduled_time
                )

                saved_posts[platform] = {
                    'post_id': post.id,
                    'content': post.content,
                    'hashtags': post.hashtags,
                    'scheduled': scheduled_time.strftime('%Y-%m-%d %H:%M') if scheduled_time else None,
                    'schedule_info': schedule_info,
                    'auto_scheduled': auto_schedule_enabled
                }

            article_id = article.id
            article_title = article.title

            db.close()

            return {
                'success': True,
                'article_id': article_id,
                'title': article_title,
                'summary': analysis['summary'],
                'sentiment': analysis['sentiment'],
                'relevance_score': analysis.get('relevance_score', 5),
                'posts': saved_posts,
                'total_posts': len(saved_posts)
            }

        except Exception as e:
            db.close()
            return {
                'error': True,
                'message': f'Ошибка обработки: {str(e)}'
            }

    def _parse_schedule_time(self, time_slot: str) -> datetime:
        now = datetime.now()

        if 'завтра' in time_slot.lower():
            base_date = now + timedelta(days=1)
        else:
            base_date = now

        import re
        time_match = re.search(r'(\d{1,2}):(\d{2})', time_slot)
        if time_match:
            hour = int(time_match.group(1))
            minute = int(time_match.group(2))
            return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

        return now + timedelta(hours=2)

    async def quick_preview(self, url: str) -> dict:
        try:
            article_data = await self.fetcher.fetch_article(url)
            return {
                'success': True,
                'title': article_data['title'],
                'content_preview': article_data['content'][:500] + '...',
                'domain': article_data['domain']
            }
        except Exception as e:
            return {
                'error': True,
                'message': str(e)
            }