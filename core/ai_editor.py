from core.universal_ai_analyzer import UniversalAIAnalyzer


class AIEditor:

    def __init__(self):
        self.analyzer = UniversalAIAnalyzer()

    async def edit_post(self, original_post: str, user_request: str, platform: str = None) -> dict:

        platform_info = ""
        if platform:
            from config.settings import PLATFORMS
            info = PLATFORMS.get(platform, {})
            platform_info = f"\nПлатформа: {info.get('name', platform)}"
            platform_info += f"\nМаксимум символов: {info.get('max_length', 1000)}"
            if info.get('emoji'):
                platform_info += "\nМожно использовать эмодзи"
            if info.get('formal'):
                platform_info += "\nФормальный стиль"

        prompt = f"""Ты - редактор контента. У тебя есть пост и запрос на редактирование.
{platform_info}

ИСХОДНЫЙ ПОСТ:
{original_post}

ЗАПРОС ПОЛЬЗОВАТЕЛЯ:
{user_request}

Отредактируй пост согласно запросу пользователя. Верни результат в JSON:
{{
    "edited_post": "отредактированный текст поста",
    "changes": "краткое описание что изменил (1-2 предложения)"
}}

Правила:
- Сохрани основную суть и ключевые факты
- Следуй запросу пользователя точно
- Если просят "короче" - убери детали, но сохрани главное
- Если просят "добавить эмодзи" - добавь уместные эмодзи
- Если просят изменить тон - измени стиль, но сохрани факты

Отвечай ТОЛЬКО JSON, без markdown."""

        try:
            result_text = await self.analyzer.generate(prompt, max_tokens=1000)

            result_text = result_text.strip()
            if result_text.startswith('```'):
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1])
            if result_text.startswith('json'):
                result_text = result_text[4:].strip()

            import json
            result = json.loads(result_text)

            return {
                'edited_post': result.get('edited_post', original_post),
                'changes': result.get('changes', 'Изменения применены'),
                'success': True
            }

        except Exception as e:
            print(f"Ошибка редактирования: {e}")
            return {
                'edited_post': original_post,
                'changes': f'Ошибка: {str(e)}',
                'success': False
            }

    async def suggest_improvements(self, post: str, platform: str = None) -> list:

        platform_info = ""
        if platform:
            from config.settings import PLATFORMS
            info = PLATFORMS.get(platform, {})
            platform_info = f"Платформа: {info.get('name', platform)}"

        prompt = f"""Проанализируй этот пост и предложи 3-5 конкретных улучшений.
{platform_info}

ПОСТ:
{post}

Верни JSON массив с предложениями:
[
    "Добавить больше эмодзи для визуальной привлекательности",
    "Сократить до 150 символов",
    "Изменить тон на более неформальный"
]

Предложения должны быть:
- Конкретными и выполнимыми
- Короткими (до 10 слов)
- Разнообразными (стиль, длина, оформление)

Отвечай ТОЛЬКО JSON массивом."""

        try:
            result_text = await self.analyzer.generate(prompt, max_tokens=500)

            result_text = result_text.strip()
            if result_text.startswith('```'):
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1])
            if result_text.startswith('json'):
                result_text = result_text[4:].strip()

            import json
            suggestions = json.loads(result_text)

            return suggestions if isinstance(suggestions, list) else []

        except Exception as e:
            print(f"Ошибка предложений: {e}")
            return [
                "Добавить больше эмодзи",
                "Сделать текст короче",
                "Изменить тон общения"
            ]

    async def create_variations(self, post: str, count: int = 3, platform: str = None) -> list:

        platform_info = ""
        if platform:
            from config.settings import PLATFORMS
            info = PLATFORMS.get(platform, {})
            platform_info = f"Платформа: {info.get('name', platform)}, макс. {info.get('max_length')} символов"

        prompt = f"""Создай {count} разных варианта этого поста.
{platform_info}

ИСХОДНЫЙ ПОСТ:
{post}

Создай {count} варианта с разными стилями:
1. Краткий и емкий
2. Развернутый с деталями
3. С юмором и эмодзи

Верни JSON:
[
    {{"text": "текст варианта 1", "style": "краткий стиль"}},
    {{"text": "текст варианта 2", "style": "подробный стиль"}}
]

Сохрани основную информацию во всех вариантах!

Отвечай ТОЛЬКО JSON массивом."""

        try:
            result_text = await self.analyzer.generate(prompt, max_tokens=1500)

            result_text = result_text.strip()
            if result_text.startswith('```'):
                lines = result_text.split('\n')
                result_text = '\n'.join(lines[1:-1])
            if result_text.startswith('json'):
                result_text = result_text[4:].strip()

            import json
            variations = json.loads(result_text)

            return variations if isinstance(variations, list) else []

        except Exception as e:
            print(f"Ошибка создания вариантов: {e}")
            return []