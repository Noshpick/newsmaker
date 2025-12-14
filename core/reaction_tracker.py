import aiohttp
from datetime import datetime
from typing import Dict, List
import os


class ReactionTracker:

    def __init__(self):
        self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.vk_access_token = os.getenv('VK_ACCESS_TOKEN')

    async def get_telegram_post_stats(self, channel_id: str, message_id: int) -> dict:
        try:
            url = f"https://api.telegram.org/bot{self.telegram_bot_token}/getUpdates"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'success': True,
                            'platform': 'telegram',
                            'views': 'N/A',
                            'shares': 'N/A',
                            'comments': 'N/A',
                            'note': 'Telegram Bot API has limited analytics access'
                        }
                    else:
                        return {'success': False, 'error': f'API error: {response.status}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    async def get_vk_post_stats(self, group_id: str, post_id: int) -> dict:
        try:
            url = 'https://api.vk.com/method/wall.getById'
            params = {
                'access_token': self.vk_access_token,
                'v': '5.131',
                'posts': f'-{group_id}_{post_id}'
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        if 'response' in result and result['response']:
                            post = result['response'][0]
                            likes = post.get('likes', {}).get('count', 0)
                            reposts = post.get('reposts', {}).get('count', 0)
                            comments = post.get('comments', {}).get('count', 0)
                            views = post.get('views', {}).get('count', 0)

                            return {
                                'success': True,
                                'platform': 'vk',
                                'likes': likes,
                                'reposts': reposts,
                                'comments': comments,
                                'views': views,
                                'engagement_rate': self._calculate_engagement(likes, reposts, comments, views)
                            }
                        else:
                            return {'success': False, 'error': 'Post not found'}
                    else:
                        return {'success': False, 'error': f'VK API error: {response.status}'}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _calculate_engagement(self, likes: int, reposts: int, comments: int, views: int) -> float:
        if views == 0:
            return 0.0
        total_interactions = likes + reposts + comments
        return round((total_interactions / views) * 100, 2)

    async def analyze_post_performance(self, post_stats: dict) -> dict:
        if not post_stats.get('success'):
            return {'error': 'Invalid stats data'}

        engagement = post_stats.get('engagement_rate', 0)
        views = post_stats.get('views', 0)

        performance = 'low'
        if engagement > 5:
            performance = 'excellent'
        elif engagement > 3:
            performance = 'good'
        elif engagement > 1:
            performance = 'average'

        return {
            'performance': performance,
            'engagement_rate': engagement,
            'views': views,
            'recommendations': self._get_recommendations(performance, post_stats),
            'analysis_time': datetime.utcnow().isoformat()
        }

    def _get_recommendations(self, performance: str, stats: dict) -> List[str]:
        recommendations = []

        if performance == 'low':
            recommendations.append('Попробуйте изменить время публикации')
            recommendations.append('Добавьте более привлекательные изображения')
            recommendations.append('Используйте более релевантные хештеги')

        if stats.get('comments', 0) < stats.get('likes', 0) * 0.1:
            recommendations.append('Задавайте вопросы в конце поста для стимулирования комментариев')

        if stats.get('reposts', 0) < stats.get('likes', 0) * 0.05:
            recommendations.append('Создавайте контент, которым хочется делиться')
            recommendations.append('Добавьте призыв к действию')

        if not recommendations:
            recommendations.append('Отличная работа! Продолжайте в том же духе')

        return recommendations

    async def get_all_posts_analytics(self, posts_info: List[dict]) -> dict:
        analytics = {
            'total_posts': len(posts_info),
            'total_views': 0,
            'total_likes': 0,
            'total_reposts': 0,
            'total_comments': 0,
            'average_engagement': 0,
            'best_performing_post': None,
            'platform_breakdown': {}
        }

        stats_list = []
        for post_info in posts_info:
            platform = post_info['platform']
            if platform == 'vk':
                stats = await self.get_vk_post_stats(post_info['group_id'], post_info['post_id'])
            elif platform == 'telegram':
                stats = await self.get_telegram_post_stats(post_info['channel_id'], post_info['message_id'])
            else:
                continue

            if stats.get('success'):
                stats_list.append(stats)
                analytics['total_views'] += stats.get('views', 0)
                analytics['total_likes'] += stats.get('likes', 0)
                analytics['total_reposts'] += stats.get('reposts', 0)
                analytics['total_comments'] += stats.get('comments', 0)

                if platform not in analytics['platform_breakdown']:
                    analytics['platform_breakdown'][platform] = {
                        'posts': 0,
                        'total_engagement': 0
                    }
                analytics['platform_breakdown'][platform]['posts'] += 1
                analytics['platform_breakdown'][platform]['total_engagement'] += stats.get('engagement_rate', 0)

        if stats_list:
            analytics['average_engagement'] = round(
                sum(s.get('engagement_rate', 0) for s in stats_list) / len(stats_list), 2
            )
            analytics['best_performing_post'] = max(
                stats_list, key=lambda x: x.get('engagement_rate', 0)
            )

        return analytics
