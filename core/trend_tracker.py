import aiohttp
import json
from datetime import datetime, timedelta
from typing import List, Dict


class TrendTracker:

    def __init__(self):
        self.sources = {
            'google_trends': 'https://trends.google.com/trends/trendingsearches/daily/rss?geo=RU',
            'yandex_news': 'https://news.yandex.ru/index.rss',
        }

    async def get_trending_topics(self, region: str = 'RU', limit: int = 10) -> List[Dict]:
        try:
            google_trends = await self._fetch_google_trends(region, limit)
            if google_trends:
                return google_trends
            return self._get_mock_trends(limit)
        except Exception as e:
            print(f"Ошибка получения трендов: {e}")
            return self._get_mock_trends(limit)

    async def _fetch_google_trends(self, region: str, limit: int) -> List[Dict]:
        trends = []
        try:
            async with aiohttp.ClientSession() as session:
                url = f'https://trends.google.com/trends/trendingsearches/daily/rss?geo={region}'
                async with session.get(url) as response:
                    if response.status == 200:
                        from bs4 import BeautifulSoup
                        xml_data = await response.text()
                        soup = BeautifulSoup(xml_data, 'xml')

                        items = soup.find_all('item')[:limit]
                        for item in items:
                            title = item.find('title')
                            traffic = item.find('ht:approx_traffic')
                            news_items = item.find_all('ht:news_item')

                            trend = {
                                'title': title.text if title else 'Unknown',
                                'traffic': traffic.text if traffic else 'N/A',
                                'source': 'Google Trends',
                                'timestamp': datetime.utcnow().isoformat(),
                                'related_news': []
                            }

                            for news in news_items[:3]:
                                news_title = news.find('ht:news_item_title')
                                news_url = news.find('ht:news_item_url')
                                if news_title and news_url:
                                    trend['related_news'].append({
                                        'title': news_title.text,
                                        'url': news_url.text
                                    })

                            trends.append(trend)
        except Exception as e:
            print(f"Google Trends error: {e}")

        return trends

    async def analyze_trend_relevance(self, trend_title: str, brand_keywords: List[str]) -> dict:
        relevance_score = 0
        matching_keywords = []

        trend_lower = trend_title.lower()
        for keyword in brand_keywords:
            if keyword.lower() in trend_lower:
                relevance_score += 1
                matching_keywords.append(keyword)

        return {
            'trend': trend_title,
            'relevant': relevance_score > 0,
            'relevance_score': relevance_score,
            'matching_keywords': matching_keywords,
            'recommendation': 'high' if relevance_score >= 2 else 'medium' if relevance_score == 1 else 'low'
        }

    async def suggest_content_from_trends(self, trends: List[Dict], brand_info: dict) -> List[Dict]:
        brand_keywords = brand_info.get('keywords', [])
        suggestions = []

        for trend in trends:
            analysis = await self.analyze_trend_relevance(trend['title'], brand_keywords)

            if analysis['relevant']:
                suggestion = {
                    'trend_title': trend['title'],
                    'traffic': trend.get('traffic', 'N/A'),
                    'relevance': analysis,
                    'content_ideas': [
                        f"Как {brand_info.get('brand_name', 'мы')} относится к {trend['title']}",
                        f"{trend['title']}: что это значит для нашей индустрии",
                        f"Экспертное мнение о {trend['title']}"
                    ],
                    'related_news': trend.get('related_news', [])
                }
                suggestions.append(suggestion)

        suggestions.sort(key=lambda x: x['relevance']['relevance_score'], reverse=True)
        return suggestions[:5]

    def _get_mock_trends(self, limit: int) -> List[Dict]:
        mock_trends = [
            {
                'title': 'Искусственный интеллект в бизнесе',
                'traffic': '100K+',
                'source': 'Локальная база',
                'timestamp': datetime.utcnow().isoformat(),
                'related_news': [
                    {'title': 'ИИ трансформирует рынок труда', 'url': '#'},
                    {'title': 'Компании внедряют AI-решения', 'url': '#'}
                ]
            },
            {
                'title': 'Новые технологии в образовании',
                'traffic': '75K+',
                'source': 'Локальная база',
                'timestamp': datetime.utcnow().isoformat(),
                'related_news': [
                    {'title': 'Цифровая трансформация школ', 'url': '#'},
                    {'title': 'Онлайн-обучение набирает популярность', 'url': '#'}
                ]
            },
            {
                'title': 'Экологические инициативы',
                'traffic': '60K+',
                'source': 'Локальная база',
                'timestamp': datetime.utcnow().isoformat(),
                'related_news': [
                    {'title': 'Компании переходят на зеленую энергию', 'url': '#'},
                    {'title': 'Новые экостандарты для бизнеса', 'url': '#'}
                ]
            },
            {
                'title': 'Развитие стартап-экосистемы',
                'traffic': '50K+',
                'source': 'Локальная база',
                'timestamp': datetime.utcnow().isoformat(),
                'related_news': [
                    {'title': 'Рост инвестиций в технологические стартапы', 'url': '#'},
                    {'title': 'Новые акселераторы для предпринимателей', 'url': '#'}
                ]
            },
            {
                'title': 'Цифровизация государственных услуг',
                'traffic': '45K+',
                'source': 'Локальная база',
                'timestamp': datetime.utcnow().isoformat(),
                'related_news': [
                    {'title': 'Госуслуги расширяют функционал', 'url': '#'},
                    {'title': 'Электронный документооборот в госсекторе', 'url': '#'}
                ]
            }
        ]
        return mock_trends[:limit]

    async def get_hashtag_trends(self, platform: str = 'twitter') -> List[str]:
        trending_hashtags = [
            '#новости',
            '#технологии',
            '#бизнес',
            '#инновации',
            '#россия'
        ]

        return trending_hashtags
