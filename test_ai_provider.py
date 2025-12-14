import asyncio
import sys
from config.settings import AI_PROVIDER, AI_API_KEY, AI_MODEL

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")


async def test_provider():
    
    print("\n" + "="*60)
    print("🧪 ТЕСТ AI ПРОВАЙДЕРА")
    print("="*60 + "\n")
    
    print_info(f"Провайдер: {AI_PROVIDER}")
    print_info(f"Модель: {AI_MODEL}")
    print_info(f"API ключ: {AI_API_KEY[:20]}..." if AI_API_KEY else "Не указан")
    print()
    
    try:
        from core.universal_ai_analyzer import UniversalAIAnalyzer
        print_success("Модуль UniversalAIAnalyzer загружен")
    except Exception as e:
        print_error(f"Ошибка загрузки модуля: {e}")
        return
    
    try:
        analyzer = UniversalAIAnalyzer()
        print_success(f"AI Analyzer инициализирован для {AI_PROVIDER}")
    except Exception as e:
        print_error(f"Ошибка инициализации: {e}")
        print_warning("Возможные причины:")
        print("  - Неправильный API ключ")
        print("  - Не установлена библиотека провайдера")
        print(f"  - Для {AI_PROVIDER} выполни: pip install {get_package_name(AI_PROVIDER)}")
        return
    
    print()
    print_info("Отправляю тестовый запрос...")
    print()
    
    test_prompt = """Ответь одним предложением: что такое искусственный интеллект?"""
    
    try:
        response = await analyzer.generate(test_prompt, max_tokens=100)
        
        print_success("Получен ответ от AI!")
        print()
        print("📝 Ответ AI:")
        print("-" * 60)
        print(response)
        print("-" * 60)
        print()
        
        print_info("Тестирую анализ статьи...")
        print()
        
        test_article = {
            'title': 'Компания X увеличила прибыль на 50%',
            'content': 'Компания X объявила о рекордных финансовых результатах. Прибыль выросла на 50% по сравнению с прошлым годом.'
        }
        
        analysis = await analyzer.analyze_article(
            title=test_article['title'],
            content=test_article['content']
        )
        
        print_success("Анализ выполнен!")
        print()
        print("📊 Результат анализа:")
        print("-" * 60)
        print(f"Суть: {analysis.get('summary', 'N/A')}")
        print(f"Тональность: {analysis.get('sentiment', 'N/A')}")
        print(f"Ключевые моменты: {', '.join(analysis.get('key_points', []))}")
        print(f"Релевантность: {analysis.get('relevance_score', 'N/A')}/10")
        print("-" * 60)
        print()
        
        print_success("ВСЕ ТЕСТЫ ПРОЙДЕНЫ! 🎉")
        print()
        print_info("Провайдер работает корректно и готов к использованию!")
        print()
        
    except Exception as e:
        print_error(f"Ошибка при выполнении запроса: {e}")
        print()
        print_warning("Возможные причины:")
        
        if AI_PROVIDER == 'gemini':
            print("  - Проверь API ключ на https://makersuite.google.com/app/apikey")
            print("  - Убедись что API key активен")
        elif AI_PROVIDER == 'groq':
            print("  - Проверь API ключ на https://console.groq.com/")
            print("  - Проверь лимиты (30 req/min)")
        elif AI_PROVIDER == 'ollama':
            print("  - Убедись что Ollama запущен: ollama serve")
            print("  - Проверь что модель скачана: ollama list")
            print("  - Скачай модель: ollama pull llama3.1")
        elif AI_PROVIDER == 'claude':
            print("  - Проверь API ключ на https://console.anthropic.com/")
            print("  - Проверь баланс аккаунта")
        
        print()
        return


def get_package_name(provider):
    packages = {
        'gemini': 'google-generativeai',
        'groq': 'groq',
        'claude': 'anthropic',
        'ollama': 'не требуется (работает локально)'
    }
    return packages.get(provider, 'unknown')


def main():
    
    if not AI_PROVIDER:
        print_error("AI_PROVIDER не указан в .env файле!")
        print_info("Добавь в .env: AI_PROVIDER=gemini")
        sys.exit(1)
    
    if AI_PROVIDER != 'ollama' and not AI_API_KEY:
        print_error("AI_API_KEY не указан в .env файле!")
        print_info(f"Получи ключ и добавь в .env: AI_API_KEY=твой_ключ")
        sys.exit(1)
    
    asyncio.run(test_provider())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nТест прерван пользователем")
    except Exception as e:
        print_error(f"Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()