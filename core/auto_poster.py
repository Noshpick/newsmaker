import aiohttp
import asyncio
from datetime import datetime
from database.db import get_db
from database.models import Post, PostStatus
import os


class AutoPoster:

    def __init__(self):
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.vk_access_token = os.getenv('VK_ACCESS_TOKEN')
        self.twitter_tokens = {
            'api_key': os.getenv('TWITTER_API_KEY'),
            'api_secret': os.getenv('TWITTER_API_SECRET'),
            'access_token': os.getenv('TWITTER_ACCESS_TOKEN'),
            'access_secret': os.getenv('TWITTER_ACCESS_SECRET')
        }

    async def post_to_telegram(self, channel_id: str, content: str, image_url: str = None) -> dict:
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"

            if image_url:
                url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendPhoto"
                data = {
                    'chat_id': channel_id,
                    'photo': image_url,
                    'caption': content,
                    'parse_mode': 'HTML'
                }
            else:
                data = {
                    'chat_id': channel_id,
                    'text': content,
                    'parse_mode': 'HTML'
                }

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'success': True,
                            'message_id': result['result']['message_id'],
                            'platform': 'telegram'
                        }
                    else:
                        return {
                            'success': False,
                            'error': f'Telegram API error: {response.status}'
                        }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def post_to_vk(self, group_id: str, content: str, image_url: str = None) -> dict:
        try:
            url = 'https://api.vk.com/method/wall.post'
            params = {
                'access_token': self.vk_access_token,
                'v': '5.131',
                'owner_id': f'-{group_id}',
                'message': content,
                'from_group': 1
            }

            if image_url:
                params['attachments'] = image_url

            async with aiohttp.ClientSession() as session:
                async with session.post(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        if 'response' in result:
                            return {
                                'success': True,
                                'post_id': result['response']['post_id'],
                                'platform': 'vk'
                            }
                        else:
                            return {
                                'success': False,
                                'error': result.get('error', {}).get('error_msg', 'Unknown error')
                            }
                    else:
                        return {
                            'success': False,
                            'error': f'VK API error: {response.status}'
                        }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def publish_post(self, post_id: int, channel_config: dict) -> dict:
        db = get_db()
        try:
            post = db.query(Post).filter(Post.id == post_id).first()
            if not post:
                return {'success': False, 'error': 'Post not found'}

            platform = post.platform
            content = post.content

            if post.hashtags:
                content += f"\n\n{post.hashtags}"

            result = None
            if platform == 'telegram':
                channel_id = channel_config.get('telegram_channel_id')
                if channel_id:
                    result = await self.post_to_telegram(channel_id, content)
            elif platform == 'vk':
                group_id = channel_config.get('vk_group_id')
                if group_id:
                    result = await self.post_to_vk(group_id, content)

            if result and result.get('success'):
                post.status = PostStatus.PUBLISHED
                post.published_time = datetime.utcnow()
                db.commit()
                return {
                    'success': True,
                    'post_id': post_id,
                    'platform': platform,
                    'result': result
                }
            else:
                post.status = PostStatus.FAILED
                db.commit()
                return {
                    'success': False,
                    'error': result.get('error') if result else 'No result'
                }

        except Exception as e:
            post.status = PostStatus.FAILED
            db.commit()
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            db.close()

    async def check_scheduled_posts(self, channel_config: dict):
        db = get_db()
        try:
            now = datetime.utcnow()
            scheduled_posts = db.query(Post).filter(
                Post.status == PostStatus.SCHEDULED,
                Post.scheduled_time <= now
            ).all()

            results = []
            for post in scheduled_posts:
                result = await self.publish_post(post.id, channel_config)
                results.append(result)
                await asyncio.sleep(2)

            return results
        finally:
            db.close()
