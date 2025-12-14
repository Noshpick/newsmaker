from config.settings import AI_PROVIDER, AI_API_KEY, AI_MODEL
import json
import aiohttp


class UniversalAIAnalyzer:

    def __init__(self):
        self.provider = AI_PROVIDER.lower()
        self.api_key = AI_API_KEY
        self.model = AI_MODEL

        if self.provider == 'claude':
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
        elif self.provider == 'gemini':
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai.GenerativeModel(self.model)
        elif self.provider == 'groq':
            from groq import Groq
            self.client = Groq(api_key=self.api_key)
        elif self.provider == 'ollama':
            self.base_url = "http://localhost:11434"

    async def _call_claude(self, prompt: str, max_tokens: int = 1000) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    async def _call_gemini(self, prompt: str) -> str:
        response = self.client.generate_content(prompt)
        return response.text

    async def _call_groq(self, prompt: str, max_tokens: int = 1000) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content

    async def _call_ollama(self, prompt: str) -> str:
        # Вызов Ollama (локально)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
            ) as response:
                result = await response.json()
                return result['response']

    async def generate(self, prompt: str, max_tokens: int = 1000) -> str:
        try:
            if self.provider == 'claude':
                return await self._call_claude(prompt, max_tokens)
            elif self.provider == 'gemini':
                return await self._call_gemini(prompt)
            elif self.provider == 'groq':
                return await self._call_groq(prompt, max_tokens)
            elif self.provider == 'ollama':
                return await self._call_ollama(prompt)
            else:
                raise ValueError(f"Неизвестный провайдер: {self.provider}")
        except Exception as e:
            raise Exception(f"Ошибка AI провайдера {self.provider}: {str(e)}")

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

ВАЖНО: Отвечай ТОЛЬКО JSON, без дополнительного текста, без markdown."""

        try:
            result_text = await self.generate(prompt, max_tokens=1000)

            result_text = result_text.strip()
            if result_text.startswith('```'):
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1])
            if result_text.startswith('json'):
                result_text = result_text[4:].strip()

            result = json.loads(result_text)
            return result

        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга JSON: {e}")
            print(f"Получен текст: {result_text[:200]}")
            return {
                'summary': 'Не удалось проанализировать статью',
                'sentiment': 'neutral',
                'key_points': [],
                'relevance_score': 5,
                'main_theme': 'общее'
            }
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
        from config.settings import PLATFORMS

        print(f"🔍 DEBUG: Генерация постов для платформ: {platforms}")

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

        json_example = {}
        for platform in platforms:
            json_example[platform] = {
                "content": "текст поста",
                "hashtags": "#хештег1 #хештег2"
            }
        json_example_str = json.dumps(json_example, ensure_ascii=False, indent=2)

        prompt = f"""{brand_context}
Исходная статья:
Заголовок: {article_data.get('title')}
Краткое содержание: {article_data.get('summary')}
Ключевые моменты: {', '.join(article_data.get('key_points', []))}

Тональность: {sentiment_context.get(article_data.get('sentiment', 'neutral'))}

Создай посты ТОЛЬКО для следующих платформ: {', '.join(platforms)}
Требования для каждой платформы:
{chr(10).join(platform_requirements)}

Верни результат в JSON формате (ТОЛЬКО для платформ: {', '.join(platforms)}):
{json_example_str}

Требования:
- Создай посты ТОЛЬКО для платформ: {', '.join(platforms)}
- Каждый пост должен быть УНИКАЛЬНЫМ
- Telegram и VK: более живые, с эмодзи
- LinkedIn и пресс-релиз: деловой стиль
- Twitter: максимально кратко
- Добавь релевантные хештеги (3-5 штук)

ВАЖНО: Отвечай ТОЛЬКО JSON для платформ {', '.join(platforms)}, без markdown, без лишних платформ."""

        try:
            result_text = await self.generate(prompt, max_tokens=2000)

            result_text = result_text.strip()
            if result_text.startswith('```'):
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1])
            if result_text.startswith('json'):
                result_text = result_text[4:].strip()

            print(f"🔍 DEBUG: Получен ответ AI:\n{result_text[:500]}")

            posts = json.loads(result_text)

            print(f"🔍 DEBUG: Распарсенные платформы: {list(posts.keys())}")

            filtered_posts = {k: v for k, v in posts.items() if k in platforms}

            print(f"🔍 DEBUG: После фильтрации: {list(filtered_posts.keys())}")

            for platform in platforms:
                if platform not in filtered_posts:
                    print(f"⚠️ WARNING: Платформа {platform} не найдена в ответе AI, добавляю заглушку")
                    filtered_posts[platform] = {
                        'content': f"{article_data.get('title')}\n\n{article_data.get('summary')}",
                        'hashtags': '#новости'
                    }

            return filtered_posts

        except Exception as e:
            print(f"❌ Ошибка генерации постов: {e}")
            print(f"Ответ AI: {result_text if 'result_text' in locals() else 'N/A'}")
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
    "vk": {{"time_slot": "сегодня 15:00", "priority": 2, "reason": "почему"}}
}}

ВАЖНО: Отвечай ТОЛЬКО JSON, без markdown."""

        try:
            result_text = await self.generate(prompt, max_tokens=1000)

            result_text = result_text.strip()
            if result_text.startswith('```'):
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1])
            if result_text.startswith('json'):
                result_text = result_text[4:].strip()

            schedule = json.loads(result_text)
            return schedule

        except Exception as e:
            print(f"Ошибка планирования: {e}")
            return {platform: {"time_slot": "сегодня 14:00", "priority": i + 1}
                    for i, platform in enumerate(posts.keys())}

AIAnalyzer = UniversalAIAnalyzer