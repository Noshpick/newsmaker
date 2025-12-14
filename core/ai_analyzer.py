import json
import os
from typing import Dict, List, Optional
from config.settings import AI_PROVIDER, AI_API_KEY, PLATFORMS


class AIAnalyzer:

    def __init__(self, provider: str = None, api_key: str = None):
        self.provider = provider or AI_PROVIDER
        self.api_key = api_key or AI_API_KEY

        if self.provider == "groq":
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
            self.model = "llama-3.3-70b-versatile"

        elif self.provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel('gemini-1.5-flash')
            self.model = "gemini-1.5-flash"

        elif self.provider == "openai":
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
            self.model = "gpt-4o-mini"

        elif self.provider == "anthropic":
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            self.model = "claude-sonnet-4-20250514"

        else:
            raise ValueError(f"Неподдерживаемый провайдер: {self.provider}")

    async def _call_ai(self, prompt: str, max_tokens: int = 1000) -> str:

        try:
            if self.provider == "groq":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content

            elif self.provider == "gemini":
                response = self.client.generate_content(prompt)
                return response.text

            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                return response.choices[0].message.content

            elif self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text

        except Exception as e:
            print(f"Ошибка вызова {self.provider} API: {e}")
            raise

    async def analyze_article(self, title: str, content: str, brand_info: dict = None) -> dict:

        brand_context = ""
        if brand_info and brand_info.get('brand_name'):
            brand_context = f"\n\nКонтекст бренда: {brand_info.get('brand_name')}"
            if brand_info.get('brand_tone'):
                brand_context += f"\nТон бренда: {brand_info.get('brand_tone')}"

        prompt = f"""Проанализируй эту статью/новость и верни результат СТРОГО в JSON формате.
{brand_context}

Заголовок: {title}

Содержание:
{content[:3000]}

Верни JSON со следующими полями:
{{
    "summary": "краткое содержание статьи в 2-3 предложениях",
    "sentiment": "positive/negative/neutral - отношение к упоминаемому бренду/компании",
    "key_points": ["ключевой момент 1", "ключевой момент 2", "ключевой момент 3"],
    "relevance_score": число от 1 до 10 (насколько статья важна для бренда),
    "main_theme": "основная тема статьи одним словом"
}}

Отвечай ТОЛЬКО JSON, без дополнительного текста."""

        try:
            result_text = await self._call_ai(prompt, max_tokens=1000)

            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip('`').strip()

            result = json.loads(result_text)
            return result

        except Exception as e:
            print(f"Ошибка анализа: {e}")
            return {
                'summary': 'Не удалось проанализировать статью',
                'sentiment': 'neutral',
                'key_points': [],
                'relevance_score': 5,
                'main_theme': 'общее'
            }

    async def generate_posts(self, article_data: dict, platforms: list, brand_info: dict = None) -> dict:

        brand_context = ""
        if brand_info and brand_info.get('brand_name'):
            brand_context = f"Бренд: {brand_info.get('brand_name')}\n"
            if brand_info.get('brand_tone'):
                brand_context += f"Тон коммуникации: {brand_info.get('brand_tone')}\n"

        platform_requirements = []
        for platform in platforms:
            platform_info = PLATFORMS.get(platform, {})
            req = f"- {platform_info.get('name', platform)}: "
            req += f"макс. {platform_info.get('max_length')} символов"
            if platform_info.get('formal'):
                req += ", формальный стиль"
            if platform_info.get('emoji'):
                req += ", можно эмодзи"
            platform_requirements.append(req)

        sentiment_context = {
            'positive': 'Это ПОЗИТИВНАЯ новость - подчеркни достижения и успехи',
            'negative': 'Это НЕГАТИВНАЯ новость - будь осторожен, предложи как компания работает над проблемой',
            'neutral': 'Это НЕЙТРАЛЬНАЯ новость - будь объективным'
        }

        prompt = f"""{brand_context}
Исходная статья:
Заголовок: {article_data.get('title')}
Краткое содержание: {article_data.get('summary')}
Ключевые моменты: {', '.join(article_data.get('key_points', []))}

Тональность: {sentiment_context.get(article_data.get('sentiment', 'neutral'))}

Создай посты для следующих платформ:
{chr(10).join(platform_requirements)}

Верни результат в JSON формате:
{{
    "telegram": {{
        "content": "текст поста",
        "hashtags": "#хештег1 #хештег2"
    }},
    "vk": {{ ... }},
    ...
}}

Требования:
- Каждый пост должен быть УНИКАЛЬНЫМ и адаптированным под платформу
- Сохрани суть новости, но адаптируй стиль
- Telegram и VK: более живые, с эмодзи
- LinkedIn и пресс-релиз: деловой формальный стиль
- Twitter: максимально кратко, цепляюще
- Добавь релевантные хештеги (3-5 штук)

Отвечай ТОЛЬКО JSON."""

        try:
            result_text = await self._call_ai(prompt, max_tokens=2000)

            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip('`').strip()

            posts = json.loads(result_text)
            return posts

        except Exception as e:
            print(f"Ошибка генерации постов: {e}")
            simple_post = {
                'content': f"{article_data.get('title')}\n\n{article_data.get('summary')}",
                'hashtags': '#новости'
            }
            return {platform: simple_post for platform in platforms}

    async def suggest_posting_schedule(self, posts: dict, sentiment: str) -> dict:

        prompt = f"""У нас есть посты для публикации на платформах: {', '.join(posts.keys())}
Тональность новости: {sentiment}

Предложи оптимальное расписание публикации. Учти:
- Позитивные новости лучше публиковать утром/днём
- Негативные - вечером, когда меньше охват
- Telegram и VK - можно сразу
- LinkedIn - лучше в рабочие часы (10-16)
- Пресс-релизы - утро рабочего дня

Верни JSON:
{{
    "telegram": {{"time_slot": "сегодня 14:00", "priority": 1, "reason": "почему"}},
    "vk": {{"time_slot": "сегодня 15:00", "priority": 2, "reason": "почему"}},
    ...
}}

Отвечай ТОЛЬКО JSON."""

        try:
            result_text = await self._call_ai(prompt, max_tokens=1000)

            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip('`').strip()

            schedule = json.loads(result_text)
            return schedule

        except Exception as e:
            print(f"Ошибка планирования: {e}")
            return {platform: {"time_slot": "сегодня 14:00", "priority": i + 1}
                    for i, platform in enumerate(posts.keys())}

async def test_provider(provider: str, api_key: str):
    print(f"\n🧪 Тестирую провайдер: {provider}")

    try:
        analyzer = AIAnalyzer(provider=provider, api_key=api_key)

        result = await analyzer.analyze_article(
            title="Тестовая статья",
            content="Это тестовое содержание статьи для проверки работы API."
        )

        print(f"✅ {provider} работает!")
        print(f"Результат: {result}")
        return True

    except Exception as e:
        print(f"❌ {provider} ошибка: {e}")
        return False


if __name__ == "__main__":
    import asyncio

    asyncio.run(test_provider("groq", "your_groq_api_key"))